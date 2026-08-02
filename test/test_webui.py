import json
import os
import shutil
import tempfile
import threading
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace
from datetime import datetime
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from src.webui.server import BrowserBundle, BrowserError, BrowserState, BundleStore, ResourceBrowserServer


class BrowserStateTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "images").mkdir()
        (self.root / "images" / "avatar.png").write_bytes(b"image")
        (self.root / "notes.txt").write_text("hello", encoding="utf-8")
        old_time = datetime(2024, 1, 15, 12, 0).timestamp()
        os.utime(self.root / "notes.txt", (old_time, old_time))
        (self.root / "sample.ab").write_bytes(b"not-a-real-bundle")
        self.state = BrowserState(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def test_lists_and_classifies_resources(self):
        payload = self.state.list_entries()
        self.assertEqual([item["name"] for item in payload["entries"]], ["images", "notes.txt", "sample.ab"])
        self.assertEqual(payload["summary"], {"directory": 1, "text": 1, "bundle": 1})

    def test_recursive_search(self):
        payload = self.state.list_entries(query="avatar")
        self.assertEqual(len(payload["entries"]), 1)
        self.assertEqual(payload["entries"][0]["path"], "images/avatar.png")

    def test_regex_search_uses_root_relative_path(self):
        payload = self.state.list_entries(query=r"^images/.+\.png$", regex=True)
        self.assertEqual([item["path"] for item in payload["entries"]], ["images/avatar.png"])
        with self.assertRaises(BrowserError):
            self.state.list_entries(query="[", regex=True)

    def test_filters_by_inclusive_modified_date(self):
        payload = self.state.list_entries(modified_from="2024-01-15", modified_to="2024-01-15")
        self.assertEqual([item["name"] for item in payload["entries"]], ["notes.txt"])

    def test_rejects_parent_traversal(self):
        with self.assertRaises(BrowserError):
            self.state.resolve("../outside.txt")


class ResourceBrowserHttpTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "hello.txt").write_text("你好 ArkUnpacker", encoding="utf-8")
        (self.root / "audio.wav").write_bytes(b"0123456789")
        self.server = ResourceBrowserServer(("127.0.0.1", 0), self.root)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temp.cleanup()

    def get_json(self, route):
        with urlopen(self.base + route, timeout=2) as response:
            return json.loads(response.read().decode("utf-8"))

    def test_serves_app_and_directory_api(self):
        with urlopen(self.base + "/", timeout=2) as response:
            page = response.read().decode("utf-8")
            self.assertIn("资源浏览器", page)
            self.assertIn('data-sort="name"', page)
            self.assertIn('id="inspector-resizer"', page)
            self.assertIn('id="settings-modal"', page)
            self.assertIn('id="resource-tooltip"', page)
            self.assertIn('id="regex-toggle"', page)
            self.assertIn('id="date-filter-panel"', page)
        payload = self.get_json("/api/files")
        self.assertEqual({item["name"] for item in payload["entries"]}, {"hello.txt", "audio.wav"})

    def test_text_preview_and_byte_range(self):
        payload = self.get_json("/api/text?" + urlencode({"path": "hello.txt"}))
        self.assertEqual(payload["text"], "你好 ArkUnpacker")
        request = Request(
            self.base + "/api/file?" + urlencode({"path": "audio.wav"}),
            headers={"Range": "bytes=2-5"},
        )
        with urlopen(request, timeout=2) as response:
            self.assertEqual(response.status, 206)
            self.assertEqual(response.read(), b"2345")

        with urlopen(self.base + "/api/file?" + urlencode({"path": "hello.txt", "download": 1}), timeout=2) as response:
            disposition = response.headers["Content-Disposition"]
            self.assertIn("filename*=UTF-8''hello.txt", disposition)

    def test_http_api_rejects_parent_traversal(self):
        with self.assertRaises(HTTPError) as context:
            urlopen(self.base + "/api/file?" + urlencode({"path": "../outside.txt"}), timeout=2)
        self.assertEqual(context.exception.code, 400)


class BundleStoreIntegrationTest(unittest.TestCase):
    def test_indexes_and_exports_image_from_real_bundle(self):
        bundle = Path(__file__).parent / "res" / "client-2.2" / "arts-ui-common.ab"
        store = BundleStore(max_entries=1)
        description = store.describe(bundle)
        self.assertGreater(description["objectCount"], 0)
        image = next(item for item in description["objects"] if item["kind"] == "image")
        # A JSON round trip must preserve signed 64-bit Unity PathIDs exactly.
        browser_payload = json.loads(json.dumps(description, ensure_ascii=False))
        browser_image = next(item for item in browser_payload["objects"] if item["kind"] == "image")
        self.assertIsInstance(browser_image["pathId"], str)
        self.assertEqual(browser_image["pathId"], image["pathId"])
        self.assertIsInstance(browser_image["objectId"], str)
        payload = store.object_payload(bundle, object_id=browser_image["objectId"])
        self.assertEqual(payload.content_type, "image/png")
        self.assertTrue(payload.data.startswith(b"\x89PNG\r\n\x1a\n"))

        with tempfile.TemporaryDirectory() as output_dir:
            archive_path = Path(output_dir) / "unpacked.zip"
            stats = store.write_archive(bundle, archive_path)
            self.assertGreater(stats["exported"], 0)
            with zipfile.ZipFile(archive_path) as archive:
                names = archive.namelist()
                self.assertIn("_arkunpacker_manifest.json", names)
                self.assertTrue(any(name.endswith(".png") for name in names))
                manifest = json.loads(archive.read("_arkunpacker_manifest.json"))
                self.assertEqual(manifest["exportedFileCount"], stats["exported"])

    def test_composite_object_ids_disambiguate_nested_path_ids(self):
        root_file = SimpleNamespace(name="outer.ab", parent=None)
        inner_file = SimpleNamespace(name="inner.ab", parent=root_file)
        serialized_file = SimpleNamespace(name="CAB-inner", parent=inner_file)

        def reader(name):
            return SimpleNamespace(
                path_id=1,
                type=SimpleNamespace(name="GameObject"),
                byte_size=10,
                assets_file=serialized_file,
                peek_name=lambda: name,
            )

        first, second = reader("first"), reader("second")
        environment = SimpleNamespace(file=root_file, objects=[first, second])
        bundle = BrowserBundle(environment, "fallback.ab")
        self.assertEqual([item["pathId"] for item in bundle.entries], ["1", "1"])
        self.assertEqual([item["objectId"] for item in bundle.entries], ["0", "1"])
        self.assertEqual(bundle.entries[0]["source"], "outer.ab/inner.ab/CAB-inner")
        self.assertIs(bundle.get_reader(object_id="0"), first)
        self.assertIs(bundle.get_reader(object_id="1"), second)
        with self.assertRaises(BrowserError):
            bundle.get_reader(path_id=1)


@unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg is required for USM preview")
class UsmPreviewHttpTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).parent / "res" / "client-2.5"
        self.filename = "raw-video-main_10-main_10_enter.usm"
        self.server = ResourceBrowserServer(("127.0.0.1", 0), self.root)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def test_prepares_browser_mp4_and_supports_range(self):
        query = urlencode({"path": self.filename})
        # Downloading without a cache must prepare the MP4 first, then return it
        # as an attachment while preserving byte-range support.
        download_request = Request(
            self.base + "/api/usm/preview?" + query + "&download=1",
            headers={"Range": "bytes=4-7"},
        )
        with urlopen(download_request, timeout=60) as response:
            self.assertEqual(response.status, 206)
            self.assertEqual(response.read(), b"ftyp")
            self.assertTrue(response.headers["Content-Disposition"].startswith("attachment;"))
            self.assertIn("raw-video-main_10-main_10_enter.mp4", response.headers["Content-Disposition"])

        # Preparing again should reuse the cached MP4.
        with urlopen(self.base + "/api/usm/prepare?" + query, timeout=60) as response:
            payload = json.loads(response.read().decode("utf-8"))
            self.assertTrue(payload["ready"])
            self.assertGreater(payload["size"], 0)

        request = Request(self.base + "/api/usm/preview?" + query, headers={"Range": "bytes=4-7"})
        with urlopen(request, timeout=5) as response:
            self.assertEqual(response.status, 206)
            self.assertEqual(response.read(), b"ftyp")


if __name__ == "__main__":
    unittest.main()

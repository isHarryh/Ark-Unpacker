"use strict";

const state = {
  root: "",
  path: "",
  kind: "all",
  query: "",
  regexMode: false,
  dateFrom: "",
  dateTo: "",
  bundle: null,
  selected: null,
  directoryItems: [],
  sortKey: "name",
  sortDirection: "asc",
  requestToken: 0,
};

const preferences = {
  fontScale: "arkunpacker.webui.fontScale",
  inspectorWidth: "arkunpacker.webui.inspectorWidth",
};

const $ = (selector) => document.querySelector(selector);
const elements = {
  rootForm: $("#root-form"),
  rootInput: $("#root-input"),
  kindNav: $("#kind-nav"),
  breadcrumbs: $("#breadcrumbs"),
  title: $("#view-title"),
  subtitle: $("#view-subtitle"),
  search: $("#search-input"),
  searchBox: $(".search-box"),
  regexToggle: $("#regex-toggle"),
  dateFilterButton: $("#date-filter-button"),
  dateFilterPanel: $("#date-filter-panel"),
  dateFrom: $("#date-from"),
  dateTo: $("#date-to"),
  applyDateFilter: $("#apply-date-filter"),
  clearDateFilter: $("#clear-date-filter"),
  refresh: $("#refresh-button"),
  list: $("#resource-list"),
  loading: $("#loading"),
  empty: $("#empty-state"),
  detailColumnTitle: $("#detail-column-title"),
  sortButtons: [...document.querySelectorAll(".resource-table th button[data-sort]")],
  inspector: $("#inspector"),
  inspectorResizer: $("#inspector-resizer"),
  preview: $("#preview"),
  metadata: $("#metadata"),
  download: $("#download-button"),
  closeInspector: $("#close-inspector"),
  settingsButton: $("#settings-button"),
  settingsModal: $("#settings-modal"),
  closeSettings: $("#close-settings"),
  fontScale: $("#font-scale"),
  fontScaleValue: $("#font-scale-value"),
  resetInspectorWidth: $("#reset-inspector-width"),
  resetSettings: $("#reset-settings"),
  toast: $("#toast"),
  tooltip: $("#resource-tooltip"),
};

const labels = {
  directory: "目录", bundle: "AssetBundle", image: "图片", audio: "音频",
  text: "文本", video: "视频", model: "模型", object: "Unity 对象", other: "文件",
};
const icons = {
  directory: "⌑", bundle: "AB", image: "IMG", audio: "♪", text: "TXT",
  video: "▶", model: "3D", object: "U", other: "·",
};

function esc(value) {
  return String(value ?? "").replace(/[&<>'"]/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;",
  })[char]);
}

function params(values) {
  const result = new URLSearchParams();
  Object.entries(values).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") result.set(key, value);
  });
  return result.toString();
}

async function api(url, options) {
  const response = await fetch(url, options);
  let payload;
  try { payload = await response.json(); } catch { payload = null; }
  if (!response.ok) throw new Error(payload?.error || `请求失败 (${response.status})`);
  return payload;
}

let toastTimer;
function toast(message) {
  elements.toast.textContent = message;
  elements.toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => elements.toast.classList.remove("show"), 3600);
}

function readPreference(key) {
  try { return localStorage.getItem(key); } catch { return null; }
}

function writePreference(key, value) {
  try {
    if (value === null) localStorage.removeItem(key);
    else localStorage.setItem(key, String(value));
  } catch { /* Local preferences are optional. */ }
}

function applyFontScale(value, persist = true) {
  const scale = Math.max(85, Math.min(150, Number(value) || 110));
  document.documentElement.style.setProperty("--font-scale", String(scale / 100));
  elements.fontScale.value = String(scale);
  elements.fontScaleValue.value = `${scale}%`;
  elements.fontScaleValue.textContent = `${scale}%`;
  if (persist) writePreference(preferences.fontScale, scale);
}

function inspectorWidthLimit() {
  return Math.max(280, Math.min(720, window.innerWidth - 560));
}

function applyInspectorWidth(value, persist = true) {
  const width = Math.round(Math.max(280, Math.min(inspectorWidthLimit(), Number(value) || 356)));
  document.documentElement.style.setProperty("--inspector", `${width}px`);
  elements.inspectorResizer.setAttribute("aria-valuenow", String(width));
  elements.inspectorResizer.setAttribute("aria-valuemin", "280");
  elements.inspectorResizer.setAttribute("aria-valuemax", String(inspectorWidthLimit()));
  if (persist) writePreference(preferences.inspectorWidth, width);
}

function restoreInspectorWidth() {
  writePreference(preferences.inspectorWidth, null);
  document.documentElement.style.removeProperty("--inspector");
  elements.inspectorResizer.removeAttribute("aria-valuenow");
}

function openSettings() {
  elements.settingsModal.hidden = false;
  elements.closeSettings.focus();
}

function closeSettings() {
  elements.settingsModal.hidden = true;
  elements.settingsButton.focus();
}

function formatSize(bytes) {
  if (!Number.isFinite(Number(bytes)) || bytes <= 0) return bytes === 0 ? "—" : "未知";
  const units = ["B", "KB", "MB", "GB", "TB"];
  const power = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  const value = bytes / (1024 ** power);
  return `${value >= 10 || power === 0 ? value.toFixed(0) : value.toFixed(1)} ${units[power]}`;
}

function formatDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.valueOf()) ? "—" : new Intl.DateTimeFormat("zh-CN", {
    year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit",
  }).format(date);
}

function compareText(left, right) {
  return String(left ?? "").localeCompare(String(right ?? ""), "zh-CN", {
    numeric: true,
    sensitivity: "base",
  });
}

function sortItems(items, isBundleObject = false) {
  const direction = state.sortDirection === "desc" ? -1 : 1;
  return [...items].sort((left, right) => {
    if (!isBundleObject) {
      const directoryOrder = Number(left.kind !== "directory") - Number(right.kind !== "directory");
      if (directoryOrder) return directoryOrder;
    }

    let comparison = 0;
    if (state.sortKey === "type") {
      comparison = compareText(
        isBundleObject ? left.type : labels[left.kind] || left.extension,
        isBundleObject ? right.type : labels[right.kind] || right.extension,
      );
    } else if (state.sortKey === "size") {
      comparison = Number(left.size || 0) - Number(right.size || 0);
    } else if (state.sortKey === "detail") {
      if (isBundleObject) {
        const leftId = BigInt(left.pathId);
        const rightId = BigInt(right.pathId);
        comparison = leftId < rightId ? -1 : leftId > rightId ? 1 : 0;
      } else {
        comparison = new Date(left.modified).valueOf() - new Date(right.modified).valueOf();
      }
    } else {
      comparison = compareText(left.name, right.name);
    }
    if (!comparison && state.sortKey !== "name") comparison = compareText(left.name, right.name);
    return comparison * direction;
  });
}

function updateSortHeaders() {
  elements.sortButtons.forEach((button) => {
    const active = button.dataset.sort === state.sortKey;
    const header = button.closest("th");
    header.setAttribute("aria-sort", active ? (state.sortDirection === "asc" ? "ascending" : "descending") : "none");
    button.querySelector("i").textContent = active ? (state.sortDirection === "asc" ? "↑" : "↓") : "";
  });
}

let tooltipTimer;
let tooltipPointer = { x: 0, y: 0 };

function tooltipDetails(item, isBundleObject) {
  const type = isBundleObject ? item.type : labels[item.kind] || item.extension || "文件";
  const rows = [
    ["相对路径", isBundleObject ? state.bundle?.path : item.path, "tooltip-path"],
    ["类型", type],
    ["大小", formatSize(item.size)],
  ];
  if (isBundleObject) {
    if (item.source) rows.push(["内层来源", item.source, "tooltip-path"]);
    rows.push(["对象名称", item.name]);
    rows.push(["PathID", item.pathId]);
  } else if (item.modified) {
    rows.push(["修改时间", formatDate(item.modified)]);
  }
  return `<strong>${esc(item.name)}</strong><dl>${rows.map(([key, value, className]) => (
    `<dt>${esc(key)}</dt><dd class="${esc(className || "")}">${esc(value || "—")}</dd>`
  )).join("")}</dl>`;
}

function positionTooltip() {
  if (elements.tooltip.hidden) return;
  const margin = 10;
  const offset = 14;
  const rect = elements.tooltip.getBoundingClientRect();
  let left = tooltipPointer.x + offset;
  let top = tooltipPointer.y + offset;
  if (left + rect.width > window.innerWidth - margin) left = tooltipPointer.x - rect.width - offset;
  if (top + rect.height > window.innerHeight - margin) top = tooltipPointer.y - rect.height - offset;
  elements.tooltip.style.left = `${Math.max(margin, left)}px`;
  elements.tooltip.style.top = `${Math.max(margin, top)}px`;
}

function scheduleTooltip(item, isBundleObject, event) {
  tooltipPointer = { x: event.clientX, y: event.clientY };
  clearTimeout(tooltipTimer);
  tooltipTimer = setTimeout(() => {
    elements.tooltip.innerHTML = tooltipDetails(item, isBundleObject);
    elements.tooltip.hidden = false;
    positionTooltip();
  }, 320);
}

function moveTooltip(event) {
  tooltipPointer = { x: event.clientX, y: event.clientY };
  positionTooltip();
}

function hideTooltip() {
  clearTimeout(tooltipTimer);
  elements.tooltip.hidden = true;
}

function renderBreadcrumbs(bundleName = "") {
  const pieces = state.path ? state.path.split("/") : [];
  let cumulative = "";
  const html = [`<button data-path="">ROOT</button>`];
  pieces.forEach((piece) => {
    cumulative = cumulative ? `${cumulative}/${piece}` : piece;
    html.push(`<b>/</b><button data-path="${esc(cumulative)}">${esc(piece)}</button>`);
  });
  if (bundleName) html.push(`<b>/</b><span>${esc(bundleName)}</span>`);
  elements.breadcrumbs.innerHTML = html.join("");
}

function updateCounts(summary = {}, total = 0) {
  ["bundle", "image", "audio", "text", "video", "model"].forEach((kind) => {
    $(`#count-${kind}`).textContent = summary[kind] ?? "—";
  });
  $("#count-all").textContent = total;
}

function rowHtml(item, isBundleObject = false) {
  const kind = item.kind || "other";
  const type = isBundleObject ? item.type : labels[kind] || item.extension || "文件";
  const time = isBundleObject ? item.pathId : formatDate(item.modified);
  return `<tr data-key="${esc(isBundleObject ? item.objectId ?? item.pathId : item.path)}">
    <td><div class="name-cell"><span class="file-icon ${esc(kind)}">${esc(icons[kind] || "·")}</span><span class="file-name">${esc(item.name)}</span></div></td>
    <td><span class="type-pill">${esc(type)}</span></td>
    <td>${esc(formatSize(item.size))}</td>
    <td>${esc(time)}</td>
  </tr>`;
}

function bindRows(items, isBundleObject = false) {
  hideTooltip();
  elements.list.innerHTML = items.map((item) => rowHtml(item, isBundleObject)).join("");
  [...elements.list.children].forEach((row, index) => {
    const current = items[index];
    const selectedKey = isBundleObject ? state.selected?.objectId ?? state.selected?.pathId : state.selected?.path;
    const currentKey = isBundleObject ? current.objectId ?? current.pathId : current.path;
    if (selectedKey !== undefined && String(selectedKey) === String(currentKey)) {
      row.classList.add("selected");
    }
    row.addEventListener("click", () => selectItem(items[index], row, isBundleObject));
    row.addEventListener("mouseenter", (event) => scheduleTooltip(items[index], isBundleObject, event));
    row.addEventListener("mousemove", moveTooltip);
    row.addEventListener("mouseleave", hideTooltip);
    row.addEventListener("dblclick", () => {
      const item = items[index];
      if (!isBundleObject && item.kind === "directory") openDirectory(item.path);
      if (!isBundleObject && item.kind === "bundle") openBundle(item);
    });
  });
  elements.empty.hidden = items.length > 0;
}

function setLoading(loading) {
  elements.loading.hidden = !loading;
}

async function loadDirectory() {
  const token = ++state.requestToken;
  state.bundle = null;
  state.selected = null;
  closePreview();
  setLoading(true);
  try {
    elements.searchBox.classList.remove("regex-error");
    const data = await api(`/api/files?${params({
      path: state.path,
      q: state.query,
      kind: state.kind,
      regex: state.regexMode ? 1 : undefined,
      modifiedFrom: state.dateFrom,
      modifiedTo: state.dateTo,
    })}`);
    if (token !== state.requestToken) return;
    state.root = data.root;
    state.directoryItems = data.entries;
    elements.dateFilterButton.disabled = false;
    elements.detailColumnTitle.textContent = "修改时间";
    elements.rootInput.value = data.root;
    renderBreadcrumbs();
    elements.title.textContent = state.path.split("/").pop() || "资源根目录";
    const searchNote = state.query ? `搜索“${state.query}” · ` : "";
    const dateNote = state.dateFrom || state.dateTo ? `时间范围 ${state.dateFrom || "不限"} 至 ${state.dateTo || "不限"} · ` : "";
    elements.subtitle.textContent = `${searchNote}${dateNote}${data.entries.length} 个项目${data.truncated ? " · 结果已截断" : ""}`;
    bindRows(sortItems(data.entries));
    updateSortHeaders();
    updateCounts(data.summary, data.entries.length);
  } catch (error) {
    if (state.regexMode && error.message.startsWith("正则表达式无效")) {
      elements.searchBox.classList.add("regex-error");
    }
    toast(error.message);
    elements.list.innerHTML = "";
    elements.empty.hidden = false;
  } finally {
    if (token === state.requestToken) setLoading(false);
  }
}

async function openDirectory(path, { preserveQuery = false } = {}) {
  state.path = path || "";
  if (!preserveQuery) {
    state.query = "";
    elements.search.value = "";
  }
  await loadDirectory();
}

async function openBundle(item) {
  const token = ++state.requestToken;
  setLoading(true);
  try {
    const data = await api(`/api/bundle?${params({ path: item.path })}`);
    if (token !== state.requestToken) return;
    state.bundle = { ...data, file: item };
    elements.dateFilterButton.disabled = true;
    elements.dateFilterPanel.hidden = true;
    elements.dateFilterButton.setAttribute("aria-expanded", "false");
    elements.detailColumnTitle.textContent = "PathID";
    state.selected = null;
    closePreview();
    renderBreadcrumbs(data.name);
    elements.title.textContent = data.name || item.name;
    elements.subtitle.textContent = `${data.objectCount} 个 Unity 对象 · ${formatSize(item.size)}`;
    const objects = sortItems(filterBundleObjects(data.objects), true);
    bindRows(objects, true);
    updateSortHeaders();
    updateCounts(data.summary, data.objectCount);
  } catch (error) {
    toast(error.message);
  } finally {
    if (token === state.requestToken) setLoading(false);
  }
}

function filterBundleObjects(objects) {
  const query = state.query.toLocaleLowerCase();
  let pattern = null;
  elements.searchBox.classList.remove("regex-error");
  if (state.regexMode && state.query) {
    try {
      pattern = new RegExp(state.query, "i");
    } catch (error) {
      elements.searchBox.classList.add("regex-error");
      toast(`正则表达式无效：${error.message}`);
      return [];
    }
  }
  return objects.filter((item) => {
    const matchesKind = state.kind === "all" || item.kind === state.kind || (state.kind === "text" && item.kind === "object");
    const searchable = `${item.name}\n${item.type}\n${item.pathId}\n${item.source || ""}`;
    const matchesQuery = pattern
      ? pattern.test(searchable)
      : !query
        || item.name.toLocaleLowerCase().includes(query)
        || item.type.toLocaleLowerCase().includes(query)
        || String(item.pathId).includes(query)
        || String(item.source || "").toLocaleLowerCase().includes(query);
    return matchesKind && matchesQuery;
  });
}

function refreshBundleView() {
  if (!state.bundle) return;
  const objects = sortItems(filterBundleObjects(state.bundle.objects), true);
  bindRows(objects, true);
  elements.subtitle.textContent = `${objects.length} / ${state.bundle.objectCount} 个 Unity 对象`;
}

function closePreview() {
  elements.inspector.classList.remove("open");
  elements.preview.innerHTML = `<div class="preview-placeholder"><span>◈</span><p>选择一个资源以查看详情</p></div>`;
  elements.metadata.innerHTML = "";
  elements.download.hidden = true;
  delete elements.download.dataset.bundlePath;
  document.querySelectorAll("#resource-list tr.selected").forEach((row) => row.classList.remove("selected"));
}

async function selectItem(item, row, isBundleObject) {
  document.querySelectorAll("#resource-list tr.selected").forEach((element) => element.classList.remove("selected"));
  row.classList.add("selected");
  state.selected = item;
  elements.inspector.classList.add("open");
  if (!isBundleObject && item.kind === "directory") {
    renderMetadata(item, [{ key: "内容", value: "双击进入目录" }]);
    elements.preview.innerHTML = `<div class="preview-placeholder"><span>⌑</span><p>双击进入 ${esc(item.name)}</p></div>`;
    elements.download.hidden = true;
    return;
  }
  if (!isBundleObject && item.kind === "bundle") {
    renderMetadata(item, [{ key: "操作", value: "双击查看内部对象" }]);
    elements.preview.innerHTML = `<div class="preview-placeholder"><span>⬡</span><p>AssetBundle · 双击打开</p></div>`;
    elements.download.href = `/api/bundle/archive?${params({ path: item.path })}`;
    elements.download.dataset.bundlePath = item.path;
    elements.download.firstChild.textContent = "下载并解包 ZIP ";
    elements.download.hidden = false;
    return;
  }
  if (isBundleObject) await previewBundleObject(item);
  else await previewFile(item);
}

function renderMetadata(item, extra = []) {
  const pairs = [
    { key: "类型", value: item.type || labels[item.kind] || "文件" },
    { key: "大小", value: formatSize(item.size) },
    ...extra,
  ];
  if (item.path) pairs.push({ key: "路径", value: item.path });
  if (item.pathId !== undefined) pairs.push({ key: "PathID", value: item.pathId });
  if (item.modified) pairs.push({ key: "修改时间", value: formatDate(item.modified) });
  elements.metadata.innerHTML = `<h2>${esc(item.name)}</h2><dl>${pairs.map(({ key, value }) => `<dt>${esc(key)}</dt><dd>${esc(value)}</dd>`).join("")}</dl>`;
}

function mediaPreview(kind, url, name) {
  if (kind === "image") return `<img src="${esc(url)}" alt="${esc(name)}">`;
  if (kind === "audio") return `<audio src="${esc(url)}" controls autoplay></audio>`;
  if (kind === "video") return `<video src="${esc(url)}" controls></video>`;
  return "";
}

async function textPreview(url) {
  elements.preview.innerHTML = `<div class="loading"><i></i><span>正在生成预览</span></div>`;
  try {
    const payload = await api(url);
    const suffix = payload.truncated ? "\n\n… 预览内容已截断" : "";
    elements.preview.innerHTML = `<pre>${esc(payload.text + suffix)}</pre>`;
  } catch (error) {
    elements.preview.innerHTML = `<p class="preview-error">${esc(error.message)}</p>`;
  }
}

async function previewFile(item) {
  renderMetadata(item);
  const source = `/api/file?${params({ path: item.path })}`;
  elements.download.href = `/api/file?${params({ path: item.path, download: 1 })}`;
  delete elements.download.dataset.bundlePath;
  elements.download.firstChild.textContent = "下载资源 ";
  elements.download.hidden = false;
  if (item.extension === ".usm") {
    elements.download.href = `/api/usm/preview?${params({ path: item.path, download: 1 })}`;
    elements.download.firstChild.textContent = "下载 MP4 ";
    await previewUsm(item);
    return;
  }
  const media = mediaPreview(item.kind, source, item.name);
  if (media) elements.preview.innerHTML = media;
  else if (["text", "model"].includes(item.kind)) await textPreview(`/api/text?${params({ path: item.path })}`);
  else elements.preview.innerHTML = `<div class="preview-placeholder"><span>${esc(icons[item.kind] || "·")}</span><p>此格式不支持直接预览，可下载查看</p></div>`;
}

async function previewUsm(item) {
  const selectedPath = item.path;
  elements.preview.innerHTML = `<div class="preview-placeholder usm-converting"><i></i><p>正在将 USM 转换为浏览器可播放的 MP4<br><small>首次预览可能需要一些时间</small></p></div>`;
  try {
    await api(`/api/usm/prepare?${params({ path: item.path })}`);
    if (state.selected?.path !== selectedPath) return;
    const source = `/api/usm/preview?${params({ path: item.path })}`;
    elements.preview.innerHTML = mediaPreview("video", source, item.name);
  } catch (error) {
    if (state.selected?.path !== selectedPath) return;
    elements.preview.innerHTML = `<p class="preview-error">${esc(error.message)}</p>`;
  }
}

async function previewBundleObject(item) {
  const sourceDetails = [{ key: "所属 Bundle", value: state.bundle.path }];
  if (item.source) sourceDetails.push({ key: "内层来源", value: item.source });
  renderMetadata(item, sourceDetails);
  const source = `/api/bundle/object?${params({
    path: state.bundle.path,
    objectId: item.objectId,
    pathId: item.objectId === undefined ? item.pathId : undefined,
  })}`;
  elements.download.href = `${source}&download=1`;
  delete elements.download.dataset.bundlePath;
  elements.download.firstChild.textContent = "下载资源 ";
  elements.download.hidden = false;
  const media = mediaPreview(item.kind, source, item.name);
  if (media) {
    elements.preview.innerHTML = media;
  } else {
    elements.preview.innerHTML = `<div class="loading"><i></i><span>正在解析 Unity 对象</span></div>`;
    try {
      const response = await fetch(source);
      if (!response.ok) {
        const payload = await response.json().catch(() => null);
        throw new Error(payload?.error || `预览失败 (${response.status})`);
      }
      const contentType = response.headers.get("Content-Type") || "";
      if (contentType.startsWith("text/") || contentType.includes("json") || item.kind === "model") {
        elements.preview.innerHTML = `<pre>${esc(await response.text())}</pre>`;
      } else {
        elements.preview.innerHTML = `<div class="preview-placeholder"><span>U</span><p>该对象可导出，但浏览器无法直接预览</p></div>`;
      }
    } catch (error) {
      elements.preview.innerHTML = `<p class="preview-error">${esc(error.message)}</p>`;
    }
  }
}

elements.rootForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const data = await api("/api/root", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: elements.rootInput.value.trim() }),
    });
    state.root = data.root;
    state.path = "";
    state.bundle = null;
    await loadDirectory();
  } catch (error) { toast(error.message); }
});

elements.kindNav.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-kind]");
  if (!button) return;
  state.kind = button.dataset.kind;
  elements.kindNav.querySelectorAll("button").forEach((item) => item.classList.toggle("active", item === button));
  if (state.bundle) refreshBundleView(); else loadDirectory();
});

elements.sortButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const key = button.dataset.sort;
    if (state.sortKey === key) state.sortDirection = state.sortDirection === "asc" ? "desc" : "asc";
    else {
      state.sortKey = key;
      state.sortDirection = "asc";
    }
    updateSortHeaders();
    if (state.bundle) refreshBundleView();
    else bindRows(sortItems(state.directoryItems));
  });
});

elements.breadcrumbs.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-path]");
  if (button) openDirectory(button.dataset.path, { preserveQuery: true });
});

let searchTimer;
elements.search.addEventListener("input", () => {
  elements.searchBox.classList.remove("regex-error");
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    state.query = elements.search.value.trim();
    if (state.bundle) refreshBundleView(); else loadDirectory();
  }, 240);
});

elements.regexToggle.addEventListener("click", () => {
  state.regexMode = !state.regexMode;
  elements.regexToggle.classList.toggle("active", state.regexMode);
  elements.regexToggle.setAttribute("aria-pressed", String(state.regexMode));
  elements.searchBox.classList.remove("regex-error");
  if (state.bundle) refreshBundleView();
  else loadDirectory();
});

function updateDateFilterButton() {
  const active = Boolean(state.dateFrom || state.dateTo);
  elements.dateFilterButton.classList.toggle("active", active);
  elements.dateFilterButton.title = active
    ? `修改时间：${state.dateFrom || "不限"} 至 ${state.dateTo || "不限"}`
    : "按修改时间筛选";
}

elements.dateFilterButton.addEventListener("click", () => {
  const willOpen = elements.dateFilterPanel.hidden;
  elements.dateFilterPanel.hidden = !willOpen;
  elements.dateFilterButton.setAttribute("aria-expanded", String(willOpen));
});
elements.applyDateFilter.addEventListener("click", () => {
  const dateFrom = elements.dateFrom.value;
  const dateTo = elements.dateTo.value;
  if (dateFrom && dateTo && dateFrom > dateTo) {
    toast("开始日期不能晚于结束日期");
    return;
  }
  state.dateFrom = dateFrom;
  state.dateTo = dateTo;
  updateDateFilterButton();
  elements.dateFilterPanel.hidden = true;
  elements.dateFilterButton.setAttribute("aria-expanded", "false");
  loadDirectory();
});
elements.clearDateFilter.addEventListener("click", () => {
  state.dateFrom = "";
  state.dateTo = "";
  elements.dateFrom.value = "";
  elements.dateTo.value = "";
  updateDateFilterButton();
  elements.dateFilterPanel.hidden = true;
  elements.dateFilterButton.setAttribute("aria-expanded", "false");
  if (!state.bundle) loadDirectory();
});
document.addEventListener("click", (event) => {
  if (!event.target.closest(".date-filter")) {
    elements.dateFilterPanel.hidden = true;
    elements.dateFilterButton.setAttribute("aria-expanded", "false");
  }
});

elements.refresh.addEventListener("click", () => state.bundle ? openBundle(state.bundle.file) : loadDirectory());
$(".table-wrap").addEventListener("scroll", hideTooltip, { passive: true });
elements.download.addEventListener("click", async (event) => {
  const bundlePath = elements.download.dataset.bundlePath;
  if (!bundlePath) return;
  event.preventDefault();
  if (elements.download.dataset.preparing === "true") return;
  elements.download.dataset.preparing = "true";
  elements.download.setAttribute("aria-disabled", "true");
  elements.download.firstChild.textContent = "正在解包并生成 ZIP… ";
  try {
    const result = await api(`/api/bundle/archive/prepare?${params({ path: bundlePath })}`);
    if (elements.download.dataset.bundlePath === bundlePath) {
      elements.download.firstChild.textContent = `下载 ZIP（${result.exported} 个文件） `;
    }
    window.location.assign(`/api/bundle/archive?${params({ path: bundlePath })}`);
  } catch (error) {
    toast(error.message);
    if (elements.download.dataset.bundlePath === bundlePath) {
      elements.download.firstChild.textContent = "下载并解包 ZIP ";
    }
  } finally {
    delete elements.download.dataset.preparing;
    elements.download.removeAttribute("aria-disabled");
  }
});
elements.closeInspector.addEventListener("click", closePreview);
elements.settingsButton.addEventListener("click", openSettings);
elements.closeSettings.addEventListener("click", closeSettings);
elements.settingsModal.addEventListener("click", (event) => {
  if (event.target === elements.settingsModal) closeSettings();
});
elements.fontScale.addEventListener("input", () => applyFontScale(elements.fontScale.value));
elements.resetInspectorWidth.addEventListener("click", restoreInspectorWidth);
elements.resetSettings.addEventListener("click", () => {
  applyFontScale(110);
  restoreInspectorWidth();
});

let resizeStartX = 0;
let resizeStartWidth = 0;
elements.inspectorResizer.addEventListener("pointerdown", (event) => {
  if (window.innerWidth <= 820 || event.button !== 0) return;
  resizeStartX = event.clientX;
  resizeStartWidth = elements.inspector.getBoundingClientRect().width;
  elements.inspectorResizer.setPointerCapture(event.pointerId);
  document.body.classList.add("resizing");
  event.preventDefault();
});
elements.inspectorResizer.addEventListener("pointermove", (event) => {
  if (!elements.inspectorResizer.hasPointerCapture(event.pointerId)) return;
  applyInspectorWidth(resizeStartWidth + resizeStartX - event.clientX);
});
elements.inspectorResizer.addEventListener("pointerup", (event) => {
  if (elements.inspectorResizer.hasPointerCapture(event.pointerId)) {
    elements.inspectorResizer.releasePointerCapture(event.pointerId);
  }
  document.body.classList.remove("resizing");
});
elements.inspectorResizer.addEventListener("dblclick", restoreInspectorWidth);
elements.inspectorResizer.addEventListener("keydown", (event) => {
  if (!["ArrowLeft", "ArrowRight", "Home"].includes(event.key)) return;
  event.preventDefault();
  if (event.key === "Home") restoreInspectorWidth();
  else {
    const current = elements.inspector.getBoundingClientRect().width;
    applyInspectorWidth(current + (event.key === "ArrowLeft" ? 16 : -16));
  }
});
window.addEventListener("resize", () => {
  const savedWidth = Number(readPreference(preferences.inspectorWidth));
  if (savedWidth && window.innerWidth > 820) applyInspectorWidth(savedWidth, false);
});

$(".brand").addEventListener("click", (event) => { event.preventDefault(); openDirectory(""); });
document.addEventListener("keydown", (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key.toLocaleLowerCase() === "k") {
    event.preventDefault(); elements.search.focus(); elements.search.select();
  }
  if (event.key === "Escape") {
    if (!elements.settingsModal.hidden) closeSettings();
    else closePreview();
  }
});

const savedFontScale = Number(readPreference(preferences.fontScale));
applyFontScale(savedFontScale || 110, false);
const savedInspectorWidth = Number(readPreference(preferences.inspectorWidth));
if (savedInspectorWidth && window.innerWidth > 820) applyInspectorWidth(savedInspectorWidth, false);
updateSortHeaders();

api("/api/status")
  .then((data) => { state.root = data.root; elements.rootInput.value = data.root; return loadDirectory(); })
  .catch((error) => toast(error.message));

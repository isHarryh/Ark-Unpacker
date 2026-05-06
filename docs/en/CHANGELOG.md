Changelog / CHANGELOG
==========
<sup> This project only supports Chinese docs. If you are an English user, feel free to contact us. </sup>

| **Mark** |    ★     |    ☆     |   ~~Text~~   |
| :------: | :------: | :------: | :----------: |
| **Meaning** | Major change | Minor change | Deprecated features |

-----

## v5.0
#### Added
1. ★ Added multi-process AssetBundle file unpacking (previously multi-threaded), significantly improving unpacking speed.
2. ★ Added a brand-new interactive CLI, implemented with [Rich](https://github.com/Textualize/rich).
3. Added warnings for overly long working paths.

#### Improved
1. ★ Improved performance of the file write approval mechanism.
2. Improved file path parsing by migrating to the glob module.

#### Dependencies
1. ★ Upgraded UnityPy to 1.25.0.
2. ☆ Upgraded ArkFBSPy to game version 2.7.21.
3. ☆ Introduced [Rich](https://github.com/Textualize/rich) to implement the new interactive CLI.

#### Build
1. ★ Dropped support for Python 3.9.
3. Updated workflow scripts for automated builds.
2. Upgraded Poetry to 2.3.2.

-----

## v4.5
#### Added
1. ★ Added the ability to export AssetBundle TypeTree structures as JSON files.
2. ☆ Added the ability to configure JSON indent and text file encoding in the config file.

#### Fixed
1. ★ \([#30](https://github.com/isHarryh/Ark-Unpacker/issues/30)\) Fixed an issue where enemy Spine models could not be exported when the resource name differed from the program name.
2. ☆ \([#30](https://github.com/isHarryh/Ark-Unpacker/issues/30)\) Fixed an issue where the "ArkModels Extraction and Sorting Tool" could not recognize enemy model directories after game version 2.5.60.
3. Fixed a potential file lock release issue.

#### Improved
1. ★ Optimized game object reading and lookup logic by using lazy loading and LUT-based lookup, improving unpacking speed.
2. Reduced memory usage in some scenarios.
3. Improved accuracy of export file counting used in tests.

#### Patch
1. ★ (v4.5.1) \([#30](https://github.com/isHarryh/Ark-Unpacker/issues/31)\) Fixed an issue where duplicate enemy Spine models could not be exported, and adjusted Spine model renaming logic.
2. ☆ (v4.5.1) Upgraded ArkFBSPy to game version 2.6.91.
3. (v4.5.2) Fixed an issue introduced in this version where some JSON files could not be exported.
4. ☆ (v4.5.3) Upgraded ArkFBSPy to game version 2.7.01.

## v4.4
#### Added
1. ☆ Added robust handling for interactive CLI path input containing quotes.

#### Fixed
1. ☆ Fixed an issue where the "ArkModels Extraction and Sorting Tool" could not sort some dynamic portrait files.

#### Dependencies
1. ★ Upgraded UnityPy to 1.23.0.
2. ☆ Upgraded pyinstaller to 6.17.0.

## v4.3
#### Added
1. ★ \([#24](https://github.com/isHarryh/Ark-Unpacker/issues/24)\) Added automatic throttling of multi-thread task submission when available memory is low.
2. ★ Added extraction of audio and video from Criware USM files.

#### Fixed
1. Fixed a potential issue with incorrect export paths.

#### Improved
1. ☆ Improved file export performance.

#### Dependencies
1. ☆ Upgraded ArkFBSPy to game version 2.6.61.
2. Added psutil to dependencies.

#### Patch
1. (v4.3.1) Fixed an issue where audio/video extraction failed for Criware USM files without audio.
2. (v4.3.1) Fixed incorrect version number display in the app.
3. ☆ (v4.3.1) Upgraded ArkFBSPy to game version 2.6.71.


## v4.2
#### Added
1. ★ Added more granular Spine export categories: DynIllustStart and DynPortrait.

#### Fixed
1. ☆ Fixed mixed-up export results for dynamic portrait Spine models in specific cases.
2. ☆ Fixed an issue where the "ArkModels Extraction and Sorting Tool" could not correctly handle a few dynamic portraits.

#### Improved
1. ★ Improved the parsing approach and reliability before exporting Spine models, thanks to the introduction of spine_asset.

#### Dependencies
1. ☆ Added spine_asset to dependencies.
2. Upgraded UnityPy to 1.22.5.
3. Upgraded pycryptodome to 3.23.0.
4. ☆ Upgraded ArkFBSPy to game version 2.5.80.


## v4.1
#### Added
1. ★ Added a dedicated Spine export mode.
2. ★ Added the ability to export Mesh 3D models as OBJ files.

#### Fixed
1. ☆ Fixed an issue where some Spine models for game version 2.5.60 and above could not be parsed.
2. ☆ Fixed an issue where the "ArkModels Extraction and Sorting Tool" could not unpack enemy chibi models for game version 2.5.60 and above.

#### Improved
1. Improved logging system performance.
2. Improved the user experience of entering file paths in the interactive CLI.

#### Patch
1. (v4.1.1) Fixed an issue where certain operators' battle models could not be unpacked correctly. See [#26](https://github.com/isHarryh/Ark-Unpacker/issues/26) for details.
2. (v4.1.1) Fixed an issue where certain operators' base models could not be unpacked correctly.


## v4.0
#### Added
1. ★ Added support for game version 2.5.04 and above by introducing a special decompression algorithm. See [#20](https://github.com/isHarryh/Ark-Unpacker/issues/20) for details.
2. ☆ Added automatic scaling of Spine PNG images to the specified size when the PNG size does not match the size recorded in the ATLAS file.
3. ☆ Added more detailed task information display (for example, running status and accumulated time).

#### Improved
1. Removed the black background in the command line interface.
2. Improved logging system performance.
3. Improved various code logic and type annotations.

#### Dependencies
1. ☆ Upgraded UnityPy to 1.22.1.
2. ☆ Upgraded ArkFBSPy to game version 2.5.04.

#### Build
1. ★ Dropped support for Python 3.8. The build now uses Python 3.12, significantly improving performance.
2. ★ Dropped Poetry 1.8. Poetry is now version 2.1.
3. ☆ Updated workflow scripts for automated builds.
4. Other minor dependency version updates.

#### Patch
1. (v4.0.1) Fixed imprecise float serialization when decoding FlatBuffers data files. See [#23](https://github.com/isHarryh/Ark-Unpacker/issues/23) for details.
2. (v4.0.1) Fixed incorrect task progress display for text asset decoding.
3. (v4.0.2) Fixed an error caused by strings that could not be decoded with UTF-8 when decoding FlatBuffers data files.
4. (v4.0.2) Upgraded ArkFBSPy to game version 2.5.60. Note: some FlatBuffers data decoding may not be supported for older game versions.

-----

## v3.6
#### Added
1. ★ Added forced PMA for Spine textures with non-premultiplied alpha (PMA).

#### Fixed
1. \([#19](https://github.com/isHarryh/Ark-Unpacker/issues/19)\) Fixed an issue where `exit` could not be called correctly in packaged builds.

#### Improved
1. ☆ Reduced the size of Windows packaged files, thanks to the fix in [PyInstaller #8799](https://github.com/pyinstaller/pyinstaller/pull/8799).

#### Dependencies
1. ☆ Upgraded UnityPy to 1.20.21.
2. ☆ Upgraded PyInstaller to 6.12.0.
3. ☆ Upgraded ArkFBSPy to game version 2.4.61.

#### Patch
1. (v3.6.1) Upgraded UnityPy to 1.22.0, along with other dependency updates.
2. (v3.6.1) Added exception handling when loading file resources.


## v3.5
#### Added
1. ★ Added the new feature "ArkVoice Extraction and Sorting Tool". See the [supplementary document](docs/ArkVoiceRepoKit.md) for details.

#### Improved
1. ★ Improved audio extraction efficiency, thanks to the multithreading performance improvements in [UnityPy #291](https://github.com/K0lb3/UnityPy/pull/291).
2. Adopted standard-level type checking and improved some code style.

#### Dependencies
1. ☆ Upgraded UnityPy to 1.20.19.
2. ☆ Upgraded PIL to 9.5.0.
3. ☆ Upgraded ArkFBSPy to game version 2.4.41.


## v3.4
#### Added
1. ☆ Added support for extensionless (non-binary) skeleton files in the "ArkModels Extraction and Sorting Tool".

#### Improved
1. ★ Refactored task time tracking logic to improve remaining time estimation accuracy.
2. ☆ Refactored Spine model parsing logic.
3. ★ Adopted basic-level type checking and improved inappropriate type annotations.

#### Dependencies
1. ☆ Upgraded ArkFBSPy to game version 2.4.21 (2).
2. Upgraded PyInstaller to 6.10.0.
3. Other minor dependency version updates.

#### Patch
1. (v3.4.1) Adapted to field structure changes in some Spine models introduced in game version 2.4.21.


## v3.3
#### Added
1. ★ Added support for unpacking anonymous BIN files.

#### Improved
1. ☆ Refactored game data acquisition logic in the "ArkModels Extraction and Sorting Tool", since game data has been stored as anonymous files since game version 2.4.01.

#### Dependencies
1. ☆ Upgraded ArkFBSPy to game version 2.4.01.
2. Upgraded UnityPy to 1.10.18 and added archspec to dependencies.
3. Upgraded pycryptodome to 3.21.
4. Other minor dependency version updates.

#### Patch
1. ☆ (v3.3.1) Upgraded ArkFBSPy to game version 2.4.21.


## v3.2
#### Added
1. ★ Added decoding for AES-CBC encrypted files. This feature has been merged with FlatBuffers decoding into "Decode Text Assets".

#### Fixed
1. Fixed a possible `AttributeError` when unpacking early AB files.

#### Improved
1. ☆ Optimized various code logic and fixed code style issues.
2. Improved logging system performance.

#### Dependencies
1. ★ Introduced PyLint as the code linting system.
2. ☆ Upgraded ArkFBSPy to game version 2.3.21.
3. Added bson and pycryptodome to dependencies.

#### Patch
1. ☆ (v3.2.1) Upgraded ArkFBSPy to game version 2.3.81.


## v3.1
#### Added
1. ★ Added the ability to start the program and run tasks directly via the command line.

#### Fixed
1. ☆ Fixed a probabilistic failure when unpacking audio files caused by `Fmoderror`.

#### Improved
1. Removed the delay wait after task completion.

#### Dependencies
1. Upgraded UnityPy to 1.10.14.


## v3.0
#### Added
1. ★ Added multi-threaded file writing based on dynamically scheduled Workers, improving save speed.
2. ☆ Added support for unpacking a single AB file.
3. Added the ability to enter `*` in some input operations to cancel a task.
4. ☆ Added a dedicated export option for Spine model asset types.
5. ★ Added decoding for binary data files encoded with FlatBuffers.
6. ☆ Added the "Generate Dataset" feature using local `gamedata` in the "ArkModels Extraction and Sorting Tool".
7. Added the "One-click Execution" feature in the "ArkModels Extraction and Sorting Tool".

#### Fixed
1. ★ Fixed an issue where file writing could probabilistically lose files due to thread contention in specific cases.
2. Fixed a potential cross-platform compatibility issue caused by `os.system`.

#### Improved
1. ☆ Optimized various code logic and fixed code style issues.
2. Improved duplicate filename suffix format, now using `$` instead of `#`.
3. Improved text prompts in the interactive CLI.
4. Improved path parsing, file filtering, and file list reading logic.
5. ☆ Refactored the "Generate Dataset" and "Merge Images" logic to use an object-oriented approach.
6. Improved the mapping between configuration performance levels and thread counts.
7. ★ Improved task progress calculations and progress bar display, improving remaining time estimation accuracy.
8. ☆ Refactored the "Sort Models" logic in the "ArkModels Extraction and Sorting Tool".
9. ☆ Improved handling of runtime exceptions.

#### Build
1. ★ Added automated build scripts, optimizing steps for distributable builds.
2. ★ Implemented direct packaging of Windows executables without virtualization packaging.
3. ☆ Added GitHub Actions CI to implement build workflows.
4. ★ Added automated unit test scripts and test resource files.

#### Dependencies
1. ★ Introduced Poetry as the dependency management system.
2. Upgraded PyInstaller to 6.8.0.
3. ☆ Added ArkFBSPy as a Git Submodule.
4. Added flatbuffers and numpy to dependencies.
5. ☆ Removed requests from dependencies and dropped calls to the ArknightsGameData repository.

-----

## v2.7
#### Added
1. ★ Added automatic selection of the maximum thread count based on CPU core count, removing the need for manual configuration.

#### Improved
1. Improved code self-documentation style and localized some self-documentation content.
2. Improved package import logic.
3. Improved various style issues and spelling mistakes in code.
4. ☆ Improved data export and saving logic for resource classes.
5. ☆ Improved config file read/write logic and robustness.


## v2.6
#### Added
1. ★ Added extraction and sorting support for dynamic portraits in the "ArkModels Extraction and Sorting Tool".

#### Improved
1. ☆ Optimized UI output printing logic to reduce unnecessary performance overhead.


## v2.5
#### Improved
1. ★ Optimized multithreading allocation logic. The file writing system now supports multi-threading, improving unpacking speed for large AB files.
2. ☆ Optimized program directory structure by separating some scripts.
3. ~~Optimized default configuration, including but not limited to increasing the default thread count to 16.~~
4. Adjusted file list reading logic.

#### Build
1. Published build scripts, bundled libraries, and step-by-step instructions. See the [build directory](build).


## v2.4
#### Fixed
1. ★ Fixed an issue where Spine models with multiple textures (for example, Sui Xiang and some operators' dynamic portraits) could not export image files correctly.

#### Improved
1. ☆ Refactored CLI output printing to use Unicode control characters for more aesthetic and efficient output.
2. Improved directory tree deletion for faster deletion.
3. Improved sorting logic in the "ArkModels Extraction and Sorting Tool" for faster sorting.
4. Improved multithreading allocation logic during unpacking to improve speed.


## v2.3
#### Added
1. ★ Added a logging system. The program saves logs to the working directory for later inspection and troubleshooting.
2. ★ Added a configuration file. The program reads the config file at startup, allowing users to adjust some settings by editing it.

#### Fixed
1. ☆ Fixed an issue where battle chibi and base chibi name collisions caused Spine models to be exported incorrectly. Base chibi are now exported to the `Building` subdirectory.

#### Improved
1. Adjusted file list reading logic.


## v2.2
#### Added
1. ★ Added extraction and sorting support for enemy models in the "ArkModels Extraction and Sorting Tool".

#### Fixed
1. ☆ ([#4](https://github.com/isHarryh/Ark-Unpacker/issues/4)) Fixed inaccurate front/back image distinction for battle chibi images.


## v2.1
#### Added
1. ★ Added the "ArkModels Extraction and Sorting Tool" feature. See the [supplementary document](docs/ArkModelsRepoKit.md) for details.


## v2.0
#### Added
1. ★ Added and enabled multi-threaded resource unpacking and image merging by default, greatly improving runtime speed.
2. ~~Added support for custom thread count in custom mode.~~

#### Improved
1. Improved runtime echoing and printing speed.
2. Improved image matching accuracy and tuned algorithm parameters.
3. No longer supports streaming detailed runtime info; only concise output (progress bar mode) is shown.

#### Fixed
1. ☆ Fixed an issue where the destination could be saved incorrectly in specific cases: when the task target relative path contains `..`, it can now be saved correctly.

#### Documentation
1. Organized the documentation and created the [docs directory](docs) to store supplementary documents.

#### Test Data
Test results for this version on the author's PC:
> PC configuration
> -- Windows 10 (64-bit)
> -- CPU 2.00GHz, RAM 8.00GB
> Arknights version
> -- Android v1.9.01
> Test scope
> -- "One-click Execution" for the entire Android folder
> -- Thread mode: 8 threads
> -- Source folder: 5.19GB(6.8K files)
> Test results
> -- Time: 1.5h
> -- Unpacked assets folder: 13.5GB(61K files)
> -- Merged images folder: 2.04GB(5.8K files)

-----

## v1.2
#### Added
1. ★ Added support for placing files unpacked from different AB files into separate subfolders for categorized storage.
2. ☆ Added support for displaying estimated remaining task time.

#### Improved
1. Removed echo output when creating directories.

#### Test Data
Test results for this version on the author's PC:
> PC configuration
> -- Windows 10 (64-bit)
> -- CPU 2.00GHz, RAM 8.00GB
> Arknights version
> -- Android v1.8.81
> Test scope
> -- "One-click Execution" for the entire Android folder
> -- Source folder: 5.06GB(6.6K files)
> Test results
> -- Time: 3.0h
> -- Unpacked assets folder: 20.1GB(70K files)
> -- Merged images folder: 2.03GB(5.2K files)


## v1.1
#### Added
1. Added the app icon and window title at runtime.

#### Improved
1. ☆ Optimized various code logic, such as string concatenation and file list parsing logic.
2. ☆ Optimized file saving logic. When files in the folder have similar names and identical contents, no save operation is performed.
3. ☆ Optimized the image merging algorithm: now uses `PIL.Image` built-in `putalpha` to merge RGB and Alpha channel images, greatly improving merging efficiency.
4. Improved information echo for the image merging task.

#### Fixed
1. ☆ Fixed an issue where operator battle chibi resources could not be fully exported due to duplicate names.
2. Fixed an issue where merged images could not be saved by directory.
3. ☆ Fixed an issue where operator battle chibi images could not be correctly matched and merged.
4. ☆ Fixed a name collision save conflict: ~~now automatically adds the `_#` suffix to distinguish duplicate files~~, and no longer requires user configuration for overwrite behavior.
5. Fixed an unexpected error when trying to save zero-size images; these invalid images are now skipped.
6. ☆ Fixed inaccurate matching between RGB and Alpha channel images. After the fix, a few mismatches may still occur.

#### Build
1. Fixed a potential missing `fmod.dll` in the executable.
2. ☆ Packaged the executable using file virtualization technology.

#### Test Data
Test results for this version on the author's PC:
> PC configuration
> -- Windows 10 (64-bit)
> -- CPU 2.00GHz, RAM 8.00GB
> Arknights version
> -- Android v1.8.01
> Test scope
> -- "One-click Execution" for the entire Android folder
> -- Source folder: 4.74GB(5.9K files)
> Test results
> -- Time: 2.5h
> -- Unpacked assets folder: 18.4GB(57K files)
> -- Merged images folder: 1.90GB(5.4K files)

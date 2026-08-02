CHANGELOG
==========

|  **表示**   |      ★       |      ☆       |      ~~Text~~       |
| :---------: | :----------: | :----------: | :-----------------: |
|  **含义**   |   重大变更   |   主要变更   |    已弃用的特性     |
| **Meaning** | Major change | Minor change | Deprecated features |

-----

## v5.1
#### 修复 (Fixed)
1. ★ \([#33](https://github.com/isHarryh/Ark-Unpacker/pull/33)\) 修复了解包大量文件时可能的进度假死问题。  
   [EN] Fixed the potential progress freeze issue when unpacking a large number of files.

#### 优化 (Improved)
1. ★ 重构了任务调度和 Worker Pool。  
   [EN] Refactored task scheduling and worker pool.

#### 依赖 (Dependencies)
1. ☆ 将 UnityPy 升级到了 1.25.3。  
   [EN] Upgraded UnityPy to 1.25.3.
2. ☆ 将 ArkFBSPy 库升级到游戏版本 2.7.61。  
   [EN] Upgraded ArkFBSPy to game version 2.7.61.
3. 将 pyinstaller 升级到了 6.20.0。  
   [EN] Upgraded pyinstaller to 6.20.0.

## v5.0
#### 新增 (Added)
1. ★ 新增了多进程 AssetBundle 文件解包的特性（先前是多线程解包），大幅提升了解包速度。  
   [EN] Added multi-process AssetBundle file unpacking (previously multi-threaded), significantly improving unpacking speed.
2. ★ 新增了全新的交互式命令行界面，基于 [Rich](https://github.com/Textualize/rich) 实现。  
   [EN] Added a brand-new interactive CLI, implemented with [Rich](https://github.com/Textualize/rich).
3. 新增了对过长工作路径的警告提示。  
   [EN] Added warnings for overly long working paths.

#### 优化 (Improved)
1. ★ 优化了文件写入的审批机制的性能表现。  
   [EN] Improved performance of the file write approval mechanism.
2. 优化了解析文件路径的方式，迁移到 glob 模块。  
   [EN] Improved file path parsing by migrating to the glob module.

#### 依赖 (Dependencies)
1. ★ 将 UnityPy 升级到了 1.25.0。  
   [EN] Upgraded UnityPy to 1.25.0.
2. ☆ 将 ArkFBSPy 库升级到游戏版本 2.7.21。  
   [EN] Upgraded ArkFBSPy to game version 2.7.21.
3. ☆ 引入了 [Rich](https://github.com/Textualize/rich) 库来实现全新的交互式命令行界面。  
   [EN] Introduced [Rich](https://github.com/Textualize/rich) to implement the new interactive CLI.

#### 构建 (Build)
1. ★ 弃用了 Python 3.9。  
   [EN] Dropped support for Python 3.9.
2. 更新了自动化构建的工作流脚本。  
   [EN] Updated workflow scripts for automated builds.
3. 将 Poetry 升级到了 2.3.2。  
   [EN] Upgraded Poetry to 2.3.2.

#### 补丁 (Patch)
1. ☆ (v5.0.1) 将 ArkFBSPy 库升级到游戏版本 2.7.41。  
   [EN] (v5.0.1) Upgraded ArkFBSPy to game version 2.7.41.

## v4.5
#### 新增 (Added)
1. ★ 新增了可以导出 AssetBundle 文件的 TypeTree 结构为 JSON 文件的功能。  
   [EN] Added the ability to export AssetBundle TypeTree structures as JSON files.
2. ☆ 新增了可以在配置文件中调整导出 JSON 文件的缩进、导出文本格式文件时采用的文件编码的功能。  
   [EN] Added the ability to configure JSON indent and text file encoding in the config file.

#### 修复 (Fixed)
1. ★ \([#30](https://github.com/isHarryh/Ark-Unpacker/issues/30)\) 修复了无法导出资源名称与编程名称不一致的敌方 Spine 模型的问题。  
   [EN] \([#30](https://github.com/isHarryh/Ark-Unpacker/issues/30)\) Fixed an issue where enemy Spine models could not be exported when the resource name differed from the program name.
2. ☆ \([#30](https://github.com/isHarryh/Ark-Unpacker/issues/30)\) 修复了“ArkModels提取与分拣工具”无法识别 2.5.60 游戏版本后的敌方模型目录的问题。  
   [EN] \([#30](https://github.com/isHarryh/Ark-Unpacker/issues/30)\) Fixed an issue where the "ArkModels Extraction and Sorting Tool" could not recognize enemy model directories after game version 2.5.60.
3. 修复了潜在的文件锁释放问题。  
   [EN] Fixed a potential file lock release issue.

#### 优化 (Improved)
1. ★ 优化了游戏对象的读取和查找逻辑，现在采用懒加载读取和 LUT 对象查找法，提升了解包速度。  
   [EN] Optimized game object reading and lookup logic by using lazy loading and LUT-based lookup, improving unpacking speed.
2. 优化了部分情况下的内存占用。  
   [EN] Reduced memory usage in some scenarios.
3. 优化了测试所用的导出文件清点的准确性。  
   [EN] Improved accuracy of export file counting used in tests.

#### 补丁 (Patch)
1. ★ (v4.5.1) \([#30](https://github.com/isHarryh/Ark-Unpacker/issues/31)\) 修复了无法导出重复的敌方 Spine 模型的问题，并且调整了 Spine 模型的重命名逻辑。  
   [EN] (v4.5.1) \([#30](https://github.com/isHarryh/Ark-Unpacker/issues/31)\) Fixed an issue where duplicate enemy Spine models could not be exported, and adjusted Spine model renaming logic.
2. ☆ (v4.5.1) 将 ArkFBSPy 库升级到游戏版本 2.6.91。  
   [EN] (v4.5.1) Upgraded ArkFBSPy to game version 2.6.91.
3. (v4.5.2) 修复了此版本引入的无法导出某些 JSON 文件的问题。  
   [EN] (v4.5.2) Fixed an issue introduced in this version where some JSON files could not be exported.
4. ☆ (v4.5.3) 将 ArkFBSPy 库升级到游戏版本 2.7.01。  
   [EN] (v4.5.3) Upgraded ArkFBSPy to game version 2.7.01.

## v4.4
#### 新增 (Added)
1. ☆ 新增了对含有引号的交互式命令行路径输入的鲁棒性适配。  
   [EN] Added robust handling for interactive CLI path input containing quotes.

#### 修复 (Fixed)
1. ☆ 修复了“ArkModels提取与分拣工具”无法分拣某些动态立绘文件的问题。  
   [EN] Fixed an issue where the "ArkModels Extraction and Sorting Tool" could not sort some dynamic portrait files.

#### 依赖 (Dependencies)
1. ★ 将 UnityPy 升级到了 1.23.0。  
   [EN] Upgraded UnityPy to 1.23.0.
2. ☆ 将 pyinstaller 升级到了 6.17.0。  
   [EN] Upgraded pyinstaller to 6.17.0.

## v4.3
#### 新增 (Added)
1. ★ \([#24](https://github.com/isHarryh/Ark-Unpacker/issues/24)\) 新增了在设备可用内存较低时，可以自动阻滞多线程任务提交的特性。  
   [EN] \([#24](https://github.com/isHarryh/Ark-Unpacker/issues/24)\) Added automatic throttling of multi-thread task submission when available memory is low.
2. ★ 新增了从 Criware USM 文件中提取音视频文件的功能。  
   [EN] Added extraction of audio and video from Criware USM files.

#### 修复 (Fixed)
1. 修复了潜在的的导出路径不正确的问题。  
   [EN] Fixed a potential issue with incorrect export paths.

#### 优化 (Improved)
1. ☆ 优化了文件导出的性能表现。  
   [EN] Improved file export performance.

#### 依赖 (Dependencies)
1. ☆ 将 ArkFBSPy 库升级到游戏版本 2.6.61。  
   [EN] Upgraded ArkFBSPy to game version 2.6.61.
2. 将 psutil 添加到了依赖项中。  
   [EN] Added psutil to dependencies.

#### 补丁 (Patch)
1. (v4.3.1) 修复了无法从不含音频的 Criware USM 文件中进行音视频提取的问题。  
   [EN] (v4.3.1) Fixed an issue where audio/video extraction failed for Criware USM files without audio.
2. (v4.3.1) 修复了软件内版本号显示有误的问题。  
   [EN] (v4.3.1) Fixed incorrect version number display in the app.
3. ☆ (v4.3.1) 将 ArkFBSPy 库升级到游戏版本 2.6.71。  
   [EN] (v4.3.1) Upgraded ArkFBSPy to game version 2.6.71.

## v4.2
#### 新增 (Added)
1. ★ 新增了更加细分的 Spine 模型导出分类：DynIllustStart 和 DynPortrait。  
   [EN] Added more granular Spine export categories: DynIllustStart and DynPortrait.

#### 修复 (Fixed)
1. ☆ 修复了特定情况下动态立绘 Spine 模型的导出结果混乱的问题。  
   [EN] Fixed mixed-up export results for dynamic portrait Spine models in specific cases.
2. ☆ 修复了“ArkModels提取与分拣工具”无法正确处理极个别动态立绘的问题。  
   [EN] Fixed an issue where the "ArkModels Extraction and Sorting Tool" could not correctly handle a few dynamic portraits.

#### 优化 (Improved)
1. ★ 优化了 Spine 模型的导出前解析的方式和可靠性，这得益于 spine_asset 库的引入。  
   [EN] Improved the parsing approach and reliability before exporting Spine models, thanks to the introduction of spine_asset.

#### 依赖 (Dependencies)
1. ☆ 将 spine_asset 添加到了依赖项中。  
   [EN] Added spine_asset to dependencies.
2. 将 UnityPy 升级到了 1.22.5。  
   [EN] Upgraded UnityPy to 1.22.5.
3. 将 pycryptodome升级到了 3.23.0。  
   [EN] Upgraded pycryptodome to 3.23.0.
4. ☆ 将 ArkFBSPy 库升级到游戏版本 2.5.80。  
   [EN] Upgraded ArkFBSPy to game version 2.5.80.

## v4.1
#### 新增 (Added)
1. ★ 新增了单独的 Spine 模型导出模式。  
   [EN] Added a dedicated Spine export mode.
2. ★ 新增了可以导出 Mesh 对象的 3D 模型为 OBJ 文件的功能。  
   [EN] Added the ability to export Mesh 3D models as OBJ files.

#### 修复 (Fixed)
1. ☆ 修复了无法解析游戏版本 2.5.60 及以上的部分 Spine 模型的问题。  
   [EN] Fixed an issue where some Spine models for game version 2.5.60 and above could not be parsed.
2. ☆ 修复了“ArkModels提取与分拣工具”不支持解包游戏版本 2.5.60 及以上的敌方小人模型的问题。  
   [EN] Fixed an issue where the "ArkModels Extraction and Sorting Tool" could not unpack enemy chibi models for game version 2.5.60 and above.

#### 优化 (Improved)
1. 优化了日志系统的性能表现。  
   [EN] Improved logging system performance.
2. 优化了在交互式命令行界面中输入文件路径的用户体验。  
   [EN] Improved the user experience of entering file paths in the interactive CLI.

#### 补丁 (Patch)
1. (v4.1.1) 修复了无法正确解包个别干员的战斗模型的问题，详情参见 [#26](https://github.com/isHarryh/Ark-Unpacker/issues/26)。  
   [EN] (v4.1.1) Fixed an issue where certain operators' battle models could not be unpacked correctly. See [#26](https://github.com/isHarryh/Ark-Unpacker/issues/26) for details.
2. (v4.1.1) 修复了无法正确解包个别干员的基建模型的问题。  
   [EN] (v4.1.1) Fixed an issue where certain operators' base models could not be unpacked correctly.

## v4.0
#### 新增 (Added)
1. ★ 新增了针对游戏版本 2.5.04 及以上的支持，引入了特殊的解压算法，详情参见 [#20](https://github.com/isHarryh/Ark-Unpacker/issues/20)。  
   [EN] Added support for game version 2.5.04 and above by introducing a special decompression algorithm. See [#20](https://github.com/isHarryh/Ark-Unpacker/issues/20) for details.
2. ☆ 新增了在 Spine 模型的 PNG 图片尺寸与 ATLAS 文件中记录的尺寸不匹配时，会自动缩放 PNG 图片到规定的尺寸的特性。  
   [EN] Added automatic scaling of Spine PNG images to the specified size when the PNG size does not match the size recorded in the ATLAS file.
3. ☆ 新增了更为详细的任务信息显示（例如运行状态和累计耗时）。  
   [EN] Added more detailed task information display (for example, running status and accumulated time).

#### 优化 (Improved)
1. 移除了命令行界面的黑色背景。  
   [EN] Removed the black background in the command line interface.
2. 优化了日志系统的性能表现。  
   [EN] Improved logging system performance.
3. 优化了各类代码逻辑和类型注解。  
   [EN] Improved various code logic and type annotations.

#### 依赖 (Dependencies)
1. ☆ 将 UnityPy 升级到了 1.22.1。  
   [EN] Upgraded UnityPy to 1.22.1.
2. ☆ 将 ArkFBSPy 库升级到游戏版本 2.5.04。  
   [EN] Upgraded ArkFBSPy to game version 2.5.04.

#### 构建 (Build)
1. ★ 弃用了 Python 3.8，目前构建版的 Python 版本采用的是 3.12，大幅提升了性能。  
   [EN] Dropped support for Python 3.8. The build now uses Python 3.12, significantly improving performance.
2. ★ 弃用了 Poetry 1.8，目前 Poetry 版本采用的是 2.1。  
   [EN] Dropped Poetry 1.8. Poetry is now version 2.1.
3. ☆ 更新了自动化构建的工作流脚本。  
   [EN] Updated workflow scripts for automated builds.
4. 其他次级依赖项的版本更新。  
   [EN] Other minor dependency version updates.

#### 补丁 (Patch)
1. (v4.0.1) 修复了解码 FlatBuffers 数据文件时，浮点数的序列化不精确的问题，详情参见 [#23](https://github.com/isHarryh/Ark-Unpacker/issues/23)。  
   [EN] (v4.0.1) Fixed imprecise float serialization when decoding FlatBuffers data files. See [#23](https://github.com/isHarryh/Ark-Unpacker/issues/23) for details.
2. (v4.0.1) 修复了文本资源解码的任务进度显示不正确的问题。  
   [EN] (v4.0.1) Fixed incorrect task progress display for text asset decoding.
3. (v4.0.2) 修复了解码 FlatBuffers 数据文件时，无法使用 UTF-8 解码的字符串会引发错误的问题。  
   [EN] (v4.0.2) Fixed an error caused by strings that could not be decoded with UTF-8 when decoding FlatBuffers data files.
4. (v4.0.2) 将 ArkFBSPy 库升级到游戏版本 2.5.60。注意，旧的游戏版本的某些 FlatBuffers 数据解码有可能不受支持。  
   [EN] (v4.0.2) Upgraded ArkFBSPy to game version 2.5.60. Note: some FlatBuffers data decoding may not be supported for older game versions.

## v3.6
#### 新增 (Added)
1. ★ 新增了针对非预乘 Alpha (PMA) 的 Spine 模型纹理强制启用 PMA 的特性。  
   [EN] Added forced PMA for Spine textures with non-premultiplied alpha (PMA).

#### 修复 (Fixed)
1. \([#19](https://github.com/isHarryh/Ark-Unpacker/issues/19)\) 修复了在打包版本中无法正确调用 `exit` 的问题。  
   [EN] \([#19](https://github.com/isHarryh/Ark-Unpacker/issues/19)\) Fixed an issue where `exit` could not be called correctly in packaged builds.

#### 优化 (Improved)
1. ☆ 减少了 Windows 打包文件的大小，这得益于 [PyInstaller #8799](https://github.com/pyinstaller/pyinstaller/pull/8799) 的修复。  
   [EN] Reduced the size of Windows packaged files, thanks to the fix in [PyInstaller #8799](https://github.com/pyinstaller/pyinstaller/pull/8799).

#### 依赖 (Dependencies)
1. ☆ 将 UnityPy 升级到了 1.20.21。  
   [EN] Upgraded UnityPy to 1.20.21.
2. ☆ 将 PyInstaller 升级到了 6.12.0。  
   [EN] Upgraded PyInstaller to 6.12.0.
3. ☆ 将 ArkFBSPy 库升级到游戏版本 2.4.61。  
   [EN] Upgraded ArkFBSPy to game version 2.4.61.

#### 补丁 (Patch)
1. (v3.6.1) 将 UnityPy 升级到了 1.22.0，以及其他依赖性的更新。  
   [EN] (v3.6.1) Upgraded UnityPy to 1.22.0, along with other dependency updates.
2. (v3.6.1) 增加了在载入文件资源时的异常捕获。  
   [EN] (v3.6.1) Added exception handling when loading file resources.

## v3.5
#### 新增 (Added)
1. ★ 支持新功能“ArkVoice提取与分拣工具”，详情参见[附加文档](docs/ArkVoiceRepoKit.md)。  
   [EN] Added the new feature "ArkVoice Extraction and Sorting Tool". See the [supplementary document](docs/ArkVoiceRepoKit.md) for details.

#### 优化 (Improved)
1. ★ 优化了提取音频文件时的效率，这得益于 [UnityPy #291](https://github.com/K0lb3/UnityPy/pull/291) 对于多线程性能的改进。  
   [EN] Improved audio extraction efficiency, thanks to the multithreading performance improvements in [UnityPy #291](https://github.com/K0lb3/UnityPy/pull/291).
2. 采用了标准级类型检查，优化了部分代码样式。  
   [EN] Adopted standard-level type checking and improved some code style.

#### 依赖 (Dependencies)
1. ☆ 将 UnityPy 升级到了 1.20.19。  
   [EN] Upgraded UnityPy to 1.20.19.
2. ☆ 将 PIL 升级到了 9.5.0。  
   [EN] Upgraded PIL to 9.5.0.
3. ☆ 将 ArkFBSPy 库升级到游戏版本 2.4.41。  
   [EN] Upgraded ArkFBSPy to game version 2.4.41.

## v3.4
#### 新增 (Added)
1. ☆ 新增了“ArkModels提取与分拣工具”对无扩展名（非二进制）骨骼文件的支持。  
   [EN] Added support for extensionless (non-binary) skeleton files in the "ArkModels Extraction and Sorting Tool".

#### 优化 (Improved)
1. ★ 重构了任务时间记录的代码逻辑，优化了任务剩余时间的估算准确度。  
   [EN] Refactored task time tracking logic to improve remaining time estimation accuracy.
2. ☆ 重构了 Spine 模型解析的代码逻辑。  
   [EN] Refactored Spine model parsing logic.
3. ★ 采用了基本级类型检查，优化了不恰当的类型注解。  
   [EN] Adopted basic-level type checking and improved inappropriate type annotations.

#### 依赖 (Dependencies)
1. ☆ 将 ArkFBSPy 库升级到游戏版本 2.4.21 (2)。  
   [EN] Upgraded ArkFBSPy to game version 2.4.21 (2).
2. 将 PyInstaller 升级到了 6.10.0。  
   [EN] Upgraded PyInstaller to 6.10.0.
3. 其他次级依赖项的版本更新。  
   [EN] Other minor dependency version updates.

#### 补丁 (Patch)
1. (v3.4.1) 适应了游戏版本 2.4.21 出现的部分 Spine 模型的字段结构变更。  
   [EN] (v3.4.1) Adapted to field structure changes in some Spine models introduced in game version 2.4.21.

## v3.3
#### 新增 (Added)
1. ★ 新增了对匿名 BIN 文件的解包支持。  
   [EN] Added support for unpacking anonymous BIN files.

#### 优化 (Improved)
1. ☆ 重构了“ArkModels提取与分拣工具”中对游戏数据的获取逻辑，因为游戏数据自游戏版本 2.4.01 起已采用匿名文件存储。  
   [EN] Refactored game data acquisition logic in the "ArkModels Extraction and Sorting Tool", since game data has been stored as anonymous files since game version 2.4.01.

#### 依赖 (Dependencies)
1. ☆ 将 ArkFBSPy 库升级到游戏版本 2.4.01。  
   [EN] Upgraded ArkFBSPy to game version 2.4.01.
2. 将 UnityPy 升级到了 1.10.18，将 archspec 添加到了依赖项中。  
   [EN] Upgraded UnityPy to 1.10.18 and added archspec to dependencies.
3. 将 pycryptodome 升级到了 3.21。  
   [EN] Upgraded pycryptodome to 3.21.
4. 其他次级依赖项的版本更新。  
   [EN] Other minor dependency version updates.

#### 补丁 (Patch)
1. ☆ (v3.3.1) 将 ArkFBSPy 库升级到游戏版本 2.4.21。  
   [EN] (v3.3.1) Upgraded ArkFBSPy to game version 2.4.21.

## v3.2
#### 新增 (Added)
1. ★ 新增了对使用 AES-CBC 加密的文件进行解码的功能，该功能已经与 FlatBuffers 解码功能合并成为“解码文本资源”功能。  
   [EN] Added decoding for AES-CBC encrypted files. This feature has been merged with FlatBuffers decoding into "Decode Text Assets".

#### 修复 (Fixed)
1. 修复了对早期版本 AB 文件进行解包时可能出现的某种 `AttributeError` 错误。  
   [EN] Fixed a possible `AttributeError` when unpacking early AB files.

#### 优化 (Improved)
1. ☆ 优化了各类代码逻辑，修复了各类代码样式问题。  
   [EN] Optimized various code logic and fixed code style issues.
2. 优化了日志系统的性能表现。  
   [EN] Improved logging system performance.

#### 依赖 (Dependencies)
1. ★ 引入了 PyLint 作为代码检查系统。  
   [EN] Introduced PyLint as the code linting system.
2. ☆ 将 ArkFBSPy 库升级到游戏版本 2.3.21。  
   [EN] Upgraded ArkFBSPy to game version 2.3.21.
3. 将 bson 和 pycryptodome 添加到了依赖项中。  
   [EN] Added bson and pycryptodome to dependencies.

#### 补丁 (Patch)
1. ☆ (v3.2.1) 将 ArkFBSPy 库升级到游戏版本 2.3.81。  
   [EN] (v3.2.1) Upgraded ArkFBSPy to game version 2.3.81.

## v3.1
#### 新增 (Added)
1. ★ 新增了可以通过命令行的方式直接启动程序并执行任务的功能。  
   [EN] Added the ability to start the program and run tasks directly via the command line.

#### 修复 (Fixed)
1. ☆ 修复了解包音频文件时有概率因 `Fmoderror` 导致失败的问题。  
   [EN] Fixed a probabilistic failure when unpacking audio files caused by `Fmoderror`.

#### 优化 (Improved)
1. 不再在任务完成后加入延迟等待。  
   [EN] Removed the delay wait after task completion.

#### 依赖 (Dependencies)
1. 将 UnityPy 升级到了 1.10.14。  
   [EN] Upgraded UnityPy to 1.10.14.

## v3.0
#### 新增 (Added)
1. ★ 新增了基于动态调度 Worker 实现的多线程文件写入的功能，提升了保存文件的速度。  
   [EN] Added multi-threaded file writing based on dynamically scheduled Workers, improving save speed.
2. ☆ 新增了支持解包单个 AB 文件的功能。  
   [EN] Added support for unpacking a single AB file.
3. 新增了在部分输入操作中可以输入符号 `*` 来取消任务的功能。  
   [EN] Added the ability to enter `*` in some input operations to cancel a task.
4. ☆ 新增了单独解包 Spine 模型的资源类型导出选项。  
   [EN] Added a dedicated export option for Spine model asset types.
5. ★ 新增了对使用 FlatBuffers 编码的二进制数据文件进行解码的功能。  
   [EN] Added decoding for binary data files encoded with FlatBuffers.
6. ☆ 新增了“ArkModels提取与分拣工具”使用本地 `gamedata` 进行“生成数据集”的特性。  
   [EN] Added the "Generate Dataset" feature using local `gamedata` in the "ArkModels Extraction and Sorting Tool".
7. 新增了“ArkModels提取与分拣工具”内的“一键执行”功能。  
   [EN] Added the "One-click Execution" feature in the "ArkModels Extraction and Sorting Tool".

#### 修复 (Fixed)
1. ★ 修复了特定情况下写入文件时有概率发生由线程竞争导致文件缺失的问题。  
   [EN] Fixed an issue where file writing could probabilistically lose files due to thread contention in specific cases.
2. 修复了由 `os.system` 函数导致的潜在的跨平台兼容性问题。  
   [EN] Fixed a potential cross-platform compatibility issue caused by `os.system`.

#### 优化 (Improved)
1. ☆ 优化了各类代码逻辑，修复了各类代码样式问题。  
   [EN] Optimized various code logic and fixed code style issues.
2. 优化了文件重名的后缀命名格式，现在采用 `$` 后缀，而不是 `#` 后缀。  
   [EN] Improved duplicate filename suffix format, now using `$` instead of `#`.
3. 优化了交互式命令行的文本提示。  
   [EN] Improved text prompts in the interactive CLI.
4. 优化了路径解析、文件筛选和文件列表读取的逻辑。  
   [EN] Improved path parsing, file filtering, and file list reading logic.
5. ☆ 重构了“生成数据集”和“合并图片”的代码逻辑，现在采用了面向对象的模式。  
   [EN] Refactored the "Generate Dataset" and "Merge Images" logic to use an object-oriented approach.
6. 优化了配置文件性能等级与多线程数量的映射关系。  
   [EN] Improved the mapping between configuration performance levels and thread counts.
7. ★ 优化了任务进度的计算逻辑和进度条的显示，优化了任务剩余时间的估算准确度。  
   [EN] Improved task progress calculations and progress bar display, improving remaining time estimation accuracy.
8. ☆ 重构了“ArkModels提取与分拣工具”中“分拣模型”的代码逻辑。  
   [EN] Refactored the "Sort Models" logic in the "ArkModels Extraction and Sorting Tool".
9. ☆ 优化了对运行时异常的处理。  
   [EN] Improved handling of runtime exceptions.

#### 构建 (Build)
1. ★ 新增了自动化的构建脚本，优化了构建可分发文件的步骤。  
   [EN] Added automated build scripts, optimizing steps for distributable builds.
2. ★ 实现了针对 Windows 系统的可执行文件的直接打包，不再采用虚拟化打包。  
   [EN] Implemented direct packaging of Windows executables without virtualization packaging.
3. ☆ 新增了 GitHub Actions 的持续集成，实现了构建工作流。  
   [EN] Added GitHub Actions CI to implement build workflows.
4. ★ 新增了自动化的单元测试脚本，新增了测试用资源文件。  
   [EN] Added automated unit test scripts and test resource files.

#### 依赖 (Dependencies)
1. ★ 引入了 Poetry 作为依赖管理系统。  
   [EN] Introduced Poetry as the dependency management system.
2. 将 PyInstaller 升级到了 6.8.0。  
   [EN] Upgraded PyInstaller to 6.8.0.
3. ☆ 作为 Git Submodule 引入了 ArkFBSPy 模块。  
   [EN] Added ArkFBSPy as a Git Submodule.
4. 将 flatbuffers 和 numpy 添加到了依赖项中。  
   [EN] Added flatbuffers and numpy to dependencies.
5. ☆ 将 requests 从依赖项中移除，取消了对 ArknightsGameData 仓库的调用。  
   [EN] Removed requests from dependencies and dropped calls to the ArknightsGameData repository.

## v2.7
#### 新增 (Added)
1. ★ 新增了根据设备CPU核心数来自动选择最大多线程数量的功能，不再需要手动设置此参数。  
   [EN] Added automatic selection of the maximum thread count based on CPU core count, removing the need for manual configuration.

#### 优化 (Improved)
1. 优化了代码自文档的样式，并进行了部分自文档的国际化。  
   [EN] Improved code self-documentation style and localized some self-documentation content.
2. 优化了软件包的导入逻辑。  
   [EN] Improved package import logic.
3. 优化了代码内各类样式问题和拼写错误。  
   [EN] Improved various style issues and spelling mistakes in code.
4. ☆ 优化了资源类的数据导出和保存逻辑。  
   [EN] Improved data export and saving logic for resource classes.
5. ☆ 优化了配置文件的读写逻辑和鲁棒性。  
   [EN] Improved config file read/write logic and robustness.

## v2.6
#### 新增 (Added)
1. ★ 新增了“ArkModels提取与分拣工具”对于动态立绘的提取和分拣支持。  
   [EN] Added extraction and sorting support for dynamic portraits in the "ArkModels Extraction and Sorting Tool".

#### 优化 (Improved)
1. ☆ 优化了用户界面输出的打印逻辑，减少了不必要的性能消耗。  
   [EN] Optimized UI output printing logic to reduce unnecessary performance overhead.

## v2.5
#### 优化 (Improved)
1. ★ 优化了多线程分配逻辑，文件写入系统已支持多线程，提升了大型ab文件的解包速度。  
   [EN] Optimized multithreading allocation logic. The file writing system now supports multi-threading, improving unpacking speed for large AB files.
2. ☆ 优化了程序的目录结构，分离了部分程序脚本。  
   [EN] Optimized program directory structure by separating some scripts.
3. ~~优化了默认配置，包括但不限于将默认的多线程数上调至16。~~  
   [EN] ~~Optimized default configuration, including but not limited to increasing the default thread count to 16.~~
4. 调整了读取文件列表的代码逻辑。  
   [EN] Adjusted file list reading logic.

#### 构建 (Build)
1. 公开了构建所用的脚本、附加库文件和步骤说明，参见[build目录](build)。  
   [EN] Published build scripts, bundled libraries, and step-by-step instructions. See the [build directory](build).

## v2.4
#### 修复 (Fixed)
1. ★ 修复了无法正确导出拥有多纹理图的Spine模型（例如岁相、部分干员动态立绘）的图片文件的问题。  
   [EN] Fixed an issue where Spine models with multiple textures (for example, Sui Xiang and some operators' dynamic portraits) could not export image files correctly.

#### 优化 (Improved)
1. ☆ 重构了命令行界面的打印方式，现在采用Unicode控制符进行更美观高效的打印操作。  
   [EN] Refactored CLI output printing to use Unicode control characters for more aesthetic and efficient output.
2. 优化了删除目录树的方式，提升了删除的速度。  
   [EN] Improved directory tree deletion for faster deletion.
3. 优化了“ArkModels提取与分拣工具”的分拣逻辑，提升了分拣的速度。  
   [EN] Improved sorting logic in the "ArkModels Extraction and Sorting Tool" for faster sorting.
4. 优化了解包时的多线程分配逻辑，提升了解包的速度。  
   [EN] Improved multithreading allocation logic during unpacking to improve speed.

## v2.3
#### 新增 (Added)
1. ★ 新增了日志系统。程序运行时会在工作目录保存日志文件，以便后续的检查和故障排除等操作。  
   [EN] Added a logging system. The program saves logs to the working directory for later inspection and troubleshooting.
2. ★ 新增了配置文件。程序启动时会在工作目录读取配置文件，用户可以通过编辑该文件来调整部分设置参数。  
   [EN] Added a configuration file. The program reads the config file at startup, allowing users to adjust some settings by editing it.

#### 修复 (Fixed)
1. ☆ 修复了战斗小人与基建小人重名等特定情况下，无法正确分类导出Spine模型文件的问题。现在基建小人会单独导出到 `Building` 子目录中。  
   [EN] Fixed an issue where battle chibi and base chibi name collisions caused Spine models to be exported incorrectly. Base chibi are now exported to the `Building` subdirectory.

#### 优化 (Improved)
1. 调整了读取文件列表的代码逻辑。  
   [EN] Adjusted file list reading logic.

## v2.2
#### 新增 (Added)
1. ★ 新增了“ArkModels提取与分拣工具”对于敌方模型的提取与分拣支持。  
   [EN] Added extraction and sorting support for enemy models in the "ArkModels Extraction and Sorting Tool".

#### 修复 (Fixed)
1. ☆ ([#4](https://github.com/isHarryh/Ark-Unpacker/issues/4)) 修复了战斗小人图片正背面图片区分不准确的问题。  
   [EN] ([#4](https://github.com/isHarryh/Ark-Unpacker/issues/4)) Fixed inaccurate front/back image distinction for battle chibi images.

## v2.1
#### 新增 (Added)
1. ★ 支持新功能“ArkModels提取与分拣工具”，详情参见[附加文档](docs/ArkModelsRepoKit.md)。  
   [EN] Added the "ArkModels Extraction and Sorting Tool" feature. See the [supplementary document](docs/ArkModelsRepoKit.md) for details.

## v2.0
#### 新增 (Added)
1. ★ 支持且默认以多线程模式运行资源解包和图片合并，极大地提升了运行速度。  
   [EN] Added and enabled multi-threaded resource unpacking and image merging by default, greatly improving runtime speed.
2. ~~支持在自定义模式下可以自定义多线程数的功能。~~  
   [EN] ~~Added support for custom thread count in custom mode.~~

#### 优化 (Improved)
1. 优化了运行时的回显表现和打印速度。  
   [EN] Improved runtime echoing and printing speed.
2. 优化了图片匹配的精确度，调整了算法的参数。  
   [EN] Improved image matching accuracy and tuned algorithm parameters.
3. 不再支持流式显示运行时的详细信息，现在都只以简洁模式（进度条模式）回显信息。  
   [EN] No longer supports streaming detailed runtime info; only concise output (progress bar mode) is shown.

#### 修复 (Fixed)
1. ☆ 修复了特定情况下保存目的地异常的问题：现在任务目标相对路径含有 `..` 时，也能被正确地保存。  
   [EN] Fixed an issue where the destination could be saved incorrectly in specific cases: when the task target relative path contains `..`, it can now be saved correctly.

#### 文档 (Documentation)
1. 整理了说明文档，建立了[docs目录](docs)用于存储附加说明文档。  
   [EN] Organized the documentation and created the [docs directory](docs) to store supplementary documents.

## v1.2
#### 新增 (Added)
1. ★ 支持将不同ab文件中解包出的文件分别放到不同的子文件夹中，以便分类保存。  
   [EN] Added support for placing files unpacked from different AB files into separate subfolders for categorized storage.
2. ☆ 支持显示任务的预计剩余时间。  
   [EN] Added support for displaying estimated remaining task time.

#### 优化 (Improved)
1. 移除了目录创建时的回显。  
   [EN] Removed echo output when creating directories.

## v1.1
#### 新增 (Added)
1. 新增了程序运行时的图标和窗口标题。  
   [EN] Added the app icon and window title at runtime.

#### 优化 (Improved)
1. ☆ 优化了各种代码逻辑，例如字符串的拼接和文件列表的解析逻辑。  
   [EN] Optimized various code logic, such as string concatenation and file list parsing logic.
2. ☆ 优化了文件的保存逻辑。当文件夹内存在文件名相似、内容完全相同的文件时，不会进行保存操作。  
   [EN] Optimized file saving logic. When files in the folder have similar names and identical contents, no save operation is performed.
3. ☆ 优化了图片合并的算法：现在使用 `PIL.Image` 的内置函数 `putalpha` 来合并RGB通道图和A通道图，极大地提升了图片合并的效率。  
   [EN] Optimized the image merging algorithm: now uses `PIL.Image` built-in `putalpha` to merge RGB and Alpha channel images, greatly improving merging efficiency.
4. 优化了图片合并任务的信息回显。  
   [EN] Improved information echo for the image merging task.

#### 修复 (Fixed)
1. ☆ 修复了干员战斗小人相关资源由于重名而不能正确地全部导出的问题。  
   [EN] Fixed an issue where operator battle chibi resources could not be fully exported due to duplicate names.
2. 修复了图片合并时，不能按目录分别保存的问题。  
   [EN] Fixed an issue where merged images could not be saved by directory.
3. ☆ 修复了干员战斗小人相关图片无法被正确地匹配和合并的问题。  
   [EN] Fixed an issue where operator battle chibi images could not be correctly matched and merged.
4. ☆ 修复了重名的文件保存冲突的问题：~~现在会自动添加 `_#` 后缀来区分重名的文件~~，且不再需要用户配置是否执行覆盖。  
   [EN] Fixed a name collision save conflict: ~~now automatically adds the `_#` suffix to distinguish duplicate files~~, and no longer requires user configuration for overwrite behavior.
5. 修复了在试图保存大小为0的图片时抛出意外错误的问题，现在这些无效图片会被直接跳过。  
   [EN] Fixed an unexpected error when trying to save zero-size images; these invalid images are now skipped.
6. ☆ 修复了不能准确匹配RGB通道图和A通道图的问题。修复后不排除还有极个别图片匹配错误。  
   [EN] Fixed inaccurate matching between RGB and Alpha channel images. After the fix, a few mismatches may still occur.

#### 构建 (Build)
1. 修复了可执行文件中潜在的 `fmod.dll` 缺失的问题。  
   [EN] Fixed a potential missing `fmod.dll` in the executable.
2. ☆ 采用了的文件虚拟化技术打包可执行文件。  
   [EN] Packaged the executable using file virtualization technology.

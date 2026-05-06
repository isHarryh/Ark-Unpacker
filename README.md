<!-- 欢迎阅读 Ark-Unpacker 说明文档 -->
<!-- 仓库：https://github.com/isHarryh/Ark-Unpacker -->

<!--suppress HtmlDeprecatedAttribute -->
<div align="center" style="text-align:center">
   <h1> Ark-Unpacker </h1>
   <img alt="ArkUnpacker icon" width="64" src="https://raw.githubusercontent.com/isHarryh/Ark-Unpacker/v3.x/ArkUnpacker.ico"/>
   <p>
      Arknights Assets Unpacker | 明日方舟游戏资源批量解包器 <br>
      <code><b> v5.0 </b></code>
   </p>
   <p>
      <img alt="GitHub Top Language" src="https://img.shields.io/github/languages/top/isHarryh/Ark-Unpacker?label=Python">
      <img alt="GitHub License" src="https://img.shields.io/github/license/isHarryh/Ark-Unpacker?label=License"/>
      <img alt="Code Factor Grade" src="https://img.shields.io/codefactor/grade/github/isHarryh/Ark-Unpacker?label=CodeFactor">
      <img alt="GitHub Actions" src="https://github.com/isHarryh/Ark-Unpacker/actions/workflows/build.yml/badge.svg">
      <img alt="GitHub Downloads" src="https://img.shields.io/github/downloads/isHarryh/Ark-Unpacker/total?label=Downloads">
   </p>
      
   **🇨🇳中文** **|** [🌎English](./README-en.md)

</div>

## 介绍 <sub>Intro</sub>

### 终止更新预告

本项目正在逐步升级和迁移到 [ArkStudio](https://github.com/isHarryh/Ark-Studio)，敬请关注。

> [!NOTE]
> ArkStudio 是正在开发阶段的，功能更加强大的《明日方舟》游戏资源集成式管理平台，开发完成后，当前项目将由于生命周期结束而终止更新，感谢各位一直以来的支持和喜爱。

### 实现的功能

1. 批量解包《明日方舟》Unity AssetBundle(AB) 文件中的游戏资源对象。
   1. 支持游戏版本 v2.5.04 及以上的特殊解压算法；
   2. 解包时可对基建小人、动态立绘和战斗小人的 Spine 模型文件进行区分；
   3. 解包时可以将文件按源 AB 文件的名称分目录存放。
2. 批量合并 RGB 通道图和 Alpha 通道图。
3. 批量解码 FlatBuffers 数据文件。
4. 既提供交互式命令行界面进行操作，也支持直接通过命令行运行。

### 支持的类型

| 类型      | 描述           | 导出格式  |
| :-------- | :------------- | :-------- |
| Sprite    | 精灵图         | PNG 图片  |
| Texture2D | 二维纹理图     | PNG 图片  |
| AudioClip | 音频剪辑       | WAV 音频  |
| TextAsset | 文本或字节数据 | 未指定    |
| Mesh      | 3D 模型        | OBJ 文件  |
| TypeTree  | 对象结构       | JSON 文件 |

### 相关文档

- 更新日志 > [点击查看](docs/zh/CHANGELOG.md)
- 配置文件指引 > [点击查看](docs/zh/ConfigFile.md)
- 游戏资源查找指南 > [点击查看](docs/zh/AssetsGuide.md)

## 使用方法 <sub>Usage</sub>

### 1.资源准备

无论您是想要使用我们的发行版本还是源代码来解包明日方舟的游戏资源，您都需要先获取到明日方舟的资源文件。明日方舟是基于 Unity 开发的游戏，它的游戏资源会全部打包到一种 **AssetBundle文件**（后缀名 `.ab`，下简称“AB文件”，但少数情况下后缀名是 `.bin`）中。

<details>
<summary>📱 安卓端资源获取（展开阅读）</summary>

下面将以 **Android 系统** 为例讲述**如何获取到明日方舟的 AB 文件**。安卓端的游戏资源有 **2 个部分**：

- 一部分是通过**安装包**（`.apk`）提供的，从[明日方舟官网](https://ak.hypergryph.com)将其下载到本地后，使用压缩文件查看工具打开（后缀名改成 `.zip` 后打开），然后把里面的 `assets/AB/Android` 文件夹解压出来；

- 另一部分是通过**热更新**提供的，首先确保您的安卓手机上的明日方舟更新到了最新版本，然后（推荐使用 USB 数据线）将手机存储的 `Android/data/com.hypergryph.arknights/files/Bundles` 文件夹复制到电脑上（重命名为 `Android(2)`）。

> [!TIP]
> 对于使用**模拟器**的用户，可在模拟器中使用文件共享功能，将上述路径的文件夹直接复制到电脑上。若您熟悉 ADB 工具，也可以使用 ADB 来复制这些文件。

至此，我们的目录结构大致如下：

```
你的目录
├─Android
└─Android(2)
```

最后，将 `Android(2)` 文件夹里的内容复制到 `Android` 中，并**覆盖**同名文件，就能得到完整的游戏资源。在这之后，您就可以使用我们的程序来解包其中的游戏资源了。

当然，您也可以将 `Android` 里的部分文件夹复制出来进行处理，以解包特定的资源。

</details>

<details>
<summary>💻 PC 端资源获取（展开阅读）</summary>

下面将以 **Windows 系统** 为例讲述**如何获取到明日方舟的 AB 文件**。步骤如下：

1. 前往[明日方舟官网](https://ak.hypergryph.com)下载并安装鹰角启动器。
2. 在鹰角启动器中，下载明日方舟 PC 端。随后启动游戏，并完成游戏内热更新。
3. 关闭游戏并返回鹰角启动器，点击右下方的菜单按钮，进入“游戏设置”，随后在“游戏安装路径”选项中点击“打开文件目录”按钮。
4. 在 `Arknights_Data` 文件夹中，`StreamingAssets/AB/Windows` 是 PC 端游戏的**初始资源**，`PersistentData/Bundles` 是**热更新资源**。
5. 参照安卓端的资源获取思路进行资源的整合即可。

</details>

<br>

为了便于您找到特定资源的 AB 文件位置，我们整理并列出了各个子目录储存的资源的内容，浏览[此文档](docs/zh/AssetsGuide.md)以查看详情。注意，此文档的内容可能不是最新。

### 2.下载 ArkUnpacker

为了方便一般用户使用，我们推出了适用于 Windows 64位操作系统（暂不支持其他操作系统）的可执行文件。

请进入 Releases 页面下载 exe 文件 `ArkUnpacker-vx.x.x_x64.exe`：[前往下载](https://github.com/isHarryh/Ark-Unpacker/releases)

### 3.必备知识

在正式地使用本程序前，您最好对以下内容有初步了解：

- [RGB 通道图和 A 通道图](docs/zh/Essentials.md#rgb通道图和a通道图)
- [Spine 动画小人](docs/zh/Essentials.md#spine动画小人)

### 4.示例用法

一个最简单的用法是，将需要解包的文件夹（可以是多个）放到程序文件所在的目录中。至此，我们的目录结构大致如下：

```
你的目录
├─Android (解包整个目录需要很久)
├─chararts (可以选择解包部分文件夹)
└─ArkUnpacker.exe
```

然后直接运行程序，弹出交互式命令行界面，依据其提示操作即可。

> [!TIP]
> 运行程序后，工作目录会生成配置文件 `ArkUnpackerConfig.json` 与日志文件 `ArkUnpackerLogs.log`。有关配置文件的字段说明，请参阅[此文档](docs/zh/ConfigFile.md)了解详情。

### 5.各模式的功能概述

#### 一键执行

直接解包程序所在目录中的文件，并执行图片合并。解包出的文件默认导出到 `Unpacked_xxxx` 文件夹，合并完成的图片默认导出到 `Combined_xxxx` 文件夹。

> [!WARNING]
> 不建议直接使用此功能来解包**整个**游戏资源目录。这可能会耗费较长的时间，并且会占用较多系统资源。建议仅对部分文件夹使用此功能，或者使用自定义模式来解包特定的文件夹。

#### 自定义资源解包

解包指定路径的游戏资源，并导出到指定目录。可以选择需要解包哪些资源类型。

#### 自定义图片合并

合并指定路径中的 RGB 图和 Alpha 图，并将合并的结果导出到指定目录。

#### 自定义文本数据解码

解码指定目录中的数据文件，并将解码结果导出到指定目录。具体的原理，请参阅[此文档](docs/zh/TextAssetsDecoding.md)了解详情。

#### 自定义 Spine 模型导出

解包指定路径中的游戏资源，并将其中包含的 Spine 动画小人模型导出到指定目录。

#### 自定义 Criware USM 音视频提取

解包指定路径中的 Criware USM 文件（通常包含过场动画），并将其中包含的音视频文件导出到指定目录。

#### ArkModels 提取与分拣工具

此为定制功能，请参阅[此文档](docs/zh/ArkModelsRepoKit.md)了解详情。

#### ArkVoice 提取与分拣工具

此为定制功能，请参阅[此文档](docs/zh/ArkVoiceRepoKit.md)了解详情。

### 6.命令行用法

除了上述示例用法展示的**交互式**命令行界面外，程序还支持**直接**通过命令行来运行，以便熟悉命令行调用的用户使用。相关参数如下：

```
usage: ArkUnpacker [-h] [-v] [-m {ab,cb,fb,sp,cu}] [-i INPUT] [-o OUTPUT] [-d]
                   [--image] [--text] [--audio] [--spine] [--mesh] [--typetree] [-g]
                   [--no-video] [--no-audio] [-l {0,1,2,3,4}]

Arknights Assets Unpacker. Use no argument to run to enter the interactive CLI mode.

options:
  -h, --help            show this help message and exit
  -v, --version         show a version message and exit
  -m {ab,cb,fb,sp,cu}, --mode {ab,cb,fb,sp,cu}
                        working mode, ab=resolve-ab, cb=combine-image, fb=decode-flatbuffers, sp=resolve-spine, cu=resolve-usm
  -i INPUT, --input INPUT
                        source file or directory path
  -o OUTPUT, --output OUTPUT
                        destination directory path
  -d, -delete           delete the existed destination directory first
  --image               in resolve ab mode: export image files
  --text                in resolve ab mode: export text or binary files
  --audio               in resolve ab mode: export audio files
  --spine               in resolve ab mode: export spine asset files
  --mesh                in resolve ab mode: export mesh resources
  --typetree            in resolve ab mode: export typetree JSON files
  -g, --group           in resolve ab mode: group files into separate directories named by their source ab file
  --no-video            in resolve usm mode: skip video processing
  --no-audio            in resolve usm mode: skip audio processing
  -l {0,1,2,3,4}, --logging-level {0,1,2,3,4}
                        logging level, 0=none, 1=error, 2=warn, 3=info, 4=debug
```

运行 `ArkUnpacker -h` 命令可以显示此帮助信息。如果您使用的命令不带任何 `mode` 参数，那么程序会以交互式命令行界面的模式启动。

## 注意事项 <sub>Notice</sub>

1. 使用一键执行模式时，不会解包直接位于程序所在目录中的 AB 文件，只会解包子文件夹里的 AB 文件。
2. 程序会根据设备 CPU 核心数自动调整多进程策略，并且对设备性能（尤其是 CPU 和硬盘性能）有一定要求，配置过低的电脑在运行时可能会缓慢。
3. Windows 命令行基本常识：
   1. 快捷键 `Ctrl+C` 用于强行终止程序，若想复制文本，请用鼠标选取文本后再按此快捷键。
   2. 左键单击小黑窗会进入“文本选取”模式，此时主程序会暂停执行。
   3. 右键单击小黑窗可以粘贴文本，也可用于退出“文本选取”模式。
   4. 拖放文件到小黑窗可以快速粘贴其路径。
4. 如果您希望了解更多细节或参与贡献，请[查看开发者指引](docs/zh/ForDevelopers.md)。

## 许可证 <sub>Licensing</sub>

本项目基于 **BSD-3 开源协议**。任何人都可以自由地使用和修改项目内的源代码，前提是要在源代码或版权声明中保留作者说明和原有协议，且不可以使用本项目名称或作者名称进行宣传推广。

-----

<div align="center">
    <p><i>GitHub 历史星标图</i></p>
    <a href="https://starchart.cc/isHarryh/Ark-Unpacker">
       <img alt="Stars Chart" src="https://starchart.cc/isHarryh/Ark-Unpacker.svg?variant=adaptive">
    </a>
</div>

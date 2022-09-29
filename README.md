Ark-Unpacker
==========
A tool that can unpack Arknights AB assets automatically.  
明日方舟游戏资源批量解包器  
版本(Version)`v2.0`  

This project only supports Chinese docs. If you are an English user, feel free to contact us.

## 介绍 <sub>Intro</sub>
#### 实现的功能
1. 批量解包UnityAB文件中的图片、文本、音频
    1. 解包时对战斗小人的正背面的文件进行初步区分
    2. 解包时可以将文件按AB文件名分目录存放
2. 批量合并RGB通道图和A通道图
3. 提供命令行式的人性化界面实现上述的功能
4. 支持且默认以多线程模式运行

#### 更新日志
想了解此版本的ArkUnpacker的新特性？
[查看CHANGELOG](./CHANGELOG.md)


## 使用方法 <sub>Usage</sub>

### 1.资源准备
无论您是想要使用我们的发行版本还是源代码来解包明日方舟的游戏资源，您都需要先获取到明日方舟的资源文件。明日方舟是基于Unity开发的游戏，它的游戏资源会全部打包到一种**AssetBundle文件**（`.ab`，下简称"AB文件"）中。

下面将以**Android安卓系统**为例讲述**如何获取到明日方舟的AB文件**。明日方舟的游戏资源有**2个部分**：
* 一部分是通过**安装包**（`.apk`）提供的，从[**官网**](https://ak.hypergryph.com)将其下载到本地后，使用压缩文件查看工具打开（后缀名改成`.zip`后打开），然后把里面的`assets\AB\Android`文件夹解压出来；
* 另一部分是通过**热更新**提供的，首先确保您的安卓手机上的明日方舟更新到了最新版本，然后（推荐使用USB数据线）将手机存储的`Android\data\com.hypergryph.arknights\files\AB\Android`文件夹（一般情况下是这个路径）复制到电脑上（重命名为`Android(2)`）。至此，我们的目录结构大致如下：
> **你的目录**  
> ├─Android  
> └─Android(2)  

最后，将`Android(2)`文件夹里的内容复制到`Android`中，并**覆盖**同名文件，就能得到完整的游戏资源。合并后的文件夹约有5GB大小，在这之后，您就可以使用我们的发行版本或者源代码来解包其中的游戏资源了。

为了方便您找到想要的资源的AB文件，我们整理并列出了各个子目录储存的资源的内容（以安卓`v1.8.61`的明日方舟为例）：
> **Android**  
> ├─activity / 活动   
> ├─arts / 图片  
> ├─audio / 音频  
> ├─avg / 剧情图  
> ├─battle / 战斗相关  
> ├─building / 基建  
> ├─chararts / 干员(立绘和基建小人)  
> ├─charpack / 干员(战斗小人)  
> ├─config / 配置  
> ├─crisisseasons / 危机合约  
> ├─gamedata / 游戏数据  
> ├─graphics / 图形渲染  
> ├─hotupdate / 热更新相关  
> ├─i18n / 多语言(国际化)  
> ├─npcpack / NPC  
> ├─prefabs / 预设文件  
> ├─raw / 未打包文件(例如视频)  
> ├─retro / 复刻活动  
> ├─scenes / 关卡  
> ├─skinpack / 皮肤  
> ├─spritepack / 图标  
> └─ui / 用户界面  
> 
> 提示：在明日方舟`v1.8.01`及之前版本中，干员默认皮肤的立绘、基建小人和战斗小人全都位于`charpack`中；
> 而在之后的版本中，立绘和基建小人被转移到了`chararts`中存放。

### 2.下载ArkUnpacker
为了方便普通用户使用，我们推出了针对`Windows`64位操作系统（暂不支持其他操作系统）的发行版本(Release Version)。它是一个采用文件虚拟化技术打包的可执行文件(`.exe`)，经测试，使用它比直接使用源代码的处理速率提升了接近一倍。

请进入Releases页面下载exe文件“`ArkUnpacker-vx.x.x_x64.exe`”：[前往页面](https://github.com/isHarryh/Ark-Unpacker/releases)

### 3.必备知识
在正式地使用本程序前，您最好对以下内容有初步了解：
* [RGB通道图和A通道图](docs/Essentials.md#rgb通道图和a通道图)
* [Spine动画小人](docs/Essentials.md#spine动画小人)

### 4.示例
首先，将需要解包的文件夹（可以是多个）放到与exe相同的目录下，至此，我们的目录结构大致如下：
> **你的目录**  
> ├─Android (解包整个目录需要很久)  
> ├─charpack (可以选择解包部分文件夹)  
> └─ArkUnpacker.exe  

然后运行exe，弹出一个小黑框（内容如下），这时候只需要依据提示操作即可：
> 欢迎使用ArkUnpacker  
> - - - - - - - - - -  
> 模式选择：  
> 1: 一键执行  
> 2: 自定义资源解包  
> 3: 自定义图片合并  
> 0: 退出  
> 输入序号后按回车即可，如果您不清楚以上功能的含义，强烈建议您先阅读使用手册(README)

“一键执行”模式下，默认以8线程处理任务。此模式下，解包完成的文件（如图片、文本、音频）默认放置在`Unpacked_xxxx`文件夹中，合并完成的图片默认放置在`Combined_xxxx`文件夹中。  
若您选择“自定义资源解包”或“自定义图片合并”，还可以**自定义**解包目标、保存目的地、最大执行线程数等内容。  


## 注意事项 <sub>Notice</sub>
1. 使用一键执行模式时，不会解包与exe**同一目录**下的ab文件，只会解包子文件夹里的ab文件。
2. 本程序对电脑性能（尤其是CPU性能）有一定要求，配置过低的电脑在运行时可能会发热或卡顿。
3. Windows命令行基本常识：
    1. 快捷键`Ctrl+C`用于强行终止程序，若想复制文本，请用鼠标选取文本后再按此快捷键。
    2. 左键单击小黑窗会进入“文本选取”模式，此时程序会暂停。
    3. 右键单击小黑窗可以粘贴文本。
4. 如果程序报错可向我们提交Issue。
5. 欲查看测试数据请[查看CHANGELOG](CHANGELOG.md)
6. 如果您希望了解更多细节请[查看开发者须知](docs/ForDevelopers.md)


## 许可证 <sub>License</sub>
本项目基于**BSD3协议**。任何人都可以自由地使用和修改项目内的源代码，前提是要在源代码或版权声明中保留作者说明和原有协议，且不可以使用本项目名称或作者名称进行宣传推广。

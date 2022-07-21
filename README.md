Ark-Unpacker
==========
A tool that can unpack Arknights AB assets automatically.  
明日方舟游戏资源批量解包器  
版本(Version)`v1.1`  

This project only supports Chinese docs. If you are an English user, feel free to contact us.

## 功能 <sub>Functions</sub>
此版本**计划**实现的功能如下：
1. 批量解包UnityAB文件中的图片、文本、音频
2. 批量合并RGB通道图和A通道图
3. 对战斗小人的正背面的文件进行初步区分**(NEW)**
4. 提供命令行式的人性化界面实现(1)(2)的功能

## 使用方法 <sub>Usage</sub>

### 准备
无论您是想要使用我们的发行版本还是源代码来解包明日方舟的游戏资源，您都需要先获取到明日方舟的资源文件。明日方舟是基于Unity开发的游戏，它的游戏资源全部打包到一种**AssetBundle文件**(后缀名是`.ab`，下简称"AB文件")中。AB文件可以使用第三方工具`AssetStudio`打开，以浏览和解包里面的资源，但是这样十分繁琐，本项目就是致力于批量完成解包任务的。废话不多说，下面将以**Android安卓系统**为例讲述**如何获取到明日方舟的AB文件**。  
明日方舟的游戏资源有**2个部分**：一部分是通过**安装包**(后缀名是`.apk`)提供的，从[官网](https://ak.hypergryph.com)下载到本地后，使用压缩文件查看工具打开(可以尝试先把安装包后缀名改成`.zip`后打开)，然后把里面的`assets\AB\Android`文件夹解压出来(重命名为`Android(APK)`)即可；另一部分是通过**热更新**提供的，首先确保您的安卓手机上的明日方舟更新到了最新版本，然后将其使用USB数据线连接到电脑(为了传输文件，需要先在手机的"设置-开发者模式"中启动"USB调试")，接着在手机存储中找到`Android\data\com.hypergryph.aknights\files\AB\Android`文件夹(一般情况下是这个路径)复制到电脑上(重命名为`Android(Updated)`)。至此，我们的目录结构大致如下：
> **根目录**  
> ├─**Android(APK)**  
> | ├─activity  
> | ├─arts  
> | └─…………  
> └─**Android(Updated)**  
>   ├─activity  
>   ├─arts  
>   └─…………  

最后，将`Android(Updated)`文件夹里的内容复制到`Android(APK)`中，并**覆盖**同名文件，就能得到完整的游戏资源。然后，您就可以使用我们的发行版本或者源代码来解包其中的游戏资源了。为了方便您找到想要的资源的AB文件，我们整理并列出了各个子目录储存的资源的内容(以安卓`v1.8.01`的明日方舟为例)：
> **Android**  
> ├─activity / 活动   
> ├─arts / 图片  
> ├─audio / 音频  
> ├─avg / 剧情图  
> ├─battle / 战斗相关  
> ├─building / 基建  
> ├─charpack / 干员  
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

### 使用发行版本
此版本的程序没有发行版本，因为它尚未完成开发。

### 使用源代码

#### 依赖
源代码使用Python3编写，它依赖于以下外部库，调试前请确保您已使用`pip`安装过：
> [UnityPy](https://github.com/K0lb3/UnityPy)  
> PIL
本项目的主要功能依赖于以下程序文件：
> `src/ResolveAB.py` - 负责实现功能(1)  
> `src/CombineRGBwithA.py` - 负责实现功能(2)
以上程序文件需要以下程序文件的辅助：
> `src/osTool.py` - 提供一些便捷的文件操作函数  
> `src/colorTool.py` - 提供命令行彩色字体的打印
#### 示例
您可以直接运行`Main-v1.1.py`来实现功能(4)。如果您只想利用本项目的代码，来实现一些您自定义的功能，您可以在您的程序中这样写：
```Python
from src import ResolveAB
from src import CombineRGBwithA
ResolveAB.main(['目录1'], '目的地目录1') # ——①
CombineRGBwithA.main(['目录2','目录3'], '目的地目录2') # ——②
```
以上①②两个函数还有其他可选的参数，具体的用法已在代码注释中非常详尽地给出了，在此不再赘述。

## 许可证 <sub>License</sub>
本项目基于**BSD3协议**。任何人都可以自由地使用和修改项目内的源代码，前提是要在源代码或版权声明中保留作者说明和原有协议，且不可以使用本项目名称或作者名称进行宣传推广。

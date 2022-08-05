Ark-Unpacker
==========
A tool that can unpack Arknights AB assets automatically.  
明日方舟游戏资源批量解包器  
版本(Version)`v1.1`  

This project only supports Chinese docs. If you are an English user, feel free to contact us.

## 介绍 <sub>Intro</sub>
#### 实现的功能
1. 批量解包UnityAB文件中的图片、文本、音频
2. 批量合并RGB通道图和A通道图
3. (NEW)对战斗小人的正背面的文件进行初步区分
4. 提供命令行式的人性化界面实现上述的功能

#### 更新日志
[查看CHANGELOG](./CHANGELOG.md)


## 使用方法 <sub>Usage</sub>

### 准备
无论您是想要使用我们的发行版本还是源代码来解包明日方舟的游戏资源，您都需要先获取到明日方舟的资源文件。明日方舟是基于Unity开发的游戏，它的游戏资源会全部打包到一种**AssetBundle文件**（`.ab`，下简称"AB文件"）中。

下面将以**Android安卓系统**为例讲述**如何获取到明日方舟的AB文件**。明日方舟的游戏资源有**2个部分**：
* 一部分是通过**安装包**（`.apk`）提供的，从[**官网**](https://ak.hypergryph.com)将其下载到本地后，使用压缩文件查看工具打开（后缀名改成`.zip`后打开），然后把里面的`assets\AB\Android`文件夹解压出来；
* 另一部分是通过**热更新**提供的，首先确保您的安卓手机上的明日方舟更新到了最新版本，然后（推荐使用USB数据线）将手机存储的`Android\data\com.hypergryph.arknights\files\AB\Android`文件夹（一般情况下是这个路径）复制到电脑上（重命名为`Android(2)`）。至此，我们的目录结构大致如下：
> **你的目录**  
> ├─Android  
> └─Android(2)  

最后，将`Android(2)`文件夹里的内容复制到`Android`中，并**覆盖**同名文件，就能得到完整的游戏资源。合并后的文件夹约有5GB大小，在这之后，您就可以使用我们的发行版本或者源代码来解包其中的游戏资源了。

为了方便您找到想要的资源的AB文件，我们整理并列出了各个子目录储存的资源的内容（以安卓`v1.8.01`的明日方舟为例）：
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


### 理论
#### RGB通道图和A通道图
明日方舟的大部分图片（例如角色立绘、小人图片等）从AB文件中提取出来后，并不是单独的一张图片，而是两张图片：一张有颜色的图（称为RGB通道图），一张只有黑白灰的图（称为A通道图，文件名通常有"alpha"字样）。A通道图中，完全白色的部分表示这里是不透明的，完全黑色的部分表示这里是透明的。欲获得完整的既有颜色又能显示透明度的图片，需要进行图片合并。本项目的[功能](#实现的功能)之一就是自动识别A通道图，然后自动找到对应的RGB通道图，将其合并为完整的图片并保存。

#### Spine小人
明日方舟的小人角色是使用[Spine动画技术](http://esotericsoftware.com)实现的。明日方舟里一套完整的Spine动画通常包含3个文件：包含了各个零散素材的**png图片**、标注各个素材在图片中的位置的**atlas文件**、存储骨骼动画的**skel文件**。  
需要特别注意的是，干员战斗小人具有正面和背面之分，但是在AB文件中它们的png、atlas、skel文件的文件名完全一样。经过攻关，本项目已可以实现区分atlas、skel的正背面，并在解包时将其放入单独的文件夹`BattleFront`和`BattleBack`，（敌人小人和干员基建小人不存在此问题，它们只有正面）。但是，png的正背面尚不能有效区分，解包时会把它们命名为类似于"`xxxx_#1.png`"的形式避免混淆和覆盖。由于小人图片也是RGB和A分离的，因此一个干员会有4张战斗小人图片解包出来，在图片合并时，本项目可以使用特殊算法自动把它的A通道图和RGB通道图进行配对，最终一个干员会有2张战斗小人图片（命名方式仍然是类似于"`xxxx_#1.png`"的形式）。


### 使用发行版本
为了方便普通用户使用，我们推出了针对`Windows`64位操作系统（暂不支持其他操作系统）的发行版本(Release Version)。它是一个采用文件虚拟化技术打包的可执行文件(`.exe`)，经测试，使用它比直接使用源代码的处理速率提升了接近一倍。下面介绍其使用方法和一些细节：

#### 下载
请进入Releases页面下载exe文件“`ArkUnpacker-vx.x.x_x64.exe`”：[前往页面](https://github.com/isHarryh/Ark-Unpacker/releases)

#### 示例
首先，将需要解包的文件夹（可以是多个）放到与exe相同的目录下，至此，我们的目录结构大致如下：
> **你的目录**  
> ├─Android (解包整个目录需要很久)  
> ├─charpack (可以选择解包部分文件夹)  
> ├─skinpack  
> └─ArkUnpacker.exe  

然后运行exe，弹出一个小黑框，这时候只需要依据提示操作即可：
> 欢迎使用ArkUnpacker  
> --------------------  
> 模式选择：  
> 1: 一键执行  
> 2: 自定义资源解包  
> 3: 自定义图片合并  
> 0: 退出  
> 输入序号后按回车即可，如果您不清楚以上功能的含义，强烈建议您先阅读使用手册(README)  

最后，“一键执行”解包完成的文件（如图片、文本、音频）默认放置在`Unpacked_xxxx`文件夹中，合并完成的图片默认放置在`Combined_xxxx`文件夹中。  
若您选择“自定义资源解包”或“自定义图片合并”，还可以**自定义**解包目标和保存目的地。

#### 注意事项
1. 使用一键执行模式时，不会解包与exe**同一目录**下的ab文件，只会解包**文件夹里的**ab文件。
2. 不应打开多个exe同时运行，这不但不会有效提升运行速率，反而可能引起读写冲突。
3. 快捷键`Ctrl+C`用于强行终止程序，若想复制文本，请用鼠标选取文本后再按此快捷键。
4. 左键单击小黑窗会进入“文本选取”模式，此时程序会暂停。
5. 右键单击小黑窗可以粘贴文本。
6. 如果程序报错可向我们提交Issue。

#### 测试数据
[查看CHANGELOG](./CHANGELOG.md)


### 使用源代码
如果您是高级用户或开发者，您才需要阅读以下内容：

您可以把仓库里的`src`和`Main.py`复制到前述的`Android`文件夹或其父文件夹中，然后运行它，来实现功能(4)。在此之前您需要阅读[依赖](#依赖)说明。

#### 依赖
源代码使用**Python3**编写和调试，您需要先安装[Python](https://www.python.org/downloads)。  
另外，本项目依赖于以下**外部库**，调试前请确保您已安装过：
* [UnityPy](https://github.com/K0lb3/UnityPy)
* [Pillow](https://github.com/python-pillow/Pillow)

好消息是，只要安装UnityPy就会附带地安装上Pillow，安装命令：
```
pip install unitypy -i https://mirrors.aliyun.com/pypi/simple
```

#### 原理
本项目的代码结构分为4个层次：
* 表现层（`Main.py`）
* 衔接层（`ResolveAB.py和CombineRGBwithA.py`中的`Main`函数）
* 操作层（`ResolveAB.py和CombineRGBwithA.py`中的其他函数）
* 辅助层（`colorTool.py、osTool.py、communalTool.py`）

当您运行了`Main.py`时表现层会负责显示出操作提示。在您向表现层输入指令后，表现层会调用衔接层来完成指令。衔接层负责批量地调用操作层函数，而操作层负责底层的文件处理。此外，前三个层都有调用辅助层的通用函数。

#### 示例
如果您不想使用我们的表现层的功能，只想利用衔接层甚至操作层中的代码，来实现一些您自定义的功能，您可以在您的程序中这样写：
```Python
from src import ResolveAB
from src import CombineRGBwithA
ResolveAB.main(['Android'], 'Unpacked') # (a)
CombineRGBwithA.main(['Unpacked'], 'Combined') # (b)
```

以上(a)(b)两个衔接层的函数还有其他可选的参数，具体的用法已在函数声明的代码注释中非常详尽地给出了，如下：
```Python
# File: src/ResolveAB.py
def main(rootdir:list, destdir:str, dodel:bool=False, 
    doimg:bool=True, dotxt:bool=True, doaud:bool=True, detail:bool=True):
    '''
    #### 批量地从指定目录的ab文件中，导出指定类型的资源
    :param rootdir: 包含来源文件夹们的路径的列表;
    :param destdir: 解包目的地的根目录的路径;
    :param dodel:   预先删除目的地文件夹的所有文件，默认False;
    :param doimg:   是否导出图片资源，默认True;
    :param dotxt:   是否导出文本资源，默认True;
    :param doaud:   是否导出音频资源，默认True;
    :param detail:  是否回显详细信息，默认True，否则回显进度条;
    :returns: (None);
    '''

# File: src/CombineRGBwithA.py
def main(rootdir:list, destdir:str, dodel:bool=False, detail:bool=True):
    '''
    #### 批量地从指定目录中，找到名称相互匹配的RGB通道图和A通道图，然后合并图片后保存到另一目录
    :param rootdir: 包含来源文件夹们的路径的列表;
    :param destdir: 解包目的地的根目录的路径;
    :param dodel:   预先删除目的地文件夹的所有文件，默认False;
    :param detail:  是否回显详细信息，默认True，否则回显进度条;
    :returns: (None);
    '''
```
=======
版本(Version)`v1.0`  

This project only supports Chinese docs. If you are an English user, feel free to contact us.

## 功能 <sub>Functions</sub>
此版本已实现的功能如下：
1. 批量解包UnityAB文件中的图片、文本、音频
2. 批量合并RGB通道图和A通道图
3. 提供命令行式的人性化界面实现(1)(2)的功能

## 使用方法 <sub>Usage</sub>

### 使用发行版本
此版本的程序没有发行版本，因为其部分功能存在兼容性问题，我们将在下一个版本修复后发布。

### 使用源代码

#### 依赖
源代码使用Python3编写，它依赖于以下外部库，调试前请确保您已使用`pip`安装过：
> UnityPy  
> PIL

本项目的主要功能依赖于以下程序文件：
> `src/ResolveAB.py` - 负责实现功能(1)  
> `src/CombineRGBwithA.py` - 负责实现功能(2)

以上程序文件需要以下程序文件的辅助：
> `src/osTool.py` - 提供一些便捷的文件操作函数  
> `src/colorTool.py` - 提供命令行彩色字体的打印

#### 示例
您可以直接运行`Main-v1.0.py`来完成功能(3)。如果您只想利用本项目的代码，来实现功能(1)或功能(2)，您可以在您的程序中这样写：
```Python
from src import ResolveAB
from src import CombineRGBwithA
ResolveAB.main(['目录1'], '目的地目录1') # ——①
CombineRGBwithA.main(['目录2','目录3'], '目的地目录2') # ——②
```
以上①②两个函数还有其他可选的参数，具体的用法已在代码注释中非常详尽地给出了，在此不再赘述。

## 许可证 <sub>License</sub>
本项目基于**BSD3协议**。任何人都可以自由地使用和修改项目内的源代码，前提是要在源代码或版权声明中保留作者说明和原有协议，且不可以使用本项目名称或作者名称进行宣传推广。

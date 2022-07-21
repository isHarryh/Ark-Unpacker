Ark-Unpacker
==========
A tool that can unpack Arknights AB assets automatically.  
明日方舟游戏资源批量解包器  
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

ArkUnpacker附加说明文档
# 开发者指引

如果您是高级用户或开发者，希望实现一些额外功能，以下内容可能会帮助到你：  

## 依赖
1. **Python：** 源代码使用**Python3**编写和调试，您需要先安装[Python](https://www.python.org/downloads)。  
2. **外部库：** 本项目依赖于以下**外部库**，调试前请确保您已安装过：
    * [UnityPy](https://github.com/K0lb3/UnityPy)
    * [Pillow](https://github.com/python-pillow/Pillow)

    本项目的完整依赖表如下：
    ```
    altgraph==0.17
    Brotli==1.0.9
    certifi==2021.5.30
    etcpak==0.9.6
    future==0.18.2
    lz4==4.0.0
    pefile==2021.5.24
    Pillow==8.4.0
    pyinstaller==4.5.1
    pyinstaller-hooks-contrib==2021.3
    pywin32==301
    pywin32-ctypes==0.2.0
    requests==2.26.0
    texture2ddecoder==1.0.4
    UnityPy==1.8.9
    ```
    通常情况下，只要安装UnityPy就会附带地安装上Pillow，安装命令：
    ```
    pip install unitypy -i https://mirrors.aliyun.com/pypi/simple
    ```

## 原理
本项目的代码结构分为3个层次：
* 命令行界面(CLI)层（`Main.py`）
* 操作层
* 辅助工具层

当您运行了`Main.py`时CLI层会负责显示出操作提示。在您向CLI层输入指令后，其会调用操作层来完成指令。

## 示例
如果您不想使用我们的CLI层的功能，只想利用操作层中的代码，来实现一些您自定义的功能，您可以在您的程序中这样写：
```Python
from src import ResolveAB
from src import CombineRGBwithA
ResolveAB.main('Android', 'Unpacked') # (a)
CombineRGBwithA.main('Unpacked', 'Combined') # (b)
```

以上(a)(b)两个衔接层的函数还有其他可选的参数，具体的用法已在函数声明的代码注释中非常详尽地给出了，如下：
```Python
# File: src/ResolveAB.py
def main(rootdir:str, destdir:str, dodel:bool=False, 
    doimg:bool=True, dotxt:bool=True, doaud:bool=True, dospine:bool=False, separate:bool=True, threads:int=8):
    '''
    #### 批量地从指定目录的ab文件中，导出指定类型的资源
    :param rootdir:   来源文件夹的根目录的路径;
    :param destdir:   解包目的地的根目录的路径;
    :param dodel:     预先删除目的地文件夹的所有文件，默认False;
    :param doimg:     是否导出图片资源，默认True;
    :param dotxt:     是否导出文本资源，默认True;
    :param doaud:     是否导出音频资源，默认True;
    :param onlyspine: 是否导出Spine动画，注意Spine动画和图片资源、文本资源有重叠的部分，默认False;
    :param separate:  是否按AB文件分类保存，默认True;
    :param threads:   最大线程数，默认8;
    :returns: (None);
    '''

# File: src/CombineRGBwithA.py
def main(rootdir:str, destdir:str, dodel:bool=False, threads:int=8):
    '''
    #### 批量地从指定目录中，找到名称相互匹配的RGB通道图和A通道图，然后合并图片后保存到另一目录
    :param rootdir: 来源文件夹的根目录的路径;
    :param destdir: 解包目的地的根目录的路径;
    :param dodel:   预先删除目的地文件夹的所有文件，默认False;
    :param threads: 最大线程数，默认8;
    :returns: (None);
    '''
```

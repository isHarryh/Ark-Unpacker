ArkUnpacker附加说明文档
# 开发者指引

如果您是高级用户或开发者，希望实现一些额外功能，以下内容可能会帮助到你： 

> **注意：**  
> 此文档可能有时效性限制，请以源程序内容为准。

## 依赖
1. **Python：** 源代码使用**Python3**编写和调试，您需要先安装[Python](https://www.python.org/downloads)。推荐的IDE是VS Code。
2. **外部库：** 本项目依赖于以下**外部库**，调试前请确保您已安装过：
    - [UnityPy](https://github.com/K0lb3/UnityPy)
    - [Pillow](https://github.com/python-pillow/Pillow)

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

## 结构
本程序通过交互式命令行界面(Interactive CLI)与用户进行交互。

本项目的代码可分为3个层次：
- 表现层（入口点 `Main.py`）
- 操作层（软件包 `src`）
- 工具层（软件包 `src.utils`）

## 示例
如果您不想使用我们的表现层的功能，只想利用操作层中的代码，来实现一些您自定义的功能，您可以这样做：
```Python
from src import ResolveAB
from src import CombineRGBwithA
ResolveAB.main('Android', 'Unpacked') # (a)
CombineRGBwithA.main('Unpacked', 'Combined') # (b)
```

以上(a)(b)两个方法还有其他可选的参数，具体的用法已在函数声明的代码注释中非常详尽地给出了，如下：
```Python
# File: src/ResolveAB.py
def main(rootdir:str, destdir:str, dodel:bool=False, 
    doimg:bool=True, dotxt:bool=True, doaud:bool=True, dospine:bool=False, separate:bool=True):
    """Extract all the AB files from the given directory.

    :param rootdir: Source directory;
    :param destdir: Destination directory;
    :param dodel: Whether to delete the existing files in the destination directory, `False` for default;
    :param doimg: Whether to extract images;
    :param dotxt: Whether to extract text scripts;
    :param doaud: Whether to extract audios;
    :param dospine: Whether to extract Spine assets, note that the Spine assets may have some identical file with the images/scripts;
    :param separate: Whether to sort the extracted files by their source AB file path.
    :rtype: None;
    """

# File: src/CombineRGBwithA.py
def main(rootdir:str, destdir:str, dodel:bool=False):
    """Combines the RGB images and the Alpha images in the given directory automatically according to their file names,
    then saves the combined images into another given directory.

    :param rootdir: Source directory;
    :param destdir: Destination directory;
    :param dodel: Whether to delete the existed destination directory first, `False` for default;
    :rtype: None;
    """
```

## 构建
关于软件的构建，请参阅[此文档](../build/README.md)。

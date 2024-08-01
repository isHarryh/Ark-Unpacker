ArkUnpacker附加说明文档
# 开发者指引

此文档描述了运行源程序或参与项目开发的准备工作和具体步骤。

## 依赖
1. **Python：** 本项目基于 **Python 3.8.10**，您可[前往下载](https://www.python.org/downloads)。
2. **IDE：** 建议使用的集成开发环境（IDE）是 **VS Code**，您可[前往下载](https://code.visualstudio.com)。
    > 建议使用的 VS Code 插件：
    > - [Code Spell Checker](https://marketplace.visualstudio.com/items?itemName=streetsidesoftware.code-spell-checker)
    > - [Python](https://marketplace.visualstudio.com/items?itemName=ms-python.python)
3. **Poetry：** 本项目使用 **Poetry** 进行依赖项的自动化管理，您可[查看教程](https://python-poetry.org/docs)。所有依赖项将被安装在 Poetry 的虚拟环境中。
    > Poetry 快速安装方法：
    > 1. 命令行运行 `pip install pipx` 安装 pipx 这一命令行程序管理工具；
    > 2. 命令行运行 `pipx install poetry` 安装 Poetry，并在命令行运行 `pipx ensurepath` 以完善 PATH 配置；
    > 3. 命令行运行 `poetry -v` 以检查是否安装成功（这可能需要在新的命令行窗口中运行）。
4. **子模块：** 本项目使用 [ArkFBSPy](https://github.com/isHarryh/Ark-FBS-Py) 模块来实现 FlatBuffers 的数据解码，该模块是以 Git Submodule 的形式存储在仓库中的。

## 项目初始化
1. 使用 Git 克隆仓库到本地，然后使用 IDE 打开项目文件夹。
    > 由于仓库使用了 Git Submodule，因此：  
    > - 在初始化仓库时，您需要运行 `git submodule update --init --recursive` 来初始化子模块。
    > - 当子模块的远程仓库有更新时，您需要运行 `git submodule update --remote --recursive` 来更新本地的子模块。
2. 在 VS Code 中启动 `Project Setup` 终端任务（通常情况下，每次打开项目都会自动运行这一任务）；或者命令行运行 `poetry install`。这将激活 Poetry 并在虚拟环境中安装依赖项。本项目的主要依赖项可在 `pyproject.toml` 文件中查看。
3. 选择 Python 解释器为 Poetry 虚拟环境中的解释器（命令行运行 `poetry env info` 即可查看解释器路径）。
4. 在 VS Code 中启动 `Python: ArkUnpacker` 运行，即可开始调试主程序。

## 测试与构建
1. **测试：** 在 VS Code 中启动 `Test` 终端任务；或者直接运行 `Test.py` 脚本。这将使用仓库自带的测试用的游戏资源文件（位于 `test/res` 目录中）进行模拟解包。测试完成后会生成运行用时的记录文件 `test/rt.json`。
2. **构建：** 在 VS Code 中启动 `Build Dist` 终端任务；或者直接运行 `Build.py` 脚本。这将使用 PyInstaller 在项目文件夹的 `build/dist` 目录中自动生成可分发的文件。

## 代码结构与用例
本程序可以通过交互式命令行界面（Interactive CLI）与用户进行交互，也可以直接使用命令行运行并执行任务。

本项目的代码可分为 3 个层次：
- 表现层（入口点 `Main.py`）
- 操作层（软件包 `src`）
- 工具层（软件包 `src.utils`）

如果您不想使用我们的表现层的功能，只想利用操作层中的代码，来实现一些您自定义的功能，您可以这样做：
```Python
from src import ResolveAB
from src import CombineRGBwithA
ResolveAB.main('Android', 'Unpacked') # (a)
CombineRGBwithA.main('Unpacked', 'Combined') # (b)
```

以上 (a) (b) 两个方法还有其他可选的参数，具体的用法已在函数声明的代码注释中非常详尽地给出了，请自行阅读。

关于直接使用命令行运行的详细介绍，请参阅 [README](../README.md#5命令行用法)。

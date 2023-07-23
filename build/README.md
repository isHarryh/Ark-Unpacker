ArkUnpacker构建指引
# 概述
此软件使用`pyinstaller`生成可执行文件，然后使用`Enigma Virtual Box`(简称EVB)进行封装打包。为避免无用库的污染导致文件过大，在生成时使用的是`venv`虚拟环境。

# 构建流程
使用预编写的构建脚本进行快速构建，并利用EVB打包的具体步骤如下：
1. 运行脚本`Build.py`，此时会创建`venv`虚拟环境文件夹并进行相关生成操作。
2. 上一步成功完成后，[下载安装](https://enigmaprotector.com/en/downloads.html)并打开EVB软件。
3. 在EVB窗口中，将`venv/dist/Main/Main.exe`设为输入路径，然后填写任意输出路径。
4. 在EVB窗口的 “File” 选项卡中，点击 “Add - New Root Folder” 添加`%DEFAULT FOLDER%`作为虚拟根目录。
5. 将`venv/dist/Main`目录下的所有文件拖入`%DEFAULT FOLDER%`。
6. 最后，点击 “Process”，即可生成最终的可执行文件。

> 提示：
> 1. 建议在EVB打包时启用压缩模式：在EVB窗口的 “File Options” 中，选中 “Compress Files” 即可。
> 2. 为便于下次EVB打包，可以将EVB项目保存为文件。

ArkUnpacker附加说明文档
# 关于ArkModels提取与分拣工具

## 功能概述
[ArkModels](https://github.com/isHarryh/Ark-Models)是作者建立的明日方舟Spine模型仓库，收录了游戏中的一部分Spine模型。“ArkModels提取与分拣工具” 用于辅助该仓库进行更新，其子功能包括：
- 模型提取：自动从游戏原始资源文件中，提取出ArkModels仓库可能需要的文件。
- 文件分拣：对提取出的文件进行进一步筛选，按照ArkModels仓库的相关格式要求进行命名与分类。
- 生成数据集：从第三方仓库[ArknightsGameData](https://github.com/Kengxxiao/ArknightsGameData)中联网获取一些辅助信息，然后将ArkModels仓库中的每个模型的信息写入一个JSON数据集中。

## 使用方法
1. 按照README文档中的说明，进行[资源准备](../README.md#1资源准备)。具体需要哪些资源，请参考[ArkModels](https://github.com/isHarryh/Ark-Models)仓库所需要收录的内容，和我们的[游戏资源查找指南](AssetsGuide.md)。请将准备的资源文件夹放在和程序**同一个**目录里面。
2. 打开程序，进入 “ArkModels提取与分拣工具” 界面，分别运行 “模型提取”，“文件分拣”，“生成数据集” 。之后，程序所在目录就会生成ArkModels仓库需要的文件(和文件夹)了。
3. 克隆ArkModels仓库，使用刚刚生成的文件(和文件夹)替换掉原来的内容，并进行Commit等操作更新仓库，即可完成模型的更新。整个流程非常简单。

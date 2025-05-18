ArkUnpacker附加说明文档
# 文本资源解码

## 概述

解包《明日方舟》AB 文件所导出的 TextAsset 类型的文件，主要有三种格式：

1. 纯文本文件，例如某些剧情文本；
2. 以 FlatBuffers 格式存储的文件；
3. 用 AES 加密的文件，例如。

其中，FlatBuffers 文件和 AES 加密文件都需要经过一定的解码步骤才能查看，直接打开是乱码的。为了解码，需要使用 ArkUnpacker 提供的“解码文本资源”功能。

在“解码文本数据”的功能中，您无需自行区分乱码的文件到底是 FlatBuffers 文件还是 ASE 加密的文件，因为 ArkUnpacker 会自动进行识别。

若您对解码这些数据的具体步骤感兴趣，并且您了解数据存储和密码学的基本常识，您可以继续阅读下面的原理介绍。

## FlatBuffers 文件的解码原理

FlatBuffers 是一种用于高效地存储数据的格式，您可前往 [FlatBuffers 官网](https://flatbuffers.dev)查看介绍。

为了将二进制的 FlatBuffers 文件转化为 JSON 等可读格式，除了需要原始二进制文件外，我们还需要 FlatBuffers Schema (FBS) 这一架构文件。

FBS 相当于一种抽象模板，它定义了哪些数据以怎样的类型被存储。如果没有 FBS，那么我们只能从原始二进制文件中读取到非结构性的孤立的值。

获得 FBS 的有效途径是对游戏内部数据结构进行解析。

ArkUnpacker 所使用的 FBS 根本上来自于 [OpenArknightsFBS](https://github.com/MooncellWiki/OpenArknightsFBS)。为了便于解析，程序中使用的 FBS 并不是原始的 FBS，而是编译到 Python 的 FBS 的类，即 [ArkFBSPy](https://github.com/isHarryh/Ark-FBS-Py)。

### 解码步骤

1. 通过原始二进制文件的名称，判断该文件采用的是哪个 FBS；
2. 使用该 FBS 对文件进行解码，得到结构性的数据；
3. 将解码后的数据保存为 JSON 格式。

## AES 加密文件的解码原理

AES 是一种常见的对称加密算法。

解码前，首先需要获得一个起到密钥作用的 32 字节的 CHAT_MASK。所有 AES 加密文件使用的 CHAT_MASK 都相同，但《明日方舟》各个大版本所使用的 CHAT_MASK 很可能会发生变更。

### 解码步骤

1. 对于较新版本《明日方舟》的二进制加密文件，其文件头部通常有 128 字节的 RSA 签名，在解密时需要跳过；
2. 通过某种途径取得 CHAT_MASK，CHAT_MASK 的首 16 字节是 AES 密钥；
3. 跳过签名块后，将首 16 字节数据与 CHAT_MASK 的后 16 字节进行异或，可以得到初始向量（IV）；
4. 利用上述步骤所得的 AES 密钥和 IV，对后面的数据进行 AES-CBC 解密；
5. 解密后的数据可能是 JSON 文件，也可能是 BSON 文件（需要转换为 JSON 文件）。

Additional Documentation for ArkUnpacker

# Text Resource Decoding

## Overview

TextAsset files exported from unpacked Arknights AB files mainly fall into three formats:

1. Plain text files (e.g., certain story scripts);  
2. Files stored in FlatBuffers format;  
3. AES-encrypted files.  

Among these, FlatBuffers files and AES-encrypted files require decoding before they can be read, as they will appear as garbled text if opened directly. To decode them, use the "Decode Text Resources" feature provided by ArkUnpacker.

Within the "Decode Text Data" feature, you do not need to manually distinguish whether a file is FlatBuffers or AES-encrypted, as ArkUnpacker will automatically detect the format.

If you are interested in the decoding process and have basic knowledge of data structures and cryptography, you can continue reading the sections below.

---

## FlatBuffers File Decoding

FlatBuffers is a format designed for efficient data storage. You can visit the [FlatBuffers official site](https://flatbuffers.dev) for more information.

To convert binary FlatBuffers files into readable formats such as JSON, you need both the original binary file and the FlatBuffers Schema (FBS).

The FBS acts as a structural template that defines how data is stored and typed. Without an FBS, you can only extract unstructured, isolated values from the binary data.

A reliable way to obtain FBS files is by analyzing the internal data structures of the game.

The FBS used by ArkUnpacker is primarily derived from [OpenArknightsFBS](https://github.com/MooncellWiki/OpenArknightsFBS). For ease of parsing, the program does not use raw FBS files directly, but instead uses compiled Python classes generated from FBS, provided by [ArkFBSPy](https://github.com/isHarryh/Ark-FBS-Py).

### Decoding Steps

1. Determine which FBS schema is used based on the name of the original binary file;  
2. Decode the file using the corresponding FBS to obtain structured data;  
3. Save the decoded data in JSON format.  

---

## AES Encrypted File Decoding

AES is a widely used symmetric encryption algorithm.

Before decoding, a 32-byte value called `CHAT_MASK` must be obtained, which acts as the encryption key. All AES-encrypted files use the same `CHAT_MASK`, but it may change between major versions of Arknights.

### Decoding Steps

1. For binary encrypted files in newer versions of Arknights, the file header usually contains a 128-byte RSA signature, which must be skipped during decryption;  
2. Obtain the `CHAT_MASK`, where the first 16 bytes serve as the AES key;  
3. After skipping the signature block, XOR the first 16 bytes of the data with the last 16 bytes of the `CHAT_MASK` to obtain the initialization vector (IV);  
4. Use the AES key and IV obtained above to perform AES-CBC decryption on the remaining data;  
5. The decrypted data may be in JSON or BSON format (BSON needs to be converted to JSON).  
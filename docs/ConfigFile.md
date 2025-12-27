ArkUnpacker附加说明文档
# 配置文件指引

## 概述

在运行程序后，工作目录会生成 ArkUnpacker 的配置文件，以 JSON 格式存储部分设置参数。文件名为 `ArkUnpackerConfig.json`。

> **注意：**  
> 1. 不同版本的 ArkUnpacker 配置文件可能不兼容。若因此导致程序故障，请删除原来的配置文件。
> 2. 修改或删除配置文件后，必须重新启动 ArkUnpacker 才能应用更改。

## 字段说明

配置文件内容示例如下，文件编码为 `UTF-8`：
```json
{
    "log_file": "ArkUnpackerLogs.log",
    "log_level": 3,
    "min_spare_memory_mb": 256,
    "performance_level": 2,
    "usm_encoding": "gbk",
    "usm_export_video_codec": "vp9",
    "usm_export_audio_codec": "libvorbis",
    "usm_export_video_ext": ".mkv",
    "usm_export_audio_ext": ".ogg",
    "export_encoding": "utf-8",
    "export_json_indent": 4
}
```

- `log_file`：字符串。日志文件的存储路径，设为 `""` 以禁用日志文件写入。
- `log_level`：整数。日志等级，`0=None` `1=Error` `2=Warn` `3=Info` `4=Debug`。
- `min_spare_memory_mb`：整数。多线程任务提交的可用内存下限，单位为 MB。当设备可用内存低于此值时，新的多线程任务将被阻滞直到内存充足。
- `performance_level`：整数。性能等级，数值越大则线程和性能消耗越多，`0=Minimal` `1=Low` `2=Standard` `3=High`。
- `usm_encoding`：字符串。读取 Criware USM 文件时采用的编码，常见的有 `utf-8` 和 `gbk`。
- `usm_export_video_codec`：字符串。在 Criware USM 提取模式下，使用的视频编码器。
- `usm_export_audio_codec`：字符串。在 Criware USM 提取模式下，使用的音频编码器。
- `usm_export_video_ext`：字符串。在 Criware USM 提取模式下，导出视频文件时使用的文件扩展名。
- `usm_export_audio_ext`：字符串。在 Criware USM 提取模式下，导出音频文件时使用的文件扩展名。
- `export_encoding`：字符串。导出文本格式文件时采用的文件编码。
- `export_json_indent`：整数。导出 JSON 文件时的缩进空格数。

> **提示：**  
> - 性能等级（`performance_level`）越高并不一定会使得效率越高。通常来说 Standard 是比较推荐的。
> - 若想要绕过多线程阻滞的限制，可以将 `min_spare_memory_mb` 设为 `0`。

Additional Documentation for ArkUnpacker

# Configuration File Guide

## Overview

After running the program, a configuration file for ArkUnpacker will be generated in the working directory. It stores certain settings in JSON format. The file name is `ArkUnpackerConfig.json`.

> **Note:**  
> 1. Configuration files from different versions of ArkUnpacker may not be compatible. If this causes issues, please delete the existing configuration file.  
> 2. After modifying or deleting the configuration file, you must restart ArkUnpacker for the changes to take effect.  

## Field Description

An example of the configuration file is shown below. The file encoding is `UTF-8`:

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

- `log_file`：string. Path to the log file. Set to `""` to disable log file writing.
- `log_level`：integer. Log level, `0=None` `1=Error` `2=Warn` `3=Info` `4=Debug`.
- `min_spare_memory_mb`：integer. Minimum available memory (in MB) required to submit multithreaded tasks. If available memory falls below this value, new tasks will be blocked until sufficient memory is available.
- `performance_level`：integer. Performance level. Higher values consume more threads and resources. `0=Minimal` `1=Low` `2=Standard` `3=High`.
- `usm_encoding`：string. Encoding used when reading Criware USM files (commonly `utf-8` or `gbk`).
- `usm_export_video_codec`：string. Video codec used in Criware USM extraction mode.
- `usm_export_audio_codec`：string. Audio codec used in Criware USM extraction mode.
- `usm_export_video_ext`：string. File extension used when exporting video files in Criware USM extraction mode.
- `usm_export_audio_ext`：string. File extension used when exporting audio files in Criware USM extraction mode.
- `export_encoding`：string. Encoding used when exporting text-based files.
- `export_json_indent`：integer. Number of spaces used for indentation when exporting JSON files.

> **Tip:**  
> - A higher `performance_level` does not necessarily result in better performance. In most cases, Standard is recommended.
> - To bypass multithreading blocking, you can set `min_spare_memory_mb` to `0`.
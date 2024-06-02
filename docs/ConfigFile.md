ArkUnpacker附加说明文档
# 配置文件指引

## 概述
在运行程序后，工作目录会生成 ArkUnpacker 的配置文件，以 JSON 格式存储部分设置参数。文件名为 `ArkUnpackerConfig.json`。

> **注意：**  
> 修改配置文件后，必须重新启动 ArkUnpacker 才能应用更改。

## 字段说明
配置文件内容示例如下，文件编码为 `UTF-8`：
```json
{
    "log_file": "ArkUnpackerLogs.log",
    "log_level": 3,
    "performance_level": 2,
    "ark_models_constants": {
        "src_prefix": "https://raw.githubusercontent.com/Kengxxiao/ArknightsGameData/master",
        "src_server": "zh_CN"
    }
}
```
- `log_file`：字符串。日志文件的存储路径，设为 `""` 以禁用日志文件写入。
- `log_level`：整数。日志等级，`0=None` `1=Error` `2=Warn` `3=Info` `4=Debug`。
- `performance_level`：整数。性能等级，数值越大性能消耗越多，`0=Minimal` `1=Low` `2=Standard` `3=High`。
- `ark_models_constants`: 字典对象。ArkModels提取与分拣工具所使用的相关常量。

ArkUnpacker附加说明文档
# 配置文件指引

## 概述
在运行程序后，工作目录会生成ArkUnpacker的配置文件，以JSON格式存储部分设置参数。文件名为`ArkUnpackerConfig.json`。

修改配置文件后，必须重新启动ArkUnpacker才能应用更改。

## 字段说明
配置文件内容示例如下：
```json
{
    "log_file": "ArkUnpackerLogs.log",
    "log_level": 3,
    "threads_limit": 48,
    "threads_default": 16,
    "ark_models_constants": {
        "src_prefix": "https://raw.githubusercontent.com/Kengxxiao/ArknightsGameData/master",
        "src_server": "zh_CN"
    }
}
```
- `log_file`：字符串。日志文件的存储路径，设为`""`以禁用日志文件写入。
- `log_level`：整数。日志等级，`0=None` `1=Error` `2=Warn` `3=Info` `4=Debug`。
- `threads_limit`：整数。允许用户设置的最大线程数。
- `threads_default`：整数。一键执行模式中默认的线程数。
- `ark_models_constants`: 字典对象。ArkModels提取与分拣工具所使用的相关常量。

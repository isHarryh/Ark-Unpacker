ArkUnpacker附加说明文档
# 配置文件指引

## 概述
在运行程序后，工作目录会生成ArkUnpacker的配置文件，以JSON格式存储部分设置参数。文件名为`ArkUnpackerConfig.json`。

## 字段说明
默认的配置文件内容如下：
```json
{
    "log_file": "ArkUnpackerLogs.log",
    "log_level": 3,
    "threads_limit": 32,
    "threads_default": 8
}
```
- `log_file`：字符串。日志文件的存储路径。
- `log_level`：整数。日志等级，`0=None` `1=Error` `2=Warn` `3=Info` `4=Debug`。
- `threads_limit`：整数。允许用户设置的最大线程数。
- `threads_default`：整数。一键执行模式中默认的线程数。

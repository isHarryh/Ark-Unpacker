# -*- coding: utf-8 -*-
# Copyright (c) 2022-2023, Harry Huang
# @ BSD 3-Clause License
import os, json
from .Logger import *

class Config():
    '''
    Configuration class for ArkUnpacker
    配置类
    '''

    __config_path = "ArkUnpackerConfig.json"
    __file_encoding = 'UTF-8'
    __default_config = {
        'log_file': "ArkUnpackerLogs.log",
        'log_level': Logger.LV_INFO,
        'threads_limit': 48,
        'threads_default': 16,
    }
    
    def __init__(self):
        '''
        ## Initialized the config system
        #### 初始化配置文件系统
        '''
        self.read_config()
        self.save_config()
    
    def get(self, key):
        '''
        ## Get the specified config field
        #### 获取指定的配置字段值
        :param key: The JSON key to the field;
        :returns:   (Any) None if the key doesn't exist;
        '''
        return self.config[key] if key in self.config.keys() else None
    
    def read_config(self):
        '''
        ## Read the config from file
        #### 读取（反序列化）配置文件
        Note: Default config will be used if the config file doesn't exist or an error occurs.
        :returns: (none);
        '''
        try:
            self.config = json.load(open(Config.__config_path, 'r', encoding=Config.__file_encoding)) if os.path.exists(Config.__config_path) else Config.__default_config
            Logger.set_instance(self.get('log_file'), self.get('log_level'))
            Logger.info(f"Succeeded in reading config.")
        except Exception as arg:
            self.config = Config.__default_config
            Logger.set_instance(self.get('log_file'), self.get('log_level'))
            Logger.error(f"Failed to read or initialize config: {arg}")
    
    def save_config(self):
        '''
        ## Save the config to file
        #### 保存（序列化）配置文件
        :returns: (none);
        '''
        try:
            json.dump(self.config, open(self.__config_path, 'w', encoding=Config.__file_encoding), indent=4, ensure_ascii=False)
            Logger.set_instance(self.get('log_file'), self.get('log_level'))
            Logger.info(f"Succeeded in saving config.")
        except Exception as arg:
            Logger.set_instance(self.get('log_file'), self.get('log_level'))
            Logger.error(f"Failed to save config: {arg}")

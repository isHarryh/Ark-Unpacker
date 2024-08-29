# -*- coding: utf-8 -*-
# Copyright (c) 2022-2024, Harry Huang
# @ BSD 3-Clause License
import re
import json
import shutil
import os
import os.path as osp
from datetime import datetime

from .ResolveAB import ab_resolve
from .DecodeTextAsset import ArkFBOLibrary
from .utils.GlobalMethods import color, print, get_dirlist, get_filelist
from .utils.Logger import Logger
from .utils.SaverUtils import SafeSaver

class PrefabError(Exception):
    def __init__(self, *args):
        super().__init__(*args)

class ModelsDist:
    SORT_TAGS_L10N = {
        # tag -> translation
        "DynIllust": "动态立绘",
        "Operator": "干员",
        "Skinned": "时装",
        "Special": "异格",
        "Enemy": "敌人",
        "EnemyNormal": "普通敌人",
        "EnemyElite": "精英敌人",
        "EnemyBoss": "领袖敌人",
        "Rarity_1": "一星",
        "Rarity_2": "二星",
        "Rarity_3": "三星",
        "Rarity_4": "四星",
        "Rarity_5": "五星",
        "Rarity_6": "六星",
    }
    ARK_PETS_COMPATIBILITY = [2, 2, 0]
    SERVER_REGION = 'zh_CN'
    MODELS_DIR = {
        # type -> dirname
        "Operator": "models",
        "Enemy": "models_enemies",
        "DynIllust": "models_illust",
    }
    GAMEDATA_DIR = 'gamedata'
    TEMP_DIR = 'temp/mdd'

    def __init__(self):
        shutil.rmtree(ModelsDist.TEMP_DIR, ignore_errors=True)
        self.data = {
            "storageDirectory": ModelsDist.MODELS_DIR,
            "sortTags": ModelsDist.SORT_TAGS_L10N,
            "gameDataVersionDescription": f"Producer: ArkUnpacker 3\nDate: {datetime.now().date()}\n",
            "gameDataServerRegion": ModelsDist.SERVER_REGION,
            "data": {},
            "arkPetsCompatibility": ModelsDist.ARK_PETS_COMPATIBILITY
        }

    def get_gamedata(self, alias:tuple):
        def basename_startswith(path:str, alias:tuple):
            for a in alias:
                if osp.basename(path).startswith(a):
                    return True
            return False
        for i in get_filelist(ModelsDist.GAMEDATA_DIR):
            if basename_startswith(i, alias):
                ab_resolve(i, ModelsDist.TEMP_DIR, False, True, False, False, None, None)
                while not SafeSaver.get_instance().completed():
                    pass
                for j in get_filelist(ModelsDist.TEMP_DIR):
                    if basename_startswith(j, alias):
                        return ArkFBOLibrary.decode(j)
                raise RuntimeError(f"Failed to get decoded data: {alias}")
        raise FileNotFoundError(f"Failed to find raw AB file: {alias}")

    def get_item_data(self, asset_id:str, type:str, style:str, sort_tags:list, name:str, appellation:str, sg_id:str, sg_name:str):
        return {
            "assetId": asset_id,
            "type": type,
            "style": style,
            "name": name,
            "appellation": appellation,
            "skinGroupId": sg_id,
            "skinGroupName": sg_name,
            "sortTags": sort_tags,
        }

    def get_operator_sort_tags(self, item:dict):
        rst = ["Operator"]
        if item.get('IsSpChar', False):
            rst.append("Special")
        try:
            if item.get('Rarity', None) is not None:
                rarity = f"Rarity_{int(item['Rarity']) + 1}"
                if rarity in self.data['sortTags']:
                    rst.append(rarity)
        except BaseException:
            Logger.warn("ModelsDataDist: Failed to recognize rarity tag.")
        return rst

    def get_enemy_sort_tags(self, item:dict):
        rst = ['Enemy']
        additional = {
            0: "EnemyNormal",
            1: "EnemyElite",
            2: "EnemyBoss"
        }.get(item['LevelType']['MValue'], None)
        return rst + [additional] if additional else rst

    def update_operator_data(self):
        Logger.info("ModelsDataDist: Decoding operator data.")
        print("解析干员信息...")
        raw:"dict[str,dict]" = self.get_gamedata(('character_table',))
        Logger.info("ModelsDataDist: Parsing operator data.")
        collected = {}
        for k, v in raw['Characters'].items():
            if k.startswith('char_') and not v.get('IsNotObtainable', None):
                key_char = k.lower()[5:]
                collected[key_char] = self.get_item_data(f'build_char_{key_char}', 'Operator', 'BuildingDefault', self.get_operator_sort_tags(v),
                        v['Name'], v['Appellation'], 'DEFAULT', '默认服装')
        self.data['data'].update(collected)
        Logger.info(f"ModelsDataDist: Found {len(collected)} operators.")
        print(f"\t找到 {len(collected)} 位干员", c=2)

    def update_skin_data(self):
        Logger.info("ModelsDataDist: Decoding skin data.")
        print("解析干员皮肤信息...")
        raw:"dict[str,dict]" = self.get_gamedata(('skin_table',))
        Logger.info("ModelsDataDist: Parsing skin data.")
        collected = {}
        for k, v in raw['CharSkins'].items():
            if v.get('BuildingId', None):
                key_char = v['CharId'][5:].lower()
                if key_char in self.data['data']:
                    origin = self.data['data'][key_char]
                    key_skin = v['BuildingId'][5:].lower()
                    if key_skin not in self.data['data']:
                        sort_tags = origin['sortTags'] + ['Skinned']
                        collected[key_skin] = self.get_item_data(f"build_char_{key_skin}", "Operator", "BuildingSkin", sort_tags,
                                origin['name'], origin['appellation'], v['DisplaySkin']['SkinGroupId'], v['DisplaySkin']['SkinGroupName'])
                    else:
                        Logger.info(f"ModelsDataDist: The skin-key of the skin \"{k}\" collided with an existed one.")
                else:
                    Logger.warn(f"ModelsDataDist: The operator-key of the skin \"{k}\" not found.")
                    print(f"\t皮肤 {k} 找不到对应的干员Key", c=3)
        self.data['data'].update(collected)
        Logger.info(f"ModelsDataDist: Found {len(collected)} skins.")
        print(f"\t找到 {len(collected)} 件干员皮肤", c=2)

    def update_enemy_data(self):
        Logger.info("ModelsDataDist: Decoding enemy data.")
        print("解析敌方单位信息...")
        raw:"dict[str,list]" = self.get_gamedata(('enemydata', 'enemy_database'))
        Logger.info("ModelsDataDist: Parsing enemy data.")
        collected = {}
        for k, v in raw['Enemies'].items():
            if k.startswith('enemy_'):
                key_enemy = k.lower()[6:]
                tags = self.get_enemy_sort_tags(v[0]['EnemyData'])
                collected[key_enemy] = self.get_item_data(f"enemy_{key_enemy}", "Enemy", None, tags,
                        v[0]['EnemyData']['Name']['MValue'], None, tags[-1], self.data['sortTags'][tags[-1]])
        self.data['data'].update(collected)
        Logger.info(f"ModelsDataDist: Found {len(collected)} enemies.")
        print(f"\t找到 {len(collected)} 个敌方单位", c=2)

    def update_dynillust_data(self):
        Logger.info("ModelsDataDist: Parsing dynillust data.")
        print("分析动态立绘信息...")
        collected = {}
        if osp.isdir(self.data['storageDirectory']['DynIllust']):
            for i in get_dirlist(self.data['storageDirectory']['DynIllust'], max_depth=1):
                #(i是每个动态立绘的文件夹)
                base = osp.basename(i)
                if base.startswith('dyn_'):
                    key = base.lower()
                    key_char = re.findall(r'[0-9]+.+', key)
                    if len(key_char) > 0:
                        key_char = key_char[0] #该动态立绘对应的原干员的key
                        if key_char in self.data['data']:
                            origin = self.data['data'][key_char]
                            sort_tags = origin['sortTags'] + ['DynIllust']
                            collected[key] = self.get_item_data(key, "DynIllust", None, sort_tags,
                                    origin['name'], origin['appellation'], origin['skinGroupId'], origin['skinGroupName'])
                        else:
                            Logger.warn(f"ModelsDataDist: The operator-key of the dyn illust \"{key}\" not found.")
                            print(f"\t动态立绘 {key} 找不到对应的干员Key", c=3)
                    else:
                        Logger.warn(f"ModelsDataDist: The operator-key of the dyn illust \"{key}\" could not pass the regular expression check.")
                        print(f"\t动态立绘 {key} 未成功通过正则匹配", c=3)
        else:
            Logger.warn("ModelsDataDist: The directory of dyn illust not found.")
            print("\t动态立绘根文件夹未找到", c=3)
        self.data['data'].update(collected)
        Logger.info(f"ModelsDataDist: Found {len(collected)} dynillusts.")
        print(f"\t找到 {len(collected)} 套动态立绘", c=2)

    def verify_models(self):
        Logger.info("ModelsDataDist: Validating models files.")
        print("校验模型文件...")
        cur_done = 0
        cur_fail = 0
        total = len(self.data['data'])
        for k, v in self.data['data'].items():
            #(i是Key,Key应为文件夹的名称)
            fail_flag = False
            asset_list = {}
            if v['type'] in self.data['storageDirectory']:
                #如果其type在模型存放目录预设中有对应值
                d = osp.join(self.data['storageDirectory'][v['type']], k)
                asset_list_pending = {}
                if osp.isdir(d):
                    #如果预期的目录存在
                    file_list = os.listdir(d)
                    for j in ('.atlas', '.png', '.skel'):
                        #(j是资源文件扩展名)
                        asset_list_specified = list(filter(lambda x:x.lower().endswith(j), file_list))
                        if len(asset_list_specified) == 0:
                            Logger.info(f"ModelsDataDist: The {j} asset of \"{k}\" not found, see in \"{d}\".")
                            print(f"[{color(3)}{k}{color(7)}] {v['name']}（{v['type']}）：{color(1)}{j}{color(7)} 文件缺失")
                            fail_flag = True
                            break
                        elif len(asset_list_specified) == 1:
                            asset_list_pending[j] = asset_list_specified[0]
                        else:
                            Logger.debug(f"ModelsDataDist: The {j} asset of \"{k}\" is multiple, see in \"{d}\".")
                            asset_list_specified.sort()
                            asset_list_pending[j] = asset_list_specified
                    if not fail_flag:
                        asset_list = asset_list_pending
                    else:
                        cur_fail += 1
                else:
                    Logger.info(f"ModelsDataDist: The model directory of \"{k}\" not found, expected path \"{d}\".")
                    print(f"[{color(3)}{k}{color(7)}] {v['name']}（{v['type']}）：模型不存在")
                    cur_fail += 1
            else:
                Logger.info(f"ModelsDataDist: The model asset of \"{k}\" is the type of \"{v['type']}\" which is not declared in the prefab.")
                print(f"[{color(3)}{k}{color(7)}] {v['name']}（{v['type']}）：未在脚本预设中找到其类型的存储目录")
                cur_fail += 1
            self.data['data'][k]['assetList'] = asset_list
            cur_done += 1
            if cur_done % 100 == 0:
                print(f"\t已处理完成 {color(2)}{round(cur_done / total * 100)}%{color(7)}")
        Logger.info(f"ModelsDataDist: Verify models completed, {cur_done - cur_fail} success, {cur_fail} failure.")
        print(f"\n\t校验完成：{color(2)}成功{cur_done - cur_fail}{color(7)}，失败{cur_fail}")

    def export_json(self):
        Logger.info("ModelsDataDist: Writing to json.")
        with open('models_data.json', 'w', encoding='UTF-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)
        Logger.info("ModelsDataDist: Succeeded in writing to json.")

########## Main-主程序 ##########
def main():
    md = ModelsDist()
    md.update_operator_data()
    md.update_skin_data()
    md.update_enemy_data()
    md.update_dynillust_data()
    md.verify_models()
    md.export_json()

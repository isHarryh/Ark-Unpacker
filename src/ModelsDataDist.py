# -*- coding: utf-8 -*-
# Copyright (c) 2022-2023, Harry Huang
# @ BSD 3-Clause License
import os.path, requests, json, warnings, re
try:
    from .utils._ImportAllUtils import *
except:
    from utils._ImportAllUtils import*
'''
生成ArkModels仓库使用的JSON数据集
'''


def get_curl(url:str):
    headers = {}
    try:
        Logger.info(f"ModelsDataDist: Fetching \"{url}\"")
        r = requests.get(url, headers=headers, verify=False)
        if r.status_code == 200:
            r.encoding = "UTF-8"
            Logger.debug(f"ModelsDataDist: Fetching was success, content length: {len(r.content)} Bytes.")
            return r.text
        else:
            Logger.error(f"ModelsDataDist: Failed to fetch \"{url}\": Responce code {r.status_code}")
            print(f"\t下载数据错误，返回码：{r.status_code}", c=3)
    except BaseException as arg:
        Logger.error(f"ModelsDataDist: Failed to fetch \"{url}\": {arg}")
        print(f"\t下载数据错误：{arg}", c=3)
        print(f"请尝试开启/关闭代理，或编辑配置文件更改数据源。")
    return False

def get_json(url:str):
    j = get_curl(url)
    if not j:
        return False
    try:
        j = json.loads(j)
        return j
    except BaseException as arg:
        Logger.error(f"ModelsDataDist: Failed to convert into JSON: Exception{type(arg)} {arg}")
        print(f"\t转化为JSON错误：{arg}")
    return False

def judge_result(rst:str):
    if rst:
        print("\t完成", c=2)
        return rst
    else:
        print("\t失败", c=3)
        return False
        
def get_item_data(assetId:str, type:str, style:str, sortTags:list, name:str, appellation:str, SGId:str, SGName:str):
    return {
        "assetId": assetId.lower(), #文件名字目前应该全是小写
        "type": type,
        "style": style,
        "name": name,
        "appellation": appellation,
        "skinGroupId": SGId,
        "skinGroupName": SGName,
        "sortTags": sortTags,
    }

def get_oper_sort_tags(item:dict, sort_tags_l10n:list):
    rst = ["Operator"]
    if 'isSpChar' in item.keys() and item['isSpChar']:
        rst.append("Special")
    try:
        rarity_prefix = "TIER_"
        if 'rarity' in item.keys() and item['rarity'] :
            if rarity_prefix in item['rarity']:
                rarity = f"Rarity_{int(item['rarity'][len(rarity_prefix)])}"
                if rarity in sort_tags_l10n:
                    rst.append(rarity)
    except:
        pass
    return rst

def get_enemy_sort_tags(item:dict):
    def get_enemy_type(num):
        if num == "NORMAL":
            return "EnemyNormal"
        if num == "ELITE":
            return "EnemyElite"
        if num == "BOSS":
            return "EnemyBoss"
        return "Enemy"
    rst = ["Enemy"]
    rst.append(get_enemy_type(item["levelType"]["m_value"]))
    return rst


########## Main-主程序 ##########
def main():
    ##### 读取预设↓ #####
    config = Config()
    arkPetsCompatibility = [2, 2, 0]
    models_dir = { #模型存放目录（类型=>目录名）
                "Operator": "models",
                "Enemy": "models_enemies",
                "DynIllust": "models_illust",
            }
    sort_tags_l10n =  { #筛选标签本地化（标签=>描述）
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
    const = config.get('ark_models_constants')
    if type(const) == dict:
        try:
            src_prefix = str(const['src_prefix'])
            src_server = str(const['src_server'])
        except KeyError as arg:
            Logger.error(f"ModelsDataDist: Prefab key {arg} not found.")
            print(f"部分预设字段缺失，请检查配置文件", c=3)
            print("可以删除配置文件并重启程序来尝试恢复默认配置")
            return False
        except Exception as arg:
            Logger.error(f'ModelsDataDist: Error occurred while reading prefabs: Exception{type(arg)} {arg}')
            print(f"读取预设字段失败，请检查配置文件", c=3)
            print("可以删除配置文件并重启程序来尝试恢复默认配置")
            return False
    else:
        Logger.error(f"ModelsDataDist: Prefabs not found.")
        print(f"预设字段缺失，请检查配置文件", c=3)
        print("可以删除配置文件并重启程序来尝试恢复默认配置")
        return False

    src_operdata = f"{src_prefix}/{src_server}/gamedata/excel/character_table.json"
    src_skindata = f"{src_prefix}/{src_server}/gamedata/excel/skin_table.json"
    src_enemydata = f"{src_prefix}/{src_server}/gamedata/levels/enemydata/enemy_database.json"
    src_verdata = f"{src_prefix}/{src_server}/gamedata/excel/data_version.txt"
    asset_ext = [".atlas", ".png", ".skel"]

    ##### 主程序↓ #####
    warnings.filterwarnings("ignore")
    print("查询数据源修订版本...")
    src_version = judge_result(get_curl(src_verdata))
    if not src_version:
        return

    print("获取干员数据...")
    datas = judge_result(get_json(src_operdata))
    if not datas:
        return
    print("解析干员信息...")
    collection = {}
    for i in datas.keys():
        if len(i) > 5 and i[:5] == "char_":
            key = i[5:].lower() #文件夹名字目前应该全是小写
            item = datas[i]
            if not item["isNotObtainable"]: #跳过不可获得的干员
                collection[key] = get_item_data("build_" + i, "Operator", "BuildingDefault", get_oper_sort_tags(item, sort_tags_l10n),
                        item["name"], item["appellation"], "DEFAULT", "默认服装")
    Logger.debug(f"ModelsDataDist: Found {len(collection)} operators.")
    print(f"\t找到 {len(collection)} 位干员", c=2)

    print("获取干员皮肤信息...")
    datas = judge_result(get_json(src_skindata)["charSkins"])
    if not datas:
        return
    print("解析干员皮肤信息...")
    addition = {}
    for i in datas.keys():
        if datas[i]["buildingId"] != None:
            key_char = datas[i]["charId"][5:] #原干员的key
            if key_char in collection.keys():
                origin = collection[key_char]
                key = datas[i]["buildingId"][5:].lower() #文件夹名字目前应该全是小写
                sort_tags = origin['sortTags'][:]
                sort_tags.append("Skinned")
                item = datas[i]
                addition[key] = get_item_data("build_" + item["buildingId"], "Operator", "BuildingSkin", sort_tags,
                        collection[item["charId"][5:]]["name"], collection[item["charId"][5:]]["appellation"], item["displaySkin"]["skinGroupId"], item["displaySkin"]["skinGroupName"])
            else:
                Logger.info(f"ModelsDataDist: The operator-key of the skin \"{datas[i]['charId']}\" not found.")
                print(f"\t皮肤 {datas[i]['charId']} 找不到对应的干员Key")
    collection.update(addition)
    Logger.debug(f"ModelsDataDist: Found {len(addition)} skins.")
    print(f"\t找到 {len(addition)} 个皮肤", c=2)

    print("获取敌人信息...")
    datas = judge_result(get_json(src_enemydata)["enemies"])
    if not datas:
        return
    print("解析敌人信息...")
    addition = {}
    for i in range(len(datas)):
        if datas[i]["Key"] != None and datas[i]["Value"][0] != None and "enemy_" in datas[i]["Key"]:
            key = datas[i]["Key"].lower()[6:] #文件夹名字目前应该全是小写
            item = datas[i]["Value"][0]["enemyData"]
            tags = get_enemy_sort_tags(item)
            addition[key] = get_item_data("enemy_" + key, "Enemy", None, tags,
                    item["name"]["m_value"], None, tags[-1], sort_tags_l10n[tags[-1]])
    collection.update(addition)
    Logger.debug(f"ModelsDataDist: Found {len(addition)} enemies.")
    print(f"\t找到 {len(addition)} 个敌人", c=2)

    print("解析动态立绘信息...")
    addition = {}
    if os.path.isdir(models_dir['DynIllust']):
        for i in get_filelist(models_dir['DynIllust'], max_depth=1, only_dirs=True):
            #(i是每个动态立绘的文件夹)
            base = os.path.basename(i)
            if len(base) > 4 and base[:4] == 'dyn_':
                key = base.lower()
                key_char = re.findall(r'[0-9]+.+', key)
                if len(key_char) > 0:
                    key_char = key_char[0] #该动态立绘对应的原干员的key
                    if key_char in collection.keys():
                        origin = collection[key_char]
                        sort_tags = origin['sortTags'][:]
                        sort_tags.append("DynIllust")
                        addition[key] = get_item_data(key, 'DynIllust', None, sort_tags, origin['name'], origin['appellation'], origin['skinGroupId'], origin['skinGroupName'])
                    else:
                        Logger.info(f"ModelsDataDist: The operator-key of the dyn illust \"{key}\" not found.")
                        print(f"\t动态立绘 {key} 找不到对应的干员Key")
                else:
                    Logger.info(f"ModelsDataDist: The operator-key of the dyn illust \"{key}\" could not pass the regular expression check.")
                    print(f"\t动态立绘 {key} 未成功通过正则匹配")
    else:
        Logger.warn(f"ModelsDataDist: The directory of dyn illust not found.")
        print("\t动态立绘根文件夹未找到", c=3)
    collection.update(addition)
    Logger.debug(f"ModelsDataDist: Found {len(addition)} dyn illust.")
    print(f"\t找到 {len(addition)} 个动态立绘", c=2)

    print("校验模型文件...")
    checksum_total = 0
    checksum_fail = 0
    for i in collection.keys():
        #(i是Key,Key应为文件夹的名称)
        fail_flag = False
        asset_list = {}
        if collection[i]["type"] in models_dir.keys():
            #如果其type在模型存放目录预设中有对应值
            dir = os.path.join(models_dir[collection[i]["type"]], i)
            asset_list_pending = {}
            if os.path.isdir(dir):
                #如果预期的目录存在
                file_list = os.listdir(dir)
                for j in asset_ext:
                    #(j是资源文件扩展名)
                    asset_list_specified = list(filter(lambda x:os.path.splitext(x)[1].lower() == j, file_list))
                    if len(asset_list_specified) == 0:
                        Logger.info(f"ModelsDataDist: The {j} asset of \"{i}\" not found, see in \"{dir}\".")
                        print(f"[{i}] {collection[i]['name']}（{collection[i]['type']}）：{j} 文件缺失")
                        fail_flag = True
                        break
                    elif len(asset_list_specified) == 1:
                        asset_list_pending[j] = asset_list_specified[0]
                    else:
                        Logger.info(f"ModelsDataDist: The {j} asset of \"{i}\" is multiple, see in \"{dir}\".")
                        asset_list_specified.sort()
                        asset_list_pending[j] = asset_list_specified
                if not fail_flag:
                    asset_list = asset_list_pending
                else:
                    checksum_fail += 1
            else:
                Logger.info(f"ModelsDataDist: The model directory of \"{i}\" not found, expected path \"{dir}\".")
                print(f"[{i}] {collection[i]['name']}（{collection[i]['type']}）：模型不存在")
                checksum_fail += 1
        else:
            Logger.info(f"ModelsDataDist: The model asset of \"{i}\" is the type of \"{collection[i]['type']}\" which is not declared in the prefab.")
            print(f"[{i}] {collection[i]['name']}（{collection[i]['type']}）：未在脚本预设中找到其类型的存储目录")
            checksum_fail += 1
        collection[i]["assetList"] = asset_list
        checksum_total += 1
    print(f"\n\t校验完成：{color(2)}成功{checksum_total - checksum_fail}{color(7)}，失败{checksum_fail}")

    print("保存为数据集文件...")
    collection = {
        "storageDirectory": models_dir,
        "sortTags": sort_tags_l10n,
        "gameDataVersionDescription": src_version,
        "gameDataServerRegion": src_server,
        "data": collection,
        "arkPetsCompatibility": arkPetsCompatibility
    }
    Logger.debug("ModelsDataDist: Writing...")
    with open("models_data.json", "w", encoding="UTF-8") as f:
        json.dump(collection, f, indent=4, ensure_ascii=False)
    Logger.info("ModelsDataDist: Succeeded.")
    print("\t完成", c=2)
    return True

if __name__ == '__main__':
    main()
    input("按Enter退出...")

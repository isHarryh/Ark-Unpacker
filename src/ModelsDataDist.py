# -*- coding: utf-8 -*-
# Copyright (c) 2022-2023, Harry Huang
# @ BSD 3-Clause License
import os.path, requests, json, warnings, hashlib
try:
    from communalTool import *
except:
    from .communalTool import *
'''
生成ArkModels仓库使用的JSON数据集
'''


def get_curl(url):
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
            print(f"\t下载数据错误，返回码：{r.status_code}")
    except BaseException as arg:
        Logger.error(f"ModelsDataDist: Failed to fetch \"{url}\": {arg}")
        print(f"\t下载数据错误：{arg}")
    return False

def get_json(url):
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

def judge_result(rst):
    if rst:
        print("\t完成")
        return rst
    else:
        print("\t失败")
        return False
        
def get_item_data(assetId, type, style, sortTags, name, appellation, SGId, SGName):
    return {
        "assetId": assetId.lower(), #文件名字目前应该全是小写
        "type": type,
        "style": style,
        "name": name,
        "sortTags": sortTags,
        "appellation": appellation,
        "skinGroupId": SGId,
        "skinGroupName": SGName
    }

def get_oper_sort_tags(data, isSkin = False):
    rst = ["Operator"]
    if isSkin:
        rst.append("Skinned")
    return rst

def get_enemy_sort_tags(data):
    def get_enemy_type(num):
        if num == "NORMAL":
            return "EnemyNormal"
        if num == "ELITE":
            return "EnemyElite"
        if num == "BOSS":
            return "EnemyBoss"
        return "Enemy"
    rst = ["Enemy"]
    rst.append(get_enemy_type(data["levelType"]["m_value"]))
    return rst


########## Main-主程序 ##########
def main():
    ##### 预设↓ #####
    arkPetsCompatibility = [2, 0, 0] #ArkPets最低兼容版本
    src_prefix = "https://raw.githubusercontent.com/Kengxxiao/ArknightsGameData/master" #资源地址前缀
    src_server = "zh_CN" #游戏服务器地区（例如zh_CN）
    models_dir = { #模型存放目录（类型=>目录名）
        "Operator": "models",
        "Enemy": "models_enemies",
    }
    sort_tags_l10n = { #筛选标签本地化（标签=>描述）
        "Operator": "干员",
        "Skinned": "时装",
        "Enemy": "敌人",
        "EnemyNormal": "普通敌人",
        "EnemyElite": "精英敌人",
        "EnemyBoss": "领袖敌人"
    }
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
    d = judge_result(get_json(src_operdata))
    if not d:
        return
    print("解析干员信息...")
    collection = {}
    for i in d.keys():
        if len(i) > 5 and i[:5] == "char_":
            key = i[5:].lower() #文件夹名字目前应该全是小写
            item = d[i]
            collection[key] = get_item_data("build_" + i, "Operator", "BuildingDefault", get_oper_sort_tags(item, False),
                    item["name"], item["appellation"], "ILLUST", "默认服装")
    Logger.debug(f"ModelsDataDist: Found {len(collection)} operators.")
    print(f"\t找到 {len(collection)} 位干员")

    print("获取干员皮肤信息...")
    d = judge_result(get_json(src_skindata)["charSkins"])
    if not d:
        return
    print("解析干员皮肤信息...")
    addition = {}
    for i in d.keys():
        if d[i]["buildingId"] != None:
            if d[i]["charId"][5:] in collection.keys():
                key = d[i]["buildingId"][5:].lower() #文件夹名字目前应该全是小写
                item = d[i]
                addition[key] = get_item_data("build_" + item["buildingId"], "Operator", "BuildingSkin", get_oper_sort_tags(item, True),
                        collection[item["charId"][5:]]["name"], collection[item["charId"][5:]]["appellation"], item["displaySkin"]["skinGroupId"], item["displaySkin"]["skinGroupName"])
            else:
                Logger.info(f"ModelsDataDist: The operator-key of the skin \"{d[i]['charId']}\" not found.")
                print(f"\t皮肤 {d[i]['charId']} 找不到对应的干员Key")
    collection.update(addition)
    Logger.debug(f"ModelsDataDist: Found {len(addition)} skins.")
    print(f"\t找到 {len(addition)} 个皮肤")

    print("获取敌人信息...")
    d = judge_result(get_json(src_enemydata)["enemies"])
    if not d:
        return
    print("解析敌人信息...")
    addition = {}
    for i in range(len(d)):
        if d[i]["Key"] != None and d[i]["Value"][0] != None and "enemy_" in d[i]["Key"]:
            key = d[i]["Key"].lower()[6:] #文件夹名字目前应该全是小写
            item = d[i]["Value"][0]["enemyData"]
            tags = get_enemy_sort_tags(item)
            addition[key] = get_item_data("enemy_" + key, "Enemy", None, tags,
                    item["name"]["m_value"], None, tags[-1], sort_tags_l10n[tags[-1]])
    collection.update(addition)
    Logger.debug(f"ModelsDataDist: Found {len(addition)} enemies.")
    print(f"\t找到 {len(addition)} 个敌人")

    print("校验模型文件...")
    checksum_total = 0
    checksum_fail = 0
    for i in collection.keys():
        #(i是Key,Key应为文件夹的名称)
        if collection[i]["type"] in models_dir.keys():
            #如果其type在模型存放目录预设中有对应值
            checksum = {}
            for j in asset_ext:
                #(j是资源文件后缀名,遍历该模型的所有资源文件)
                p = os.path.join(models_dir[collection[i]["type"]], i, collection[i]["assetId"] + j)
                if os.path.exists(p):
                    #文件存在时计算md5摘要
                    try:
                        with open(p, "rb") as f:
                            b = f.read()
                            md5 = hashlib.md5(b).hexdigest()
                            checksum[j] = md5
                    except BaseException as arg:
                        Logger.warn(f"ModelsDataDist: Failed to get the checksum of {p}: {arg}")
                        print(f"\t[{i}] {collection[i]['name']} 计算文件摘要时错误：{p}，原因：{arg}")
                        checksum = None
                        checksum_fail += 1
                        break
                else:
                    #特殊处理：有些干员基建模型没有build_前缀
                    newId = collection[i]["assetId"].replace("build_","",1)
                    p = os.path.join(models_dir[collection[i]["type"]], i, newId + j)
                    if os.path.exists(p):
                        try:
                            with open(p, "rb") as f:
                                b = f.read()
                                md5 = hashlib.md5(b).hexdigest()
                                checksum[j] = md5
                                collection[i]["assetId"] = newId
                        except BaseException as arg:
                            Logger.warn(f"ModelsDataDist: Failed to get the checksum of {p}: {arg}")
                            print(f"\t[{i}] {collection[i]['name']} 计算文件摘要时错误：{p}，原因：{arg}")
                            checksum = None
                            checksum_fail += 1
                            break
                    else:
                        Logger.info(f"ModelsDataDist: The model asset of \"{i}\" not found.")
                        print(f"\t[{i}] {collection[i]['name']} 未找到其文件")
                        checksum = None
                        checksum_fail += 1
                        break
            collection[i]["checksum"] = checksum
            checksum_total += 1
        else:
            Logger.info(f"ModelsDataDist: The model asset of \"{i}\" is the type of \"{collection[i]['type']}\" which is not declared in the prefab.")
            print(f"[{i}] {collection[i]['name']} 是{collection[i]['type']}类型的，但未在脚本预设中找到该类型的存储目录")
            checksum_fail += 1
    print(f"\n\t校验完成：成功{checksum_total - checksum_fail}，失败{checksum_fail}")

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
    print("\t完成")
    return True

if __name__ == '__main__':
    main()
    input("按Enter退出...")

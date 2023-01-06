# -*- coding: utf-8 -*-
# Copyright (c) 2022-2023, Harry Huang
# @ BSD 3-Clause License
import os.path, requests, json, warnings, hashlib
'''
生成ArkModels仓库使用的JSON数据集
'''


def get_curl(url):
    headers = {}
    try:
        r = requests.get(url, headers=headers, verify=False)
        if r.status_code == 200:
            r.encoding = "UTF-8"
            return r.text
        else:
            print(f"\t下载数据错误，返回码：{r.status_code}")
    except Exception as arg:
        print(f"\t下载数据错误：{arg}")
    return False
def get_json(url):
    j = get_curl(url)
    if not j:
        return False
    try:
        j = json.loads(j)
        return j
    except Exception as arg:
        print(f"\t转化为JSON错误：{arg}")
    return False
def judge_result(rst):
    if rst:
        print("\t完成")
        return rst
    else:
        print("\t失败")
        return False
def get_item_data(assetId, type, style, name, appellation, SGId, SGName):
    return {
        "assetId": assetId,
        "type": type,
        "style": style,
        "name": name,
        "appellation": appellation,
        "skinGroupId": SGId,
        "skinGroupName": SGName
    }

########## Main-主程序 ##########
def main():
    ##### 预设↓ #####
    arkPetsCompatibility = [2, 0, 0] #ArkPets最低兼容版本
    src_prefix = "https://raw.githubusercontent.com/Kengxxiao/ArknightsGameData/master" #资源地址前缀
    src_server = "zh_CN" #游戏服务器地区（例如zh_CN）
    models_dir = { #模型存放目录（类型=>目录名）
        "Operator": "models"
    }
    src_operdata = f"{src_prefix}/{src_server}/gamedata/excel/character_table.json"
    src_skindata = f"{src_prefix}/{src_server}/gamedata/excel/skin_table.json"
    src_verdata = f"{src_prefix}/{src_server}/gamedata/excel/data_version.txt"
    asset_ext = [".atlas", ".png", ".skel"]

    ##### 主程序↓ #####
    warnings.filterwarnings("ignore")
    print("获取干员数据...")
    d = judge_result(get_json(src_operdata))
    if not d:
        return
    print("解析干员信息...")
    data = {}
    for i in d.keys():
        if len(i) > 5 and i[:5] == "char_":
            data[i[5:]] = get_item_data("build_" + i, "Operator", "BuildingDefault", d[i]["name"], d[i]["appellation"], "ILLUST", "默认服装")
    print(f"\t找到 {len(data)} 位干员")

    print("获取干员皮肤信息...")
    d = judge_result(get_json(src_skindata))["charSkins"]
    if not d:
        return
    print("解析干员皮肤信息...")
    temp = {}
    for i in d.keys():
        if d[i]["buildingId"] != None:
            if d[i]["charId"][5:] in data.keys():
                temp[d[i]["buildingId"][5:]] = get_item_data("build_" + d[i]["buildingId"], "Operator", "BuildingSkin",
                        data[d[i]["charId"][5:]]["name"], data[d[i]["charId"][5:]]["appellation"], d[i]["displaySkin"]["skinGroupId"], d[i]["displaySkin"]["skinGroupName"])
            else:
                print(f"\t皮肤 {d[i]['charId']} 找不到对应的干员Key")
    data.update(temp)
    print(f"\t找到 {len(temp)} 个皮肤")

    print("校验模型文件...")
    checksum_total = 0
    checksum_fail = 0
    for i in data.keys():
        #(i是Key,Key应为文件夹的名称)
        if data[i]["type"] in models_dir.keys():
            #如果其type在模型存放目录预设中有对应值
            checksum = {}
            for j in asset_ext:
                #(j是资源文件后缀名,遍历该模型的所有资源文件)
                p = os.path.join(models_dir[data[i]["type"]], i, data[i]["assetId"] + j)
                if os.path.exists(p):
                    #文件存在时计算md5摘要
                    try:
                        with open(p, "rb") as f:
                            b = f.read()
                            md5 = hashlib.md5(b).hexdigest()
                            checksum[j] = md5
                    except Exception as arg:
                        print(f"\t[{i}] {data[i]['name']} 计算文件摘要时错误：{p}，原因：{arg}")
                        checksum = None
                        checksum_fail += 1
                        break
                else:
                    #特殊处理：有些干员基建模型没有build_前缀
                    newId = data[i]["assetId"].replace("build_","",1)
                    p = os.path.join(models_dir[data[i]["type"]], i, newId + j)
                    if os.path.exists(p):
                        try:
                            with open(p, "rb") as f:
                                b = f.read()
                                md5 = hashlib.md5(b).hexdigest()
                                checksum[j] = md5
                                data[i]["assetId"] = newId
                        except Exception as arg:
                            print(f"\t[{i}] {data[i]['name']} 计算文件摘要时错误：{p}，原因：{arg}")
                            checksum = None
                            checksum_fail += 1
                            break
                    else:
                        print(f"\t[{i}] {data[i]['name']} 未找到其部分文件")
                        checksum = None
                        checksum_fail += 1
                        break
            data[i]["checksum"] = checksum
            checksum_total += 1
        else:
            checksum_fail += 1
            print(f"[{i}] {data[i]['name']} 是{data[i]['type']}类型的，但未在脚本预设中找到该类型的存储目录")
    print(f"\n\t校验完成：成功{checksum_total - checksum_fail}，失败{checksum_fail}")
    print("\t如有预备干员和精英支援干员文件未找到属正常现象。报其他错误或者有其他未找到文件者，可向我们提交Issue查明原因。\n")

    print("查询数据源修订版本...")
    d = judge_result(get_curl(src_verdata))
    if not d:
        return
    print("保存为数据集文件...")
    data = {
        "storageDirectory": models_dir,
        "gameDataVersionDescription": d,
        "gameDataServerRegion": src_server,
        "data": data,
        "arkPetsCompatibility": arkPetsCompatibility
    }
    with open("models_data.json", "w", encoding="UTF-8") as f:
        f.write(json.dumps(data, indent=4, ensure_ascii=False))
    print("\t完成")
    return True

if __name__ == '__main__':
    main()
    input("按Enter退出...")

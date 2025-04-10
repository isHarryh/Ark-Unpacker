# -*- coding: utf-8 -*-
# Copyright (c) 2022-2025, Harry Huang
# @ BSD 3-Clause License
import json
import os.path as osp
from datetime import datetime

from .utils.GlobalMethods import print
from .utils.Logger import Logger


class VoiceDist:
    L10N = {
        # lang_id -> dict (id -> translation)
        "zh-CN": {
            "JP": "日语",
            "CN": "普通话",
            "KR": "韩语",
            "EN": "英语",
            "CUSTOM": "个性化",
            "001": "任命助理",
            "002": "交谈1",
            "003": "交谈2",
            "004": "交谈3",
            "005": "晋升后交谈1",
            "006": "晋升后交谈2",
            "007": "信赖提升后交谈1",
            "008": "信赖提升后交谈2",
            "009": "信赖提升后交谈3",
            "010": "闲置",
            "011": "干员报到",
            "012": "观看作战记录",
            "013": "精英化晋升1",
            "014": "精英化晋升2",
            "017": "编入队伍",
            "018": "任命队长",
            "019": "行动出发",
            "020": "行动开始",
            "021": "选中干员1",
            "022": "选中干员2",
            "023": "部署1",
            "024": "部署2",
            "025": "作战中1",
            "026": "作战中2",
            "027": "作战中3",
            "028": "作战中4",
            "029": "完成高难行动",
            "030": "3星行动结束",
            "031": "非3星行动结束",
            "032": "行动失败",
            "033": "进驻设施",
            "034": "戳一下",
            "036": "信赖触摸",
            "037": "标题",
            "038": "新年祝福",
            "042": "问候",
            "043": "生日祝福",
            "044": "周年庆典",
        },
        "zh-TW": {
            "JP": "日語",
            "CN": "普通話",
            "KR": "韓語",
            "EN": "英語",
            "CUSTOM": "個性化",
            "001": "任命助理",
            "002": "交談1",
            "003": "交談2",
            "004": "交談3",
            "005": "晉升後交談1",
            "006": "晉升後交談2",
            "007": "信賴提升後交談1",
            "008": "信賴提升後交談2",
            "009": "信賴提升後交談3",
            "010": "閒置",
            "011": "幹員報到",
            "012": "觀看作戰紀錄",
            "013": "精英化晉升1",
            "014": "精英化晉升2",
            "017": "編入隊伍",
            "018": "任命隊長",
            "019": "行動出發",
            "020": "行動開始",
            "021": "選中幹員1",
            "022": "選中幹員2",
            "023": "部署1",
            "024": "部署2",
            "025": "作戰中1",
            "026": "作戰中2",
            "027": "作戰中3",
            "028": "作戰中4",
            "029": "完成高難度行動",
            "030": "3星行動結束",
            "031": "非3星行動結束",
            "032": "行動失敗",
            "033": "進駐設施",
            "034": "戳一下",
            "036": "信賴觸摸",
            "037": "標題",
            "038": "新年祝福",
            "042": "問候",
            "043": "生日祝福",
            "044": "週年慶典",
        },
        "jp-JP": {
            "JP": "日本語",
            "CN": "標準中国語",
            "KR": "韓国語",
            "EN": "英語",
            "CUSTOM": "カスタマイズ",
            "001": "アシスタントを任命",
            "002": "会話1",
            "003": "会話2",
            "004": "会話3",
            "005": "昇進後の会話1",
            "006": "昇進後の会話2",
            "007": "信頼度アップ後の会話1",
            "008": "信頼度アップ後の会話2",
            "009": "信頼度アップ後の会話3",
            "010": "待機中",
            "011": "オペレーター報告",
            "012": "作戦記録の確認",
            "013": "エリート昇進1",
            "014": "エリート昇進2",
            "017": "チームに編成",
            "018": "隊長を任命",
            "019": "作戦出発",
            "020": "作戦開始",
            "021": "オペレーター選択1",
            "022": "オペレーター選択2",
            "023": "配置1",
            "024": "配置2",
            "025": "作戦中1",
            "026": "作戦中2",
            "027": "作戦中3",
            "028": "作戦中4",
            "029": "高難易度作戦完了",
            "030": "3星評価作戦終了",
            "031": "非3星評価作戦終了",
            "032": "作戦失敗",
            "033": "施設に入駐",
            "034": "タップ1回",
            "036": "信頼タッチ",
            "037": "タイトル",
            "038": "新年のご挨拶",
            "042": "挨拶",
            "043": "誕生日祝い",
            "044": "周年記念",
        },
        "ko-KR": {
            "JP": "일본어",
            "CN": "표준 중국어",
            "KR": "한국어",
            "EN": "영어",
            "CUSTOM": "개인화",
            "001": "보조 임명",
            "002": "대화1",
            "003": "대화2",
            "004": "대화3",
            "005": "승진 후 대화1",
            "006": "승진 후 대화2",
            "007": "신뢰도 상승 후 대화1",
            "008": "신뢰도 상승 후 대화2",
            "009": "신뢰도 상승 후 대화3",
            "010": "대기 중",
            "011": "오퍼레이터 보고",
            "012": "작전 기록 확인",
            "013": "엘리트 승진1",
            "014": "엘리트 승진2",
            "017": "팀에 배치",
            "018": "대장 임명",
            "019": "작전 출발",
            "020": "작전 시작",
            "021": "오퍼레이터 선택1",
            "022": "오퍼레이터 선택2",
            "023": "배치1",
            "024": "배치2",
            "025": "작전 중1",
            "026": "작전 중2",
            "027": "작전 중3",
            "028": "작전 중4",
            "029": "고난이도 작전 완료",
            "030": "3성 작전 종료",
            "031": "비 3성 작전 종료",
            "032": "작전 실패",
            "033": "시설에 입주",
            "034": "한 번 눌러요",
            "036": "신뢰 터치",
            "037": "타이틀",
            "038": "새해 인사",
            "042": "인사",
            "043": "생일 축하",
            "044": "기념일",
        },
        "en-US": {
            "JP": "Japanese",
            "CN": "Mandarin",
            "KR": "Korean",
            "EN": "English",
            "CUSTOM": "Custom",
            "001": "Appoint Assistant",
            "002": "Talk 1",
            "003": "Talk 2",
            "004": "Talk 3",
            "005": "Post-Promotion Talk 1",
            "006": "Post-Promotion Talk 2",
            "007": "Trust Increase Talk 1",
            "008": "Trust Increase Talk 2",
            "009": "Trust Increase Talk 3",
            "010": "Idle",
            "011": "Operator Reporting",
            "012": "View Mission Records",
            "013": "Elite Promotion 1",
            "014": "Elite Promotion 2",
            "017": "Deploy to Team",
            "018": "Appoint Leader",
            "019": "Mission Departure",
            "020": "Mission Start",
            "021": "Selected Operator 1",
            "022": "Selected Operator 2",
            "023": "Deploy 1",
            "024": "Deploy 2",
            "025": "In Mission 1",
            "026": "In Mission 2",
            "027": "In Mission 3",
            "028": "In Mission 4",
            "029": "Hard Mission End",
            "030": "3-Star Mission End",
            "031": "Non-3-Star Mission End",
            "032": "Mission Failure",
            "033": "Enter Facility",
            "034": "Tap Once",
            "036": "Trust Touch",
            "037": "Title",
            "038": "New Year Greeting",
            "042": "Greeting",
            "043": "Birthday Wishes",
            "044": "Anniversary Celebration",
        },
    }
    ARK_PETS_COMPATIBILITY = [4, 0, 0]
    SERVER_REGION = "zh_CN"
    FORMAT = ".ogg"
    VARIATIONS_DIR = {
        # variation_id -> dirname
        "JP": "voice",
        "CN": "voice_cn",
        "KR": "voice_kr",
        "EN": "voice_en",
        "CUSTOM": "voice_custom",
    }
    TYPES = {
        # type -> regex
        "common": r"^CN_\d\d\d$",
        "effected": r"^FX_\d\d\d(_\d)?$",
    }
    DATA_PART_FILE = "voice_data_part.json"

    def __init__(self):
        self.data = {
            "localizations": VoiceDist.L10N,
            "storageDirectory": VoiceDist.VARIATIONS_DIR,
            "gameDataVersionDescription": f"Producer: ArkUnpacker 3\nDate: {datetime.now().date()}\n",
            "gameDataServerRegion": VoiceDist.SERVER_REGION,
            "data": {},
            "audioTypes": VoiceDist.TYPES,
            "audioFormat": VoiceDist.FORMAT,
            "arkPetsCompatibility": VoiceDist.ARK_PETS_COMPATIBILITY,
        }

    def retrieve(self):
        Logger.info(f"VoiceDataDist: Starting retrieve voice data.")
        print("读取各语种的子数据集...")
        failed = False
        for var, dir in VoiceDist.VARIATIONS_DIR.items():
            cnt = 0
            if not osp.isdir(dir):
                Logger.error(f"VoiceDataDist: Dir {dir} not found.")
                print(f"\t未找到语种文件夹 {dir}", c=3)
                failed = True
            else:
                data_part_file = osp.join(dir, VoiceDist.DATA_PART_FILE)
                if not osp.isfile(data_part_file):
                    Logger.error(
                        f"VoiceDataDist: Data part file {data_part_file} not found."
                    )
                    print(f"\t未找到子数据集文件 {data_part_file}", c=3)
                    failed = True
                else:
                    data_part: dict = json.load(
                        open(data_part_file, "r", encoding="UTF-8")
                    )
                    for cha, lst in data_part.items():
                        cnt += 1
                        if cha not in self.data["data"]:
                            self.data["data"][cha] = {"variations": {}}
                        self.data["data"][cha]["variations"][var] = lst
                    Logger.info(
                        f"VoiceDataDist: Variation {var} includes {cnt} voice file."
                    )
                    print(f"\t语种 {var} 包含 {cnt} 套语音文件", c=2)
        if failed:
            print("读取子数据集时发生警告，因此总数据集可能不完整", c=1)
        else:
            print("读取子数据集完毕", c=2)

    def sort(self):
        self.data["data"] = dict(sorted(self.data["data"].items()))

    def export_json(self):
        Logger.info("VoiceDataDist: Writing to json.")
        with open("voice_data.json", "w", encoding="UTF-8") as f:
            json.dump(
                self.data, f, ensure_ascii=False, indent=None, separators=(",", ":")
            )
        Logger.info("VoiceDataDist: Succeeded in writing to json.")
        print("\n已写入总数据集文件", c=2)


########## Main-主程序 ##########
def main():
    vd = VoiceDist()
    vd.retrieve()
    vd.sort()
    vd.export_json()

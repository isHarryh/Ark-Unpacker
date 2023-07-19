ArkUnpacker附加说明文档
# 游戏资源查找指南

## 补充说明
1. 请在合理范围内使用本程序。基于**BSD3协议**，对于非法使用本程序解包出来的资源造成的侵权行为，作者不承担相应责任。
2. 此页文档内的所有内容为作者独立整理，如需转载请注明出处。
3. **时效性警告** - 以下内容基于 **Android`v2.0.01`** 的明日方舟，不同版本的资源具体位置可能存在差异。


## 资源导览
各个子目录储存的资源的内容：

**Android**  
├─[activity](#activity) / 活动   
├─[arts](#arts) / 图片  
├─[audio](#audio) / 音频  
├─[avg](#avg) / 剧情图  
├─[battle](#battle) / 战斗相关  
├─[building](#building) / 基建  
├─chararts / 干员(立绘和基建小人)  
├─charpack / 干员(战斗小人)  
├─climbtowerseasons / 保全派驻  
├─config / 配置  
├─crisisseasons / 危机合约  
├─gamedata / 游戏数据  
├─graphics / 图形渲染  
├─[hotupdate](#hotupdate) / 热更新相关  
├─[i18n](#i18n) / 多语言(国际化)  
├─npcpack / NPC  
├─[prefabs](#perfabs) / 预设文件  
├─raw / 未打包文件(例如视频)  
├─refs / 引用？  
├─retro / 复刻活动  
├─scenes / 关卡  
├─skinpack / 干员皮肤  
├─[spritepack](#spritepack) / 图标  
└─[ui](#ui) / 用户界面  

> 提示：  
> 1. 在明日方舟`v1.8.01`及之前版本中，干员默认皮肤的立绘、基建小人和战斗小人全都位于`charpack`中。而在之后的版本中，立绘和基建小人被转移到了`chararts`中存放。
> 2. 解包只是解包AB文件。这意味着像`raw/video/`里的部分非AB文件不会放到解包后文件夹中，所以请在原始文件中查找它们。


## 常用资源定位
条目较多，可使用`Ctrl+F`查找关键字。
[返回顶部](#资源导览)

### Activity
- `activity/[uc]act{xxx}.ab` 某个活动的界面相关资源
- `activity/commonassets.ab` 活动物资的通用图标

### Arts
- `arts/building/` 基建相关图标（基建技能图标等）
- `arts/charportraits/` 干员半身像
- `arts/dynchars/` 动态立绘资源
- `arts/guidebookpages/` 新手指引相关
- `arts/maps/` 地图地形材质
- `arts/shop/` 采购中心相关
- `arts/ui/` 各类UI插图
- `arts/clue_hub.ab` 线索图标
- `arts/elite_hub.ab` 精英化图标
- `arts/potential_hub.ab` 潜能图标
- `arts/profession_hub.ab` 职业图
- `arts/rarity_hub.ab` 稀有度星级图标
- `arts/specialized_hub.ab` 技能专精图标

### Audio
- `audio/sound_beta_2/avg/` 剧情音效
- `audio/sound_beta_2/enemy/` 敌人战斗音效
- `audio/sound_beta_2/music/` 游戏音乐
- `audio/sound_beta_2/player/` 干员战斗音效
- `audio/sound_beta_2/voice/` 语音包(日文)
- `audio/sound_beta_2/voice_{xxx}/` 语音包(其他语言)
- `audio/sound_beta_2/ambience.ab` 环境氛围音效
- `audio/sound_beta_2/battle.ab` 其他战斗音效
- `audio/sound_beta_2/vox.ab` 人声音效

> 提示：  
> 解包出的语音包内容取决于您的原始游戏文件。这意味着如果您在游戏里没有下载某个语言的语音包，则不会解包出此语言包。

### Avg
- `avg/bg/` 剧情背景图
- `avg/characters/` 剧情人物图
- `avg/effects/` 剧情特效
- `avg/imgs/` 剧情插图
- `avg/items/` 剧情道具图

### Battle
- `battle/prefabs/effects/` 战斗特效
- `battle/prefabs/enemies/` 敌方Spine
- `battle/prefabs/[uc]tokens.ab` 战斗道具和部分召唤物Spine

### Building
- `building/blueprint/[uc]rooms.ab` 基建UI
- `building/ui/[uc]diy.ab` 基建房间装扮模式UI
- `building/vault/[uc]arts.ab` 基建功能室Sprite

### Hotupdate
- `hotupdate/[uc]worldtips.ab` 热更新时背景图(开屏图)

### I18n
- `i18n/string_map.ab` 字符串映射表

### Perfabs
- `prefabs/shop/shopkeeper/` 可露希尔
- `prefabs/gacha/` 干员寻访相关

### Spritepack
活动
- `spritepack/act_achieve_{xxx}.ab` 活动相关插图
- `spritepack/ui_charm_icon_list.ab` 活动:多索雷斯假日标志物

剿灭作战
- `spritepack/ui_campaign_stage_icon.ab` 剿灭作战:关卡背景图
- `spritepack/ui_campaign_world_map_piece.ab` 剿灭作战:地图碎片图
- `spritepack/ui_campaign_zone_icon.ab` 剿灭作战:地区图标

剧情回顾
- `spritepack/story_review_mini_activity.ab` 剧情回顾:故事集封面
- `spritepack/story_review_mini_char.ab` 剧情回顾:子故事封面

危机合约
- `spritepack/ui_crisis_appraise.ab` 危机合约:通关等级图标
- `spritepack/ui_crisis_level.ab` 危机合约:词条等级图标
- `spritepack/ui_crisis_rune_bg.ab` 危机合约:词条背景图
- `spritepack/ui_crisis_rune_bg.ab` 危机合约:词条图标
- `spritepack/ui_crisis_shop.ab` 危机合约:商店相关
- `spritepack/ui_dyn_crisis_entry.ab` 危机合约:关卡加载中背景图

干员模组
- `spritepack/ui_equip_big_img_hub.ab` 干员模组:模组大图
- `spritepack/ui_equip_type_direction_hub.ab` 干员模组:模组类型图标
- `spritepack/ui_equip_type_hub.ab` 干员模组:模组类型图标

预览
- `spritepack/ui_handbook_battle_preview.ab` 预览:关卡加载中背景图
- `spritepack/ui_homebackground_preview.ab` 预览:首页背景图

宣传图
- `spritepack/ui_home_act_banner_gacha.ab` 宣传图:新寻访开放
- `spritepack/ui_home_act_banner_shop.ab` 宣传图:可露希尔推荐
- `spritepack/ui_home_act_banner_zone.ab` 宣传图:新章节开放

仓库
- `spritepack/ui_item_icons.ab` 仓库:常规物品图标
- `spritepack/ui_item_icons_acticon.ab` 仓库:活动物品图标?
- `spritepack/ui_item_icons_apsupply.ab` 仓库:理智道具图标
- `spritepack/ui_item_icons_classpotential.ab` 仓库:中坚潜能信物图标
- `spritepack/ui_item_icons_potential.ab` 仓库:潜能信物图标

蚀刻章
- `spritepack/ui_medal_banner_list.ab` 蚀刻章:套组横幅
- `spritepack/ui_medal_diy_frame_bkg.ab` 蚀刻章:套组卡槽背景
- `spritepack/ui_medal_icon_list.ab` 蚀刻章:蚀刻章图标

头像
- `spritepack/icon_enemies.ab` 敌人头像
- `spritepack/ui_char_avatar.ab` 干员头像
- `spritepack/ui_player_avatar_list.ab` 玩家头像

图标
- `spritepack/building_ui_buff_skills.ab` 基建技能图标
- `spritepack/character_sort_type_icon.ab` 干员筛选要素图标
- `spritepack/skill_icons.ab` 技能图标
- `spritepack/ui_camp_logo.ab` 阵营图标
- `spritepack/ui_sub_profession_icon_hub.ab` 职业分支图标
- `spritepack/ui_team_icon.ab` 阵营图标

其他
- `spritepack/building_diy_theme.ab` 家具套装预览
- `spritepack/chapter_title.ab` 主线章节文字标题图
- `spritepack/ui_brand_image_hub.ab` 时装品牌
- `spritepack/ui_gp_shop_dyn.ab` 采购中心组合包相关
- `spritepack/ui_kv_img.ab` 时装展示大图
- `spritepack/ui_main_mission_bg.ab` 主线任务背景图
- `spritepack/ui_stage_retro_title.ab` 复刻后活动封面
- `spritepack/ui_start_battle_button.ab` 开始行动按钮图
- `spritepack/ui_zone_home_theme.ab` 终端封面图

> 提示：  
> 为简洁起见，上方列出的Spritepack中的AB文件名不是完整的，通常其后面会有一些分类号比如`_h1`、`_0`等。

### Ui
- `ui/activity/` 各种活动
- `ui/bossrush/` 引航者行动
- `ui/campaign/` 剿灭作战
- `ui/characterinfo/` 干员信息页面相关
- `ui/friendassist/` 好友助战页面相关
- `ui/gacha/` 干员寻访相关
- `ui/handbook/` 干员档案相关
- `ui/legion/` 保全派驻
- `ui/operation/returnning/` 玩家回归活动
- `ui/pages/` 各种页面的UI
- `ui/rglktopic/` 集成战略各主题UI
- `ui/squadassist/` 好友助战编队相关
- `ui/stage/enemyhandbook/` 敌人档案相关
- `ui/timelydrop/` 限时掉落
- `ui/[uc]charsortfilter.ab` 干员筛选相关
- `ui/[uc]climbtower.ab` 保全派驻关卡页相关
- `ui/[uc]squad.ab` 编队页面相关
- `ui/activity/actfun.ab` 愚人节活动
- `ui/recruit/states/recruit_ten_result_state.ab` 十连寻访
- `ui/skin_groups.ab` 时装品牌
- `ui/zonemap_{x}.ab` 主线关卡页背景
- `ui/zonemap_camp{x}.ab` 剿灭作战关卡页背景

[返回顶部](#资源导览)

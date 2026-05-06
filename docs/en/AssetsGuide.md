Additional Documentation for ArkUnpacker

# Game Resource Navigation Guide

> **Outdated Warning:**  
> This document has not been maintained for a long time and may be outdated. Please use it with caution.

> **Note:**  
> - Please use this tool within reasonable limits. Under the BSD 3-Clause License, the author is not responsible for any infringement caused by illegal use of unpacked resources.
> - The following content is based on **Arknights Android `v2.4.01`**. The exact locations of specific resources may vary significantly across different client versions.
> - All content in this document is compiled by the author and is for reference purposes only. Please cite the source if you wish to copy it.

<!-- spell-checker: disable -->

## Resource Overview

Contents stored in each subdirectory:

**Android**  
├─[activity](#activity) / Events  
├─anon / Anonymous data  
├─[arts](#arts) / Art assets  
├─[audio](#audio) / Audio  
├─[avg](#avg) / Story images  
├─[battle](#battle) / Battle-related  
├─[building](#building) / Base (Infrastructure)  
├─chararts / Operators (illustrations & base chibi models)  
├─charpack / Operators (battle chibi models)  
├─climbtowerseasons / Stationary Security Service  
├─config / Configuration  
├─crisisv2longterm / Contingency Contract (new version)  
├─cutin / Character cut-ins  
├─graphics / Rendering  
├─npcpack / NPCs  
├─[prefabs](#perfabs) / Prefab files  
├─raw / Unpacked files (e.g., videos)  
├─refs / Integrated Strategies  
├─retro / Permanent side stories & events  
├─scenes / Stages  
├─skinpack / Operator skins  
├─[spritepack](#spritepack) / Icons  
└─[ui](#ui) / User Interface  

> **Important Changes:**  
> 1. In Arknights versions `v1.8.01` and earlier, default operator skins (illustrations, base chibi, and battle chibi) were all stored in `charpack`. In later versions, illustrations and base chibi models were moved to `chararts`.  
> 2. In Arknights versions `v2.3.81` and earlier, game data files were stored in the `gamedata` directory, hot update splash assets in `hotupdate`, and localization data in `i18n`. In later versions, these were moved to `anon` as anonymous files, and their extensions were changed to `.bin`.

> **Tip:**  
> Unpacking only extracts AB files. This means some non-AB files (e.g., under `raw/video/`) will not appear in the unpacked output. Please locate them in the original files.

---

## Common Resource Locations

There are many resource entries. You can use your browser or editor’s search function (e.g., `Ctrl+F`) to find keywords.

[Back to top](#资源导览)

---

### Activity

- `activity/[uc]act{xxx}.ab` UI-related assets for a specific event  
- `activity/commonassets.ab` Common event item icons  

---

### Arts

- `arts/building/` Base-related icons (e.g., base skill icons)  
- `arts/charportraits/` Operator half-body portraits  
- `arts/dynchars/` Dynamic illustration assets  
- `arts/guidebookpages/` Tutorial-related assets  
- `arts/maps/` Map terrain textures  
- `arts/shop/` Store-related assets  
- `arts/ui/` Various UI illustrations  
- `arts/clue_hub.ab` Clue icons  
- `arts/elite_hub.ab` Elite icons  
- `arts/potential_hub.ab` Potential icons  
- `arts/profession_hub.ab` Class icons  
- `arts/rarity_hub.ab` Rarity/star icons  
- `arts/specialized_hub.ab` Skill mastery icons  

---

### Audio

- `audio/sound_beta_2/enemy/` Enemy SFX  
- `audio/sound_beta_2/music/` Music  
- `audio/sound_beta_2/player/` Operator SFX  
- `audio/sound_beta_2/voice/` Voice pack (Japanese)  
- `audio/sound_beta_2/voice_{xxx}/` Voice packs (other languages)  
- `audio/sound_beta_2/ambience.ab` Ambient sounds  
- `audio/sound_beta_2/avg_{xxx}.ab/` Story SFX  
- `audio/sound_beta_2/battle.ab` Other battle SFX  
- `audio/sound_beta_2/vox.ab` Voice-related SFX  

> **Tip:**  
> Extracted voice content depends on your original game files. If a language voice pack is not downloaded in-game, it will not be included in the extracted output.

---

### Avg

- `avg/bg/` Story backgrounds  
- `avg/characters/` Story character images  
- `avg/effects/` Story effects  
- `avg/imgs/` Story illustrations  
- `avg/items/` Story item images  

---

### Battle

- `battle/prefabs/effects/` Battle effects  
- `battle/prefabs/enemies/` Enemy Spine assets  
- `battle/prefabs/[uc]tokens.ab` Battle items and some summon Spine assets  

---

### Building

- `building/blueprint/` Base UI  
- `building/diy/` Decoration and furniture assets  
- `building/ui/[uc]diy.ab` Base decoration UI  
- `building/vault/[uc]arts.ab` Base facility sprites  

---

### Perfabs

- `prefabs/shop/shopkeeper/` Closure  
- `prefabs/gacha/` Recruitment-related assets  

---

### Spritepack

**Events**
- `spritepack/act_achieve_{xxx}.ab` Event illustrations  
- `spritepack/ui_charm_icon_list.ab` Event: Dossoles Holiday markers  

**Annihilation**
- `spritepack/ui_campaign_stage_icon.ab` Stage backgrounds  
- `spritepack/ui_campaign_world_map_piece.ab` Map fragments  
- `spritepack/ui_campaign_zone_icon.ab` Region icons  

**Story Review**
- `spritepack/story_review_mini_activity.ab` Story collection covers  
- `spritepack/story_review_mini_char.ab` Sub-story covers  

**Operator Modules**
- `spritepack/ui_equip_big_img_hub.ab` Module images  
- `spritepack/ui_equip_type_direction_hub.ab` Module type icons  
- `spritepack/ui_equip_type_hub.ab` Module type icons  

**Preview**
- `spritepack/ui_handbook_battle_preview.ab` Loading screen backgrounds  
- `spritepack/ui_homebackground_preview.ab` Home background previews  

**Promotional**
- `spritepack/ui_home_act_banner_gacha.ab` New banner  
- `spritepack/ui_home_act_banner_shop.ab` Closure recommendations  
- `spritepack/ui_home_act_banner_zone.ab` New chapter banners  

**Inventory**
- `spritepack/ui_item_icons.ab` Standard item icons  
- `spritepack/ui_item_icons_acticon.ab` Event item icons  
- `spritepack/ui_item_icons_apsupply.ab` Sanity item icons  
- `spritepack/ui_item_icons_classpotential.ab` Class token icons  
- `spritepack/ui_item_icons_potential.ab` Potential token icons  

**Medals**
- `spritepack/ui_medal_banner_list.ab` Medal set banners  
- `spritepack/ui_medal_diy_frame_bkg.ab` Medal frame backgrounds  
- `spritepack/ui_medal_icons.ab` Medal icons  

**Avatars**
- `spritepack/icon_enemies.ab` Enemy avatars  
- `spritepack/ui_char_avatar.ab` Operator avatars  
- `spritepack/ui_player_avatar_list.ab` Player avatars  

**Icons**
- `spritepack/building_ui_buff_skills.ab` Base skill icons  
- `spritepack/character_sort_type_icon.ab` Operator filter icons  
- `spritepack/skill_icons.ab` Skill icons  
- `spritepack/ui_camp_logo.ab` Faction logos  
- `spritepack/ui_sub_profession_icon_hub.ab` Subclass icons  
- `spritepack/ui_team_icon.ab` Team icons  

**Others**
- `spritepack/building_diy_theme.ab` Furniture set previews  
- `spritepack/chapter_title.ab` Chapter title images  
- `spritepack/ui_brand_image_hub.ab` Outfit brands  
- `spritepack/ui_gp_shop_dyn.ab` Store bundle assets  
- `spritepack/ui_kv_img.ab` Outfit showcase images  
- `spritepack/ui_main_mission_bg.ab` Main mission backgrounds  
- `spritepack/ui_stage_retro_title.ab` Event rerun covers  
- `spritepack/ui_start_battle_button.ab` Start battle button  
- `spritepack/ui_zone_home_theme.ab` Terminal backgrounds  

> **Tip:**  
> For simplicity, the AB filenames listed above are not complete. They usually include suffixes such as `_h1`, `_0`, etc.

---

### UI

- `ui/activity/` Events  
- `ui/bossrush/` Contingency mode  
- `ui/campaign/` Annihilation  
- `ui/characterinfo/` Operator info pages  
- `ui/friendassist/` Support unit pages  
- `ui/gacha/` Recruitment  
- `ui/handbook/` Operator records  
- `ui/legion/` Stationary Security Service  
- `ui/pages/` Various UI pages  
- `ui/rglktopic/` Integrated Strategies UI  
- `ui/sandboxv2/` Reclamation Algorithm  
- `ui/squadassist/` Support squad setup  
- `ui/stage/enemyhandbook/` Enemy database  
- `ui/timelydrop/` Limited-time drops  
- `ui/[uc]charsortfilter.ab` Operator filters  
- `ui/[uc]climbtower.ab` Security Service stage UI  
- `ui/[uc]squad.ab` Squad UI  
- `ui/operation/return.ab` Return event  
- `ui/recruit/states/recruit_ten_result_state.ab` Ten-pull result  
- `ui/skin_groups.ab` Outfit brands  
- `ui/zonemap_{x}.ab` Main stage backgrounds  
- `ui/zonemap_camp{x}.ab` Annihilation stage backgrounds  

[Back to top](#资源导览)
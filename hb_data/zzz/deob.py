from hb_data.common.base_deob import (
    BaseDeobfuscator,
    DeobfuscatedField,
    find_key_by_position,
    find_key_by_value,
)


class AvatarBaseTemplateTbDeobfuscator(BaseDeobfuscator):
    id = DeobfuscatedField("ID", lambda data: find_key_by_value(data, 1011))
    ui_name = DeobfuscatedField(
        "UIName", lambda data: find_key_by_value(data, "Avatar_Female_Size02_Anbi_En")
    )
    full_name = DeobfuscatedField(
        "FullName", lambda data: find_key_by_value(data, "Avatar_Female_Size02_Anbi_FullName")
    )


class AvatarBattleTemplateTbDeobfuscator(BaseDeobfuscator):
    id = DeobfuscatedField("ID", lambda data: find_key_by_value(data, 1011))
    elements = DeobfuscatedField("Elements", lambda data: find_key_by_value(data, [203]))
    specialty = DeobfuscatedField("AvatarSpecialty", lambda data: find_key_by_value(data, 2))


class AvatarUITemplateTbDeobfuscator(BaseDeobfuscator):
    id = DeobfuscatedField("ID", lambda data: find_key_by_value(data, 1011))
    camp_name = DeobfuscatedField(
        "CampName", lambda data: find_key_by_value(data, "CampGentleHouse")
    )


class WeaponTemplateTbDeobfuscator(BaseDeobfuscator):
    item_id = DeobfuscatedField("ItemID", lambda data: find_key_by_value(data, 12001))
    specialty = DeobfuscatedField("WeaponSpecialty", lambda data: find_key_by_position(data, 13))


class ItemTemplateTbDeobfuscator(BaseDeobfuscator):
    item_id = DeobfuscatedField("ItemID", lambda data: find_key_by_position(data, 0))
    name = DeobfuscatedField("Name", lambda data: find_key_by_value(data, "Item_Coin"))
    rarity = DeobfuscatedField("Rarity", lambda data: find_key_by_position(data, 2))


class EquipmentTemplateTbDeobfuscator(BaseDeobfuscator):
    item_id = DeobfuscatedField("ItemID", lambda data: find_key_by_value(data, 31021))
    position = DeobfuscatedField("Position", lambda data: find_key_by_value(data, 1))
    suit_id = DeobfuscatedField("SuitID", lambda data: find_key_by_value(data, 31000))


class EquipmentSuitTemplateTbDeobfuscator(BaseDeobfuscator):
    id = DeobfuscatedField("ID", lambda data: find_key_by_value(data, 31000))
    name = DeobfuscatedField(
        "Name", lambda data: find_key_by_value(data, "EquipmentSuit_31000_name")
    )
    two_set_effect = DeobfuscatedField(
        "TwoSetEffect", lambda data: find_key_by_value(data, "EquipmentSuit_31000_2_des")
    )
    four_set_effect = DeobfuscatedField(
        "FourSetEffect", lambda data: find_key_by_value(data, "EquipmentSuit_31000_4_des")
    )
    suit_story = DeobfuscatedField(
        "SuitStory", lambda data: find_key_by_value(data, "EquipmentSuit_31000_story")
    )


class BuddyBaseTemplateTbDeobfuscator(BaseDeobfuscator):
    id = DeobfuscatedField("ID", lambda data: find_key_by_value(data, 50001))
    name = DeobfuscatedField("Name", lambda data: find_key_by_value(data, "Bangboo_Name_en_50001"))

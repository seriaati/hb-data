from __future__ import annotations

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
    specialty = DeobfuscatedField("Specialty", lambda data: find_key_by_value(data, 2))


class WeaponTemplateTbDeobfuscator(BaseDeobfuscator):
    item_id = DeobfuscatedField("ItemID", lambda data: find_key_by_value(data, 12001))


class ItemTemplateTbDeobfuscator(BaseDeobfuscator):
    item_id = DeobfuscatedField("ItemID", lambda data: find_key_by_position(data, 0))
    name = DeobfuscatedField("Name", lambda data: find_key_by_value(data, "Item_Coin"))

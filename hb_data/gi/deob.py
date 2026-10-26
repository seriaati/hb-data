from hb_data.common.base_deob import BaseDeobfuscator, DeobfuscatedField, find_key_by_value


class BeyondCostumeDrawingDeobfuscator(BaseDeobfuscator):
    id = DeobfuscatedField("id", lambda data: find_key_by_value(data, 270001))
    costume_ids = DeobfuscatedField("costumeIds", lambda data: find_key_by_value(data, [260001]))

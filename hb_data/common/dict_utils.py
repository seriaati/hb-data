from collections import defaultdict


def merge_dicts_by_key(lists: list[list[dict]], *, key: str) -> list[dict]:
    merged: dict = defaultdict(dict)

    for lst in lists:
        for item in lst:
            if key in item:
                merged[item[key]].update(item)

    return list(merged.values())

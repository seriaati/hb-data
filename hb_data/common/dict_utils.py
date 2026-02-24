from collections import defaultdict


def merge_dicts_by_key(lists: list[list[dict]], *, key: str) -> list[dict]:
    merged: dict = defaultdict(dict)

    for lst in lists:
        for item in lst:
            if key in item:
                merged[item[key]].update(item)

    return list(merged.values())


def merge_dicts_by_different_keys(dicts: dict[str, list[dict]]) -> list[dict]:
    (first_key, first_list), *rest = dicts.items()

    result = list(first_list)
    for key, lst in rest:
        index = {item[key]: item for item in lst}
        merged = []
        for item in result:
            match = index.get(item[first_key])
            if match:
                merged.append({**item, **match})
        result = merged

    return result

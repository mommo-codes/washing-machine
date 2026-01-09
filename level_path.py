by_code = {item["code"]: item for item in flat}

def get_level_names(code):
    item = by_code.get(code)
    if not item:
        return None

    return {
        f"level_{i+1}": name
        for i, name in enumerate(item["path"])
    }

print(get_level_names(30010066))

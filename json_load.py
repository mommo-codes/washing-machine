from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parent
GPC_FILE = BASE_DIR / "gpc_codes.json"

print("Loading:", GPC_FILE)

with GPC_FILE.open("r", encoding="utf-8") as f:
    data = json.load(f)

gpc_tree = data["Schema"]

print("Root nodes:", len(gpc_tree))
print("First root keys:", gpc_tree[0].keys())


def flatten_gpc(nodes, parent=None, path=None, result=None):
    if result is None:
        result = []
    if path is None:
        path = []

    for node in nodes:
        current_path = path + [node["Title"]]

        item = {
            "level": node.get("Level"),
            "code": node.get("Code"),
            "title": node.get("Title"),
            "parent_code": parent.get("Code") if parent else None,
            "path": current_path,
            "active": node.get("Active"),
        }

        result.append(item)

        childs = node.get("Childs", [])
        if childs:
            flatten_gpc(
                childs,
                parent=node,
                path=current_path,
                result=result
            )

    return result



flat = flatten_gpc(gpc_tree)

print("Flattened nodes:", len(flat))
print("Sample node:", flat[0])


# Build fast lookup by code
by_code = {item["code"]: item for item in flat}

print("Lookup example (30010066):")
print(by_code.get(30010066))


# Optional: save flattened version
OUT_FILE = BASE_DIR / "gpc_flat.json"
with OUT_FILE.open("w", encoding="utf-8") as f:
    json.dump(flat, f, ensure_ascii=False)

print("Saved flattened file to:", OUT_FILE)


by_code = {item["code"]: item for item in flat}

def get_level_names(code):
    item = by_code.get(code)
    if not item:
        return None

    return {
        f"level_{i+1}": name
        for i, name in enumerate(item["path"])
    }

print(get_level_names(10000045))
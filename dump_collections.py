import os
import json
from pymongo import MongoClient
from bson import json_util

# ✅ 设置数据库连接
client = MongoClient("mongodb://localhost:27017/")
db = client["chatdb"]

# ✅ 你现在用的4个集合
collections = ["users", "movies", "wishlist", "watched"]

# ✅ 导出路径（当前目录下）
output_dir = "data_exports"
os.makedirs(output_dir, exist_ok=True)

for name in collections:
    data = list(db[name].find({}))
    with open(f"{output_dir}/{name}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=json_util.default, ensure_ascii=False)

print("✅ Export complete. Check 'data_exports/' folder.")

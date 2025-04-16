import os
import json
from glob import glob

# === 路径设置 ===
base_dir = "/home/lym/GraphRAG4OralHealth/Benchmark/Knowledge Objectives/Answer/qwen-max"
response_path = "/home/lym/GraphRAG4OralHealth/Benchmark/Knowledge Objectives/d9a655c6-59ad-48cd-9c6d-81ff253465e4_1744800934181_success.jsonl"  # 你的模型响应结果文件

# === 加载响应文件（每行一个 JSON） ===
responses = []
with open(response_path, "r", encoding="utf-8") as f:
    for line in f:
        if line.strip():
            data = json.loads(line)
            msg = data["response"]["body"]["choices"][0]["message"]
            responses.append({
                "prediction": msg.get("content", "").strip(),
                "reason": msg.get("reasoning_content", "").strip()
            })

print(f"✅ 加载响应总数: {len(responses)}")

# === 遍历所有子目录下的 JSON 文件并填入 prediction 和 reason ===
response_index = 0
for root, dirs, files in os.walk(base_dir):
    for file in files:
        if not file.endswith(".json"):
            continue

        file_path = os.path.join(root, file)
        print(f"📝 正在处理文件: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except Exception as e:
                print(f"❌ 无法解析文件 {file_path}: {e}")
                continue

        updated = False
        for q in data:
            if response_index >= len(responses):
                print(f"⚠️ 响应数量不足，已跳出")
                break
            if "prediction" in q and "reason" in q:
                q["prediction"] = responses[response_index]["prediction"]
                q["reason"] = responses[response_index]["reason"]
                response_index += 1
                updated = True

        if updated:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✅ 所有文件更新完毕，写入总题数: {response_index}")

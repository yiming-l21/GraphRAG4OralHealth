import os
import json
from glob import glob
from inference_wrappers import deepseek_r1_inference
# === 路径设置 ===
base_dir = "/home/lym/GraphRAG4OralHealth/Benchmark/Knowledge Objectives/Answer/deepseek_r1"

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
            if "prediction" in q and "reason" in q:
                if q["prediction"] != "":
                    continue
                else:
                    ques_text = (
                    "下面我会给你一个医学相关的问题，请你根据医学知识进行回答。"
                    "一个题目有5个选项，请选出最合适的选项，并输出选项前字母。"
                    "注意只需要输出选项前字母，不需要输出任何其他内容。\n"
                    f"题目:\n{q['题目']}\n选项:\n{q['选项']}"
                )
                    q["prediction"],q["reason"] = deepseek_r1_inference(ques_text)
                    print(f" 题目: {q['题目']}")
                    print(f" 预测: {q['prediction']} 理由: {q['reason']}")
                    response_index += 1
                    updated = True
        if updated:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✅ 所有文件更新完毕，写入总题数: {response_index}")

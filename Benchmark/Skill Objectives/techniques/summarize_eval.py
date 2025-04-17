import os
import json
import glob
import pandas as pd

EVAL_DIR = "eval"  # 存放各模型评分结果的目录
DIMENSIONS = ["正确性", "完整性", "安全性", "理解力", "逻辑性", "总分"]

def summarize_model_scores(eval_dir):
    result = []

    # 遍历所有模型评测结果文件
    for file_path in glob.glob(os.path.join(eval_dir, "*_eval.json")):
        model_name = os.path.basename(file_path).replace("_eval.json", "")
        scores = {dim: [] for dim in DIMENSIONS}

        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    record = json.loads(line)
                    for dim in DIMENSIONS:
                        if dim in record and isinstance(record[dim], (int, float)):
                            scores[dim].append(record[dim])
                except:
                    continue  # 遇到格式问题跳过

        avg_scores = {dim: round(sum(scores[dim])/len(scores[dim]), 2) if scores[dim] else 0 for dim in DIMENSIONS}
        avg_scores["模型"] = model_name
        result.append(avg_scores)

    return pd.DataFrame(result).set_index("模型")


def print_table_report(df: pd.DataFrame):
    print("📊 模型评分汇总表（五维度 + 总分）")
    print("=" * 55)
    print(df.to_markdown())
    print("\n🔍 推荐展示方式：五维雷达图 + 排名柱状图（见下）")


def save_table_as_csv(df: pd.DataFrame, path="model_scores.csv"):
    df.to_csv(path, encoding='utf-8-sig')
    print(f"✅ 成功保存为 CSV 文件：{path}")


if __name__ == "__main__":
    df = summarize_model_scores(EVAL_DIR)
    df = df.sort_values("总分", ascending=False)
    print_table_report(df)
    save_table_as_csv(df, "model_eval_summary.csv")

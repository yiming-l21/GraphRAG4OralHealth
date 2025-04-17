import os
import json
import glob
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np

# Use default English-friendly font
mpl.rcParams['font.sans-serif'] = ['DejaVu Sans']
mpl.rcParams['axes.unicode_minus'] = False

# ========= Part 1: Score summary =========
EVAL_DIR = "eval"
DIMENSIONS = ["Accuracy", "Completeness", "Safety", "Understanding", "Logic", "Total"]

def summarize_model_scores(eval_dir):
    result = []
    for file_path in glob.glob(os.path.join(eval_dir, "*_eval.json")):
        model_name = os.path.basename(file_path).replace("_eval.json", "")
        scores = {dim: [] for dim in DIMENSIONS}

        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    record = json.loads(line)
                    mapping = {
                        "正确性": "Accuracy",
                        "完整性": "Completeness",
                        "安全性": "Safety",
                        "理解力": "Understanding",
                        "逻辑性": "Logic",
                        "总分": "Total"
                    }
                    for zh, en in mapping.items():
                        if zh in record and isinstance(record[zh], (int, float)):
                            scores[en].append(record[zh])
                except:
                    continue

        avg_scores = {dim: round(sum(scores[dim]) / len(scores[dim]), 2) if scores[dim] else 0 for dim in DIMENSIONS}
        avg_scores["Model"] = model_name
        result.append(avg_scores)

    return pd.DataFrame(result).set_index("Model")


def save_table_as_csv(df: pd.DataFrame, path="model_eval_summary.csv"):
    df.to_csv(path, encoding='utf-8-sig')
    print(f"✅ Saved as CSV: {path}")


# ========= Part 2: Plotting =========
SCORE_FILE = "model_eval_summary.csv"
OUT_DIR = "plots"
os.makedirs(OUT_DIR, exist_ok=True)

def plot_bar_chart(df: pd.DataFrame):
    df = df.sort_values("Total", ascending=False)
    plt.figure(figsize=(10, 5))
    bars = plt.bar(df.index, df["Total"], color='skyblue')
    plt.ylabel("Total Score (out of 10)")
    plt.title("Model Overall Scores")
    plt.ylim(0, 10)
    plt.xticks(rotation=30)
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 0.1, round(yval, 2), ha='center')
    plt.tight_layout()
    plt.savefig(f"{OUT_DIR}/bar_chart_scores_en.png")
    plt.close()
    print("✅ Saved: bar_chart_scores_en.png")

def plot_radar_chart(df: pd.DataFrame):
    labels = ["Accuracy", "Completeness", "Safety", "Understanding", "Logic"]
    num_vars = len(labels)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    for i, row in df.iterrows():
        values = [row[label] for label in labels]
        values += values[:1]
        ax.plot(angles, values, label=i)
        ax.fill(angles, values, alpha=0.1)

    ax.set_title("Model Performance Radar", size=14)
    ax.set_ylim(0, 2)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.05))
    plt.tight_layout()
    plt.savefig(f"{OUT_DIR}/radar_chart_scores_en.png")
    plt.close()
    print("✅ Saved: radar_chart_scores_en.png")


# ========= Main =========
if __name__ == "__main__":
    df = summarize_model_scores(EVAL_DIR)
    save_table_as_csv(df, SCORE_FILE)
    plot_bar_chart(df)
    plot_radar_chart(df)

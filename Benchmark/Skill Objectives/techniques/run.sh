#!/bin/bash

# 设置评测脚本路径和数据路径
EVAL_SCRIPT="eval_technique.py"
ANSWER_DIR="answers"
REF_FILE="basic_techniques.json"
OUT_DIR="eval"

# 设置 dashscope API key（可选，若已 export 则跳过）
export DASHSCOPE_API_KEY="sk-969f4200d53442a2a1733d1c0b1fb330"

# 创建输出目录（如果不存在）
mkdir -p "$OUT_DIR"

# 失败日志记录
FAILED_LOG="$OUT_DIR/eval_failed.log"
echo "" > "$FAILED_LOG"  # 清空旧记录

# 遍历所有模型答案文件
for answer_file in "$ANSWER_DIR"/*_answers.json; do
    filename=$(basename -- "$answer_file")
    model_name="${filename%_answers.json}"
    output_file="$OUT_DIR/${model_name}_eval.json"

    if [ -f "$output_file" ]; then
        echo "⏩ 跳过 $model_name，评分结果已存在：$output_file"
        continue
    fi

    echo "🔍 正在评测模型：$model_name"
    python "$EVAL_SCRIPT" "$answer_file" "$REF_FILE" "$output_file" --max_qps 1

    if [ -f "$output_file" ]; then
        echo "✅ $model_name 评测完成，结果保存至 $output_file"
    else
        echo "❌ $model_name 评测失败！未生成 $output_file"
        echo "$model_name" >> "$FAILED_LOG"
    fi
    echo "--------------------------------------"
done

echo "🎉 所有模型评测任务完成（跳过已完成）。结果目录：$OUT_DIR/"

# 输出失败列表
if [ -s "$FAILED_LOG" ]; then
    echo "⚠️ 以下模型评分失败，请检查日志或重试："
    cat "$FAILED_LOG"
else
    echo "✅ 所有模型评测均成功。"
fi

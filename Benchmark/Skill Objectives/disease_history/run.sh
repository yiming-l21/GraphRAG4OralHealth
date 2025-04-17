#!/bin/bash

# 设置评测脚本路径和数据路径
EVAL_SCRIPT="eval_history.py"
ANSWER_DIR="answers"
REF_FILE="clinical_reasoning_cases.json"
OUT_DIR="eval"

# 设置 dashscope API key（可选，若已 export 则跳过）
export DASHSCOPE_API_KEY="sk-969f4200d53442a2a1733d1c0b1fb330"

# 创建输出目录（如果不存在）
mkdir -p "$OUT_DIR"

# 遍历所有模型答案文件
for answer_file in "$ANSWER_DIR"/*_answers.json; do
    filename=$(basename -- "$answer_file")
    model_name="${filename%_answers.json}"
    output_file="$OUT_DIR/${model_name}_eval.json"

    # 判断是否已存在输出文件
    if [ -f "$output_file" ]; then
        echo "⏩ 跳过 $model_name，评测结果已存在：$output_file"
        continue
    fi

    echo "🔍 正在评测模型：$model_name"
    python "$EVAL_SCRIPT" "$answer_file" "$REF_FILE" "$output_file" --max_qps 1

    # 检查是否成功输出
    if [ -f "$output_file" ]; then
        echo "✅ $model_name 评测完成，结果保存至 $output_file"
    else
        echo "❌ $model_name 评测失败！未生成 $output_file"
    fi
    echo "--------------------------------------"
done

echo "🎉 所有模型评测任务完成（跳过已完成的评测）。结果目录：$OUT_DIR/"

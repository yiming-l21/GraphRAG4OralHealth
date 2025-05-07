#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
llm_dental_eval_history.py
~~~~~~~~~~~~~~~~~~~~~~~~~~
使用 Qwen-Plus 对口腔病史类主观题进行五维度评分，并增加临时文件机制。

CLI:
    python llm_dental_eval_history.py 模型答案.json 参考答案.json 输出结果.jsonl --max_qps 1
"""
import argparse
import json
import os
import time
import re
from pathlib import Path
from dashscope import Generation

# ========= 1. 中文评分 Rubric 与 Prompt =========
RUBRIC = """
你将对一个口腔病史类问答进行结构化评分。请使用以下五个维度对模型答案进行 0～2 分评价，并输出结构化 JSON 分数（满分 10 分）。

【五维度评分标准详解】

1. 正确性（是否识别正确诊断 + 正确术语）
- 2分：明确识别出主要诊断/鉴别诊断，疾病名称准确、医学术语规范。
- 1分：部分诊断正确，或术语略有偏差但方向正确。
- 0分：诊断错误或术语严重混淆，可能误导临床判断。

  示例：
  ✔️ 正确写：慢性根尖周炎、牙髓坏死。
  ❌ 错误写：牙周脓肿（误判病因）→ 0分

2. 完整性（是否覆盖所有应答点与推理依据）
- 2分：诊断依据、影像描述、体征、治疗流程、预防建议等均被涵盖。
- 1分：主干齐全但遗漏了如瘘管、X线透影、预防建议等重要信息。
- 0分：严重遗漏多数核心要点，仅作片段回答。

  示例：
  ❌ 未提及瘘管形成或X线透影特征 → 1分

3. 安全性（是否存在不当或危险建议）
- 2分：所有治疗建议合理、循证、无过度或缺失关键操作。
- 1分：存在轻微表述模糊，但基本无风险。
- 0分：推荐不合理操作（如直接修复而未行根管），可能带来伤害。

4. 理解力（是否逐题作答 + 不跑题）
- 2分：分清各问点，逐项清晰作答；无混淆、无答非所问。
- 1分：个别问题未完全回应或边界模糊。
- 0分：完全未理解问题意图，作答偏离全部方向。

5. 逻辑性（是否符合医学推理链 + 条理清晰）
- 2分：推理过程合理，结构流畅，因果清晰，无矛盾。
- 1分：结构略乱，但能看出合理链条。
- 0分：出现明显矛盾或思路跳跃，如前后不一致。

---

请你阅读以下【病史】【问题】【参考答案】【模型答案】，按照上述五维度评分标准进行评价。

输出格式必须严格为如下 JSON：
{
  "正确性": ?,
  "完整性": ?,
  "安全性": ?,
  "理解力": ?,
  "逻辑性": ?,
  "总分": ?,
  "点评": "请写出简明的评价，包括得分理由与主要优点/缺点总结"
}
"""

PROMPT_TMPL = """
你是一位资深口腔主治医生，请根据以下内容对模型答案进行结构化评分。

【题目ID】
{qid}

【病史】
{history}

【问题】
{questions}

【参考答案】
{ref_answer}

【模型答案】
{cand_answer}

请基于前述“评分标准”进行 0-2 分评分，并写出点评。
"""

# ========= 2. 工具函数 =========
def qwen_call(prompt: str, api_key: str, qps_delay=1.0):
    time.sleep(qps_delay)
    rsp = Generation.call(
        api_key=api_key,
        model="qwen-plus",
        messages=[
            {"role": "system", "content": "你是一个医学知识问答评分助手。"},
            {"role": "user", "content": prompt}
        ],
        result_format="message"
    )
    return rsp["output"]["choices"][0]["message"]["content"]

def safe_parse_json(content: str):
    try:
        return json.loads(content)
    except:
        pass
    cleaned = re.sub(r"^[^\{]*", "", content, count=1)
    match = re.search(r"\{.*?\}", cleaned, flags=re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except:
            return {"解析错误": "JSON 提取失败", "原始输出": content}
    else:
        return {"解析错误": "未找到 JSON", "原始输出": content}

def build_prompt(qid, history, questions, ref_ans, model_ans):
    q_str = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])
    ref_str = "\n".join([f"{i+1}. {a.strip()}" for i, a in enumerate(ref_ans)])
    model_str = "\n".join([f"{i+1}. {a.strip()}" for i, a in enumerate(model_ans)])
    return PROMPT_TMPL.format(
        qid=qid,
        history=history.strip(),
        questions=q_str,
        ref_answer=ref_str,
        cand_answer=model_str
    )

def grade_one(qid, case, ref_case, api_key, qps_delay):
    prompt = build_prompt(qid, case["病史"], case["问题"], ref_case["答案"], case["答案"])
    content = qwen_call(RUBRIC + prompt, api_key, qps_delay)
    score = safe_parse_json(content)
    print(f"⚠️ 评分结果：{score}")
    return {
        "qid": qid,
        "病史": case["病史"],
        "问题": case["问题"],
        "参考答案": ref_case["答案"],
        "模型答案": case["答案"],
        **score
    }

# ========= 3. 主程序入口 =========
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("model_file", help="模型输出 JSON 文件（病史结构）")
    parser.add_argument("ref_file", help="参考答案 JSON 文件（病史结构）")
    parser.add_argument("output_file", help="输出 JSONL")
    parser.add_argument("--max_qps", type=float, default=1.0)
    args = parser.parse_args()

    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("请设置环境变量：DASHSCOPE_API_KEY")

    with open(args.model_file, "r", encoding="utf-8") as f:
        model_cases = json.load(f)
    with open(args.ref_file, "r", encoding="utf-8") as f:
        ref_cases = json.load(f)

    # 构建病史->参考答案映射
    ref_map = {c["病史"].strip(): c for c in ref_cases}

    results = []
    temp_file = Path(args.output_file).with_suffix(".tmp.jsonl")  # 临时文件路径

    try:
        # 恢复进度
        if temp_file.exists():
            print(f"⚠️ 发现临时文件 {temp_file}，尝试恢复进度...")
            with open(temp_file, "r", encoding="utf-8") as f:
                for line in f:
                    results.append(json.loads(line))
            print(f"✅ 已从临时文件恢复 {len(results)} 条记录。")

        for idx, case in enumerate(model_cases, start=1):
            history = case["病史"].strip()
            if history not in ref_map:
                print(f"❌ 第{idx}题：未找到匹配的参考答案，跳过")
                continue
            ref_case = ref_map[history]

            try:
                result = grade_one(f"Case{idx}", case, ref_case, api_key, 1 / args.max_qps)
                results.append(result)
                print(f"✅ Case{idx} 完成，总分: {result.get('总分', '?')}")
            except Exception as e:
                print(f"⚠️ 评分失败：题目 {case['病史'][:20]}... 错误信息：{e}")
                # 将当前结果保存到临时文件
                with open(temp_file, "w", encoding="utf-8") as f:
                    for r in results:
                        f.write(json.dumps(r, ensure_ascii=False) + "\n")
                print(f"⚠️ 已将当前进度保存到临时文件 {temp_file}。")
                raise  # 继续抛出异常，终止程序

            # 定期保存到临时文件
            if idx % 10 == 0:  # 每处理 10 道题保存一次
                with open(temp_file, "w", encoding="utf-8") as f:
                    for r in results:
                        f.write(json.dumps(r, ensure_ascii=False) + "\n")
                print(f"✅ 已将当前进度保存到临时文件 {temp_file}。")

    finally:
        # 程序结束时清理临时文件并写入最终结果
        if results:
            with open(args.output_file, "w", encoding="utf-8") as f:
                for r in results:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
            print(f"\n✅ 共评测 {len(results)} 题，结果已写入 {args.output_file}")

            if temp_file.exists():
                temp_file.unlink()  # 删除临时文件
                print(f"✅ 已删除临时文件 {temp_file}。")
        else:
            print("⚠️ 未生成任何结果。")

if __name__ == "__main__":
    main()
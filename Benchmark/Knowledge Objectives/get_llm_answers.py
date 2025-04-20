import json
import os
import glob
from inference_wrappers import (
    deepseek_inference, XunfeiSpark_inference, QWenplus_inference,
    ChatGLM_inference, GPT4_inference, GPT3_inference, QWen25_7b_inference,
    deepseek_r1_inference, DentalMind_o1_inference, DentalMind_base_inference,DentalMind_graph_inference
)

# ------------ 模型配置区 ------------
model_config_dict = {
    "deepseek": {"model": deepseek_inference},
    "XunfeiSpark": {"model": XunfeiSpark_inference},
    "QWenplus": {"model": QWenplus_inference},
    "ChatGLM": {"model": ChatGLM_inference},
    "GPT4turbo": {"model": GPT4_inference},
    "GPT3turbo": {"model": GPT3_inference},
    "QWen25_7b": {"model": QWen25_7b_inference},
    "deepseek_r1": {"model": deepseek_r1_inference},
    "DentalMind_o1": {"model": DentalMind_o1_inference},
    "DentalMind_base": {"model": DentalMind_base_inference},
    "DentalMind_graph":{"model": DentalMind_graph_inference}
}

# 选择模型名称
model_name = "DentalMind_graph"
model_inference = model_config_dict[model_name]["model"]

# 保存路径
save_dir = "/home/lym/GraphRAG4OralHealth/Benchmark/Knowledge Objectives/Answer"

# ------------ 结果保存函数 ------------
def save_result(result_dict, topic, json_path):
    file_name = os.path.basename(json_path)
    model_folder = os.path.join(save_dir, model_name)
    os.makedirs(model_folder, exist_ok=True)
    topic_folder = os.path.join(model_folder, topic)
    os.makedirs(topic_folder, exist_ok=True)
    save_path = os.path.join(topic_folder, f"{model_name}_{topic}_{file_name}_answers.json")
    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(result_dict, f, ensure_ascii=False, indent=4)

# ------------ 主推理函数（单线程） ------------
from tqdm import tqdm

async def get_answer(directory_path, model_inference, topic):
    async def process_question(ques_text):
        response_content, reasoning_content = await model_inference(ques_text)
        print(ques_text)
        print(response_content)
        return response_content, reasoning_content
    all_json_paths = glob.glob(os.path.join(directory_path, '*.json'))
    for json_path in all_json_paths:
        result_list=[]
        print(f"\n📄 正在处理文件: {json_path}")
        with open(json_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)

        # 独立题
        for question in json_data.get('独立题', []):
            ques_text = (
                "下面我会给你一个医学相关的问题，请你根据医学知识进行回答。"
                "一个题目有5个选项，请选出最合适的选项，并输出选项前字母。"
                "注意只需要输出选项前字母，不需要输出任何其他内容。\n"
                f"题目:\n{question.get('题干', question.get('题目'))}\n选项:\n{question['选项']}"
            )
            res_content, res_reasoning =await process_question(ques_text)
            result_list.append({
                "题目": question.get('题干', question.get('题目')),
                "选项": question['选项'],
                "gt": question['答案'],
                "prediction": res_content,
                "reason": res_reasoning
            })

        # 共用题干题
        for question in json_data.get('共用题干题', []):
            for idx in range(len(question['答案'])):
                ques_text = (
                    "下面我会给你一个医学相关的问题，请你根据医学知识进行回答。"
                    "一个题目有5个选项，请选出最合适的选项，并输出选项前字母。"
                    "注意只需要输出选项前字母，不需要输出任何其他内容。\n"
                    f"题目:\n{question['共用题干']}\n{question['题干'][idx]}\n选项:\n{question['选项'][idx]}"
                )
                res_content, res_reasoning = process_question(ques_text)
                result_list.append({
                    "题目": question['题干'][idx],
                    "选项": question['选项'][idx],
                    "gt": question['答案'][idx],
                    "prediction": res_content,
                    "reason": res_reasoning
                })

        # 共用备选题
        for question in json_data.get('共用备选题', []):
            for idx in range(len(question['答案'])):
                ques_text = (
                    "下面我会给你一个医学相关的问题，请你根据医学知识进行回答。"
                    "一个题目有5个选项，请选出最合适的选项，并输出选项前字母。"
                    "注意只需要输出选项前字母，不需要输出任何其他内容。\n"
                    f"题目:\n{question['题干'][idx]}\n选项:\n{question['选项']}"
                )
                res_content, res_reasoning = process_question(ques_text)
                result_list.append({
                    "题目": question['题干'][idx],
                    "选项": question['选项'],
                    "gt": question['答案'][idx],
                    "prediction": res_content,
                    "reason": res_reasoning
                })
        print(result_list[:3])
        save_result(result_list, topic, json_path)



import os
import asyncio  # 别忘了引入 asyncio

async def main():
    topic_list = ["MedicalHumanity", "Clinical", "Dentistry", "Medical"]
    directory_path = "/home/lym/GraphRAG4OralHealth/Benchmark/Knowledge Objectives/"

    for topic in topic_list:
        path = os.path.join(directory_path, topic)
        await get_answer(path, model_inference, topic)

    print("✅ 所有题目处理完毕！")

# ------------ 运行入口 ------------
if __name__ == "__main__":
    asyncio.run(main())


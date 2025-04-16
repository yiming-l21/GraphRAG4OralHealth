import json
import os
import glob
from concurrent.futures import ThreadPoolExecutor, as_completed
from inference_wrappers import deepseek_inference, XunfeiSpark_inference, QWenplus_inference, ChatGLM_inference, GPT4_inference, GPT3_inference, QWen25_7b_inference, deepseek_r1_inference, DentalMind_o1_inference, DentalMind_base_inference

model_config_dict = {
    "deepseek": {
        "model": deepseek_inference
    },
    "XunfeiSpark": {
        "model": XunfeiSpark_inference
    },
    "QWenplus": {
        "model": QWenplus_inference
    },
    "ChatGLM": {
        "model": ChatGLM_inference
    },
    "GPT4turbo": {
        "model": GPT4_inference
    },
    "GPT3turbo": {
        "model": GPT3_inference
    },
    "QWen25_7b": {
        "model": QWen25_7b_inference
    },
    "deepseek_r1": {
        "model": deepseek_r1_inference
    },
    "DentalMind_o1": {
        "model": DentalMind_o1_inference
    },
    "DentalMind_base": {
        "model": DentalMind_base_inference
    }
}

model_name = "DentalMind_o1"
model_inference = model_config_dict[model_name]["model"]
save_dir = "/home/lym/GraphRAG4OralHealth/Benchmark/Knowledge Objectives/Answer"


def get_answer(directory_path, model_inference, topic, executor):
    def process_question(ques_text):
        print(ques_text)
        # 这里调用模型进行推理
        response_content, reasoning_content = model_inference(ques_text)  # 获取response_content和reasoning_content
        print(f"Response: {response_content}")
        print(f"Reasoning: {reasoning_content}")
        return response_content, reasoning_content

    result_list = []

    for json_path in glob.glob(os.path.join(directory_path, '*.json')):
        if topic == "Dentistry":
            if "口腔解剖生理学" in json_path or "口腔预防医学" in json_path or "口腔颌面外科学" in json_path or "口腔黏膜病医学" in json_path:
                continue

        print(f"Processing {json_path}")
        with open(json_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)

        # Create a list of futures for parallel execution
        future_results = []

        for question in json_data.get('独立题', []):
            ques_text = (
                "下面我会给你一个医学相关的问题，请你根据医学知识进行回答。"
                "一个题目有5个选项，请选出最合适的选项，并输出选项前字母。"
                "注意只需要输出选项前字母，不需要输出任何其他内容。\n"
                f"题目:\n{question['题干'] if '题干' in question.keys() else question['题目']}\n选项:\n{question['选项']}"
            )
            future = executor.submit(process_question, ques_text)
            future_results.append((future, question))

        for question in json_data.get('共用题干题', []):
            for idx in range(len(question['答案'])):
                ques_text = (
                    "下面我会给你一个医学相关的问题，请你根据医学知识进行回答。"
                    "一个题目有5个选项，请选出最合适的选项，并输出选项前字母。"
                    "注意只需要输出选项前字母，不需要输出任何其他内容。\n"
                    f"题目:\n{question['共用题干']}\n{question['题干'][idx]}\n选项:\n{question['选项'][idx]}"
                )
                future = executor.submit(process_question, ques_text)
                future_results.append((future, question))

        for question in json_data.get('共用备选题', []):
            for idx in range(len(question['答案'])):
                ques_text = (
                    "下面我会给你一个医学相关的问题，请你根据医学知识进行回答。"
                    "一个题目有5个选项，请选出最合适的选项，并输出选项前字母。"
                    "注意只需要输出选项前字母，不需要输出任何其他内容。\n"
                    f"题目:\n{question['题干'][idx]}\n选项:\n{question['选项']}"
                )
                future = executor.submit(process_question, ques_text)
                future_results.append((future, question))

        # Collect results in the correct order
        for future, question in future_results:
            res_content, res_reasoning = future.result()  # 获取response_content和reasoning_content
            item_dict = {
                "题目": question['题干'] if '题干' in question.keys() else question['题目'],
                "选项": question['选项'],
                "gt": question['答案'],
                "prediction": res_content,  # 使用response_content作为预测结果
                "reason": res_reasoning  # 添加reasoning_content
            }
            result_list.append(item_dict)

        # Save results after processing all questions in a JSON file
        save_result(result_list, topic, json_path)

    return


def save_result(result_dict, topic, json_path):
    file_name = os.path.basename(json_path)
    model_folder = "/home/lym/GraphRAG4OralHealth/Benchmark/Knowledge Objectives/Answer/" + model_name
    os.makedirs(model_folder, exist_ok=True)
    topic_folder = model_folder + "/" + topic
    os.makedirs(topic_folder, exist_ok=True)
    save_path = f"{topic_folder}/{model_name}_{topic}_{file_name}_answers.json"
    with open(save_path, 'a') as f:
        json.dump(result_dict, f, ensure_ascii=False, indent=4)


topic_list = ["MedicalHumanity", "Clinical", "Dentistry", "Medical"]
directory_path = '/home/lym/GraphRAG4OralHealth/Benchmark/Knowledge Objectives/'

# Use ThreadPoolExecutor to process multiple files in parallel
with ThreadPoolExecutor(max_workers=10) as executor:
    for topic in topic_list:
        path = directory_path + topic
        get_answer(path, model_inference, topic, executor)

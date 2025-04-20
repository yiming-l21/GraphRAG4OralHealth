import json
import asyncio
from inference_wrappers import (
    deepseek_inference, XunfeiSpark_inference, QWenplus_inference,
    ChatGLM_inference, GPT4_inference, GPT3_inference, QWen25_7b_inference,
    deepseek_r1_inference, DentalMind_o1_inference, DentalMind_base_inference,
    QWenMax_inference, DentalMind_graph_inference
)

# 模型映射表
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
    "QWenMax": {"model": QWenMax_inference},
    "DentalMind_graph": {"model": DentalMind_graph_inference},
}

# 主函数
async def main():
    json_file = "/home/lym/GraphRAG4OralHealth/Benchmark/Skill Objectives/techniques/basic_techniques.json"
    save_dir = "/home/lym/GraphRAG4OralHealth/Benchmark/Skill Objectives/techniques/answers"
    model_name = "DentalMind_graph"

    print(f"模型名称: {model_name}")
    model_inference = model_config_dict[model_name]["model"]
    save_path = f"{save_dir}/{model_name}_answers.json"

    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        print(f"数据集大小: {len(data)}")

        question_list = []
        answer_list = []
        history_list = []
        graph_list = []
        count = 0

        # 这段是用于处理另一个数据集的逻辑，请保留
        for item in data:
            question = item["Q"]
            question_list.append(question)
            prompt = "请你用精简准确的表达回答以下口腔医学问题:\n" + question
            answer, graph = await model_inference(prompt)
            answer_list.append(answer)
            graph_list.append(graph)
            print(f"问题: {question}")
            print(f"答案: {answer}")

        # # 当前数据处理逻辑（包含病史与图谱）
        # for item in data:
        #     history = item["病史"]
        #     ques_pair = item["问题"]
        #     history_list.append(history)

        #     prompt = (
        #         "请你用精简准确的表达回答以下口腔医学问题:\n"
        #         f"该病人的病史为:\n{history}\n问题为:\n{ques_pair}\n\n"
        #         "要求：输出三个题目答案，格式为：\n答案1. \n答案2. \n答案3.请严格按照格式输出"
        #     )

        #     # 使用 await 调用异步模型推理
        #     answer, graph = await model_inference(prompt)
        #     count += 1
        #     print(f"问题对: {count}")

        #     # 分割答案
        #     a_list = answer.split("答案")
        #     if len(a_list) >= 4:
        #         answer1 = a_list[1].strip()
        #         answer2 = a_list[2].strip()
        #         answer3 = a_list[3].strip()
        #     else:
        #         answer1 = answer2 = answer3 = "格式错误"

        #     print(f"答案1: {answer1}")
        #     print(f"答案2: {answer2}")
        #     print(f"答案3: {answer3}")

        #     question_list.append(ques_pair)
        #     answer_list.append([answer1, answer2, answer3])
        #     graph_list.append(graph)

        # result_list = [
        #     {"病史": h, "问题": q, "答案": a, "图谱": g}
        #     for h, q, a, g in zip(history_list, question_list, answer_list, graph_list)
        # ]
        result_list=[{"Q":q,"A":a,"图谱": g} for q,a,g in zip(question_list,answer_list, graph_list)]
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(result_list, f, ensure_ascii=False, indent=4)

# 启动异步主程序
if __name__ == "__main__":
    asyncio.run(main())

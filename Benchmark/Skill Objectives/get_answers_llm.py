import json
from inference_wrappers import deepseek_inference,XunfeiSpark_inference,QWenplus_inference,ChatGLM_inference,GPT4_inference,GPT3_inference,QWen25_7b_inference,deepseek_r1_inference,DentalMind_o1_inference,DentalMind_base_inference,QWenMax_inference
model_config_dict={
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
    },
    "QWenMax": {
        "model": QWenMax_inference
    },
}
json_file="/home/lym/GraphRAG4OralHealth/Benchmark/Skill Objectives/disease_history/clinical_reasoning_cases.json"
save_dir="/home/lym/GraphRAG4OralHealth/Benchmark/Skill Objectives/disease_history/answers"
model_name="QWenMax"
print(f"模型名称: {model_name}")
model_inference=model_config_dict[model_name]["model"]
save_path=f"{save_dir}/{model_name}_answers.json"
with open(json_file, 'r', encoding='utf-8') as f:
    data= json.load(f)
    print(f"数据集大小: {len(data)}")
    question_list=[]
    answer_list=[]
    history_list=[]
    # for item in data:
    #     question=item["Q"]
    #     question_list.append(question)
    #     prompt="请你用精简准确的表达回答以下口腔医学问题:\n"+question
    #     answer=model_inference(prompt)
    #     answer_list.append(answer)
    #     print(f"问题: {question}")
    #     print(f"答案: {answer}")
    count=0
    for item in data:
        history=item["病史"]
        history_list.append(history)
        ques_pair=item["问题"]
        prompt="请你用精简准确的表达回答以下口腔医学问题:\n该病人的病史为:\n"+str(history)+"问题为:\n"+str(ques_pair)+"\n\n要求：输出三个题目答案，格式为：\n答案1. \n答案2. \n答案3.请严格按照格式输出"
        #提取答案
        answer=model_inference(prompt)
        count+=1
        print(f"问题对: {count}")
        #将答案分割成列表,按照题目1、题目2、题目3的格式
        a_list=answer.split("答案")
        answer1=a_list[1].strip()
        answer2=a_list[2].strip()
        answer3=a_list[3].strip()
        print(f"答案1: {answer1}")
        print(f"答案2: {answer2}")
        print(f"答案3: {answer3}")
        question_list.append(ques_pair)
        answer_list.append([answer1,answer2,answer3])
        
#result_list=[{"Q":q,"A":a} for q,a in zip(question_list,answer_list)]
result_list=[{"病史":h,"问题":q,"答案":a} for h,q,a in zip(history_list,question_list,answer_list)]
with open(save_path, 'w', encoding='utf-8') as f:
    json.dump(result_list, f, ensure_ascii=False, indent=4)
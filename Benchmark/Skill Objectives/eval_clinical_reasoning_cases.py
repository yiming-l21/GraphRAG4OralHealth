import os
import json
import glob
from typing import List, Dict, Callable
import json
import os
import glob
import openai
from zhipuai import ZhipuAI #chatglm
import dashscope #通义千问
import requests
import _thread as thread
import os
import time
import base64
import datetime
import hashlib
import hmac
import json
from urllib.parse import urlparse
import ssl
from datetime import datetime
from time import mktime
from urllib.parse import urlencode
from wsgiref.handlers import format_date_time
import websocket
import openpyxl
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from modelscope import AutoModelForCausalLM, AutoTokenizer
import re
dashscope.api_key = "sk-969f4200d53442a2a1733d1c0b1fb330"
# 设置 API 密钥
openai.api_key = 'openai_api_key'
# 使用目录路径
# model_name = "/home/lym/.cache/modelscope/hub/Qwen/Qwen2.5-7B-Instruct"
# model = AutoModelForCausalLM.from_pretrained(
#     model_name,
#     torch_dtype="auto",
#     device_map="auto"
# )
# tokenizer = AutoTokenizer.from_pretrained(model_name)
# model_name = "/home/lym/3l-dentalmind-backend/lllchat/model_files/deepthinking_model"
# model = AutoModelForCausalLM.from_pretrained(
#     model_name,
#     torch_dtype="auto",
#     device_map="auto"
# )
# tokenizer = AutoTokenizer.from_pretrained(model_name)
def model_judge1(prompt):
    #实现GPT4的推理接口，输入用户的prompt，返回模型生成的文本信息
    response = openai.ChatCompletion.create(
        model="gpt-4",  # 使用聊天模型
        messages=[
            {"role": "system", "content": "你是一个医学知识问答机器人。"},  # 系统提示
            {"role": "user", "content": prompt}
        ],
        max_tokens=50,  # 根据需要调整
        temperature=0.7  # 控制输出的随机性
    )
    # 提取模型生成的文本
    return response.choices[0].message['content'].strip()

def model_judge(prompt: str):
    try:
        response = dashscope.Generation.call(
            model="qwen-max",
            prompt=prompt,
            result_format='message'
        )
        content = response["output"]["choices"][0]["message"]["content"]
        return content
    except Exception as e:
        print(f"❌ Judge失败: {e}")
        return ""


def DentalMind_o1_inference(prompt):
    '''实现DentalMind模型的推理接口，输入用户的prompt，返回模型生成的文本信息'''
    messages = [
        {"role": "system", "content": "你是一个医学知识问答机器人。"},
        {"role": "user", "content": prompt}
    ]
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )
    model_inputs = tokenizer([text], return_tensors="pt").to(model.device)
    generated_ids = model.generate(
        **model_inputs,
        max_new_tokens=2048
    )
    generated_ids = [
        output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
    ]
    response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
    match = re.search(r"<content>(.*?)</content>", response, flags=re.DOTALL)
    print(response)
    if match:
        response_content = match.group(1).strip()
    else:
        response_content = "No content found"
    
    print("Response content:", response_content)
    return response_content.strip()
#不同模型的推理接口，输入问题，返回答案
def QWen25_7b_inference(prompt):
    messages = [
        {"role": "system", "content": "你是一个医学知识问答机器人。"},
        {"role": "user", "content": prompt}
    ]
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )
    model_inputs = tokenizer([text], return_tensors="pt").to(model.device)
    generated_ids = model.generate(
        **model_inputs,
        max_new_tokens=512
    )
    generated_ids = [
        output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
    ]
    response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
    # 提取模型生成的文本
    return response.strip()
def baidu01_inference(prompt):
    '''实现百度灵医大模型的推理接口，输入用户的prompt，返回模型生成的文本信息'''
    #TODO
    pass
def GPT3_inference(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # 使用聊天模型
        messages=[
            {"role": "system", "content": "你是一个医学知识问答机器人。"},  # 系统提示
            {"role": "user", "content": prompt}
        ],
        max_tokens=50,  # 根据需要调整
        temperature=0.7  # 控制输出的随机性
    )
    # 提取模型生成的文本
    return response.choices[0].message['content'].strip()
def GPT4_inference(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",  # 使用聊天模型
        messages=[
            {"role": "system", "content": "你是一个医学知识问答机器人。"},  # 系统提示
            {"role": "user", "content": prompt}
        ],
        max_tokens=50,  # 根据需要调整
        temperature=0.7  # 控制输出的随机性
    )
    # 提取模型生成的文本
    return response.choices[0].message['content'].strip()
def ChatGLM_inference(prompt):
    client=ZhipuAI(api_key="28d2e1f70dc3405890b8a6a5178d4f6d.C25okw1T7X0cWpG2")
    response = client.chat.completions.create(
        model="glm-4",  # 使用聊天模型
        messages=[
            {"role": "system", "content": "你是一个医学知识问答机器人。"},  # 系统提示
            {"role": "user", "content": prompt}
        ],
        max_tokens=1000,  # 根据需要调整
        temperature=0.7  # 控制输出的随机性
    )
    # 提取模型生成的文本
    return dict(response.choices[0].message)["content"].strip()
def QWenplus_inference(prompt):
    messages=[{"role": "system", "content": "你是一个医学知识问答机器人。"},{"role": "user", "content": prompt}]
    response = dashscope.Generation.call(
    # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
    api_key="qwen_api_key",
    model="qwen-plus", # 模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
    messages=messages,
    result_format='message'
    )
    return response['output']['choices'][0]['message']['content'].strip()
def XunfeiSpark_inference(prompt):
    appid="6e57c0c0"
    api_secret="YTA3MzA5NzhjMjc3ZTVjMGYxZGYxN2Q2"
    api_key="f2838d0638a3b1e94f23ed1bf4346853"
    gpt_url = "wss://spark-api.xf-yun.com/v3.1/chat"
    domain = "generalv3"
    
    result = []

    def create_url():
        host = urlparse(gpt_url).netloc
        path = urlparse(gpt_url).path
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))
        signature_origin = f"host: {host}\ndate: {date}\nGET {path} HTTP/1.1"
        signature_sha = hmac.new(api_secret.encode('utf-8'), signature_origin.encode('utf-8'), digestmod=hashlib.sha256).digest()
        signature_sha_base64 = base64.b64encode(signature_sha).decode('utf-8')
        authorization_origin = f'api_key="{api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode('utf-8')
        v = {"authorization": authorization, "date": date, "host": host}
        return gpt_url + '?' + urlencode(v)

    def on_error(ws, error):
        pass

    def on_close(ws):
        print("### closed ###")

    def on_open(ws):
        thread.start_new_thread(run, (ws,))

    def run(ws, *args):
        data = json.dumps(gen_params())
        ws.send(data)

    def on_message(ws, message):
        data = json.loads(message)
        code = data['header']['code']
        if code != 0:
            print(f'请求错误: {code}, {data}')
            ws.close()
        else:
            choices = data["payload"]["choices"]
            status = choices["status"]
            content = choices["text"][0]["content"]
            result.append(content)
            if status == 2:
                ws.close()

    def gen_params():
        return {
            "header": {
                "app_id": appid,
                "uid": "1234",         
            },
            "parameter": {
                "chat": {
                    "domain": domain,
                    "temperature": 0.5,
                    "max_tokens": 4096,
                    "auditing": "default",
                }
            },
            "payload": {
                "message": {
                    "text": [{"role": "user", "content": prompt}]
                }
            }
        }

    websocket.enableTrace(False)
    wsUrl = create_url()
    ws = websocket.WebSocketApp(wsUrl, on_message=on_message, on_error=on_error, on_close=on_close, on_open=on_open)
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
    
    return ''.join(result)
def deepseek_inference(prompt):
    import os
    from openai import OpenAI
    client = OpenAI(
        # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
        api_key="sk-969f4200d53442a2a1733d1c0b1fb330",  # 如何获取API Key：https://help.aliyun.com/zh/model-studio/developer-reference/get-api-key
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )
    completion = client.chat.completions.create(
        model="deepseek-v3",  # 此处以 deepseek-r1 为例，可按需更换模型名称。
        messages=[
            {'role': 'user', 'content': prompt}
        ]
    )
    return completion.choices[0].message.content

# 根据评分标准打分
def score_subjective_answer_with_model(model_answer: str, reference_answer: str, rubric: str, model_eval: Callable[[str], str]) -> int:
    prompt = (
        "你是医学考试阅卷专家，请根据评分细则对考生作答进行评分。\n"
        "【评分细则】\n"
        f"{rubric.strip()}\n\n"
        "【参考答案】\n"
        f"{reference_answer.strip()}\n\n"
        "【考生作答】\n"
        f"{model_answer.strip()}\n\n"
        "请你根据评分细则打一个这道题的分数，只返回阿拉伯数字，如：40。"
        "要求：1.根据评分细则的分数范围打分，不要超出范围；严格按照评分细则的要求打分；\n"
        "2.评分细则只是大致说明了评分标准，具体的分数要根据考生的作答内容结合正确答案来打分；\n"
    )
    response = model_eval(prompt)
    # print(f"评分标准：{rubric}")
    # print(f"参考答案：{reference_answer}")
    
    # 从返回文本中提取数字分数
    match = re.search(r"\d{1,3}", response)
    if match:
        score = int(match.group())
        return min(max(score, 0), 100)  # 保证 0 ≤ 分数 ≤ 100
    else:
        return 0  # 解析失败时返回 0 分


# 构建模型输入 prompt
def build_prompt(case: Dict, question_index: int) -> str:
    return (
        f"你是医学考试专家，请根据以下病史资料和问题作答：\n"
        f"【病史】\n{case['病史']}\n"
        f"【问题】\n{case['问题'][question_index]}\n"
        f"请用临床医学语言简明回答。"
    )

# 主函数：评测一个目录中所有 json 文件
def evaluate_subjective_cases(json_folder: str, model_infer: Callable[[str], str]) -> List[Dict]:
    results = []

    for json_file in glob.glob(os.path.join(json_folder, '*.json')):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                case_list = json.load(f)

            if not isinstance(case_list, list):
                case_list = [case_list]  # 兼容单个字典结构

            for case in case_list:
                print(f"Evaluating case ID: {case['id']}")
                case_result = {
                    "id": case["id"],
                    "scores": []
                }

                for idx, question in enumerate(case["问题"]):
                    prompt = build_prompt(case, idx)
                    model_answer = model_infer(prompt)
                    ref_answer = case["答案"][idx]
                    rubric = case["评分细则"][idx]
                    # print(f"Model Answer: {model_answer}")
                    # print(f"Reference Answer: {ref_answer}")
                    score = score_subjective_answer_with_model(model_answer, ref_answer, rubric, model_judge)
                    case_result["scores"].append({
                        "question": question,
                        "model_answer": model_answer,
                        "ref_answer": ref_answer,
                        "rubric": rubric,
                        "score": score
                    })

                results.append(case_result)

        except Exception as e:
            print(f"❌ Error processing {json_file}: {e}")

    return results

# 保存结果
def save_subjective_results(results: List[Dict], out_path: str):
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


# 示例调用（请替换为真实路径与模型函数）
if __name__ == '__main__':
    results = evaluate_subjective_cases("./disease_history", deepseek_inference)  # 模型函数可换
    save_subjective_results(results, "subjective_eval_results_deepseekv3.json")
    print("评分完成，已保存结果。")

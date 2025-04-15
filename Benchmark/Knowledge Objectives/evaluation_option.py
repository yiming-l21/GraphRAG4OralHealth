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
<<<<<<< HEAD:Benchmark/Knowledge Objectives/evaluation_option.py
import re
=======

>>>>>>> be04167d1e037d1a539d9a9dc71b8cf0a5b30070:Benchmark/OptionQuestion/evaluation_option.py

# 设置 API 密钥
openai.api_key = 'openai_api_key'
# 使用目录路径
<<<<<<< HEAD:Benchmark/Knowledge Objectives/evaluation_option.py
directory_path = './Benchmark/Knowledge Objectives/'
=======
directory_path = './Benchmark/OptionQuestion/'
>>>>>>> be04167d1e037d1a539d9a9dc71b8cf0a5b30070:Benchmark/OptionQuestion/evaluation_option.py
# model_name = "/home/lym/.cache/modelscope/hub/Qwen/Qwen2.5-7B-Instruct"
# model = AutoModelForCausalLM.from_pretrained(
#     model_name,
#     torch_dtype="auto",
#     device_map="auto"
# )
# tokenizer = AutoTokenizer.from_pretrained(model_name)
<<<<<<< HEAD:Benchmark/Knowledge Objectives/evaluation_option.py
model_name = "/home/lym/3l-dentalmind-backend/lllchat/model_files/deepthinking_model"
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype="auto",
    device_map="auto"
)
tokenizer = AutoTokenizer.from_pretrained(model_name)
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
=======

>>>>>>> be04167d1e037d1a539d9a9dc71b8cf0a5b30070:Benchmark/OptionQuestion/evaluation_option.py
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
        max_tokens=50,  # 根据需要调整
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


# 评估函数，输入目录路径和模型推理函数，返回正确问题数和总问题数
def get_score(directory_path, model_inference):
    def process_question(ques_text, correct_answer):
        result = model_inference(ques_text)
<<<<<<< HEAD:Benchmark/Knowledge Objectives/evaluation_option.py
        print(f"Answer: {result}\nCorrect Answer: {correct_answer}")
=======
        #print(f"Answer: {result}\nCorrect Answer: {correct_answer}")
>>>>>>> be04167d1e037d1a539d9a9dc71b8cf0a5b30070:Benchmark/OptionQuestion/evaluation_option.py
        #print(result in correct_answer or correct_answer in result)
        return result in correct_answer or correct_answer in result

    result_list=[]

    for json_path in glob.glob(os.path.join(directory_path, '*.json')):
        print(f"Processing {json_path}")
        total_question = 0
        correct_question = 0
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            for question in json_data.get('独立题', []):
                if total_question%20==0:
                    print(f"Correct question: {correct_question}/{total_question}")
                total_question += 1
                ques_text = (
                    "下面我会给你一个医学相关的问题，请你根据医学知识进行回答。"
                    "一个题目有5个选项，请选出最合适的选项，并输出选项前字母。"
                    "注意只需要输出选项前字母，不需要输出任何其他内容。\n"
                    f"题目:\n{question['题干'] if '题干' in question.keys() else question['题目']}\n选项:\n{question['选项']}"
                )
                if process_question(ques_text, question['答案']):
                    correct_question += 1

            for question in json_data.get('共用题干题', []):
                if total_question%20==0:
                    print(f"Correct question: {correct_question}/{total_question}")
                total_question += len(question['答案'])
                for idx in range(len(question['答案'])):
                    ques_text = (
                        "下面我会给你一个医学相关的问题，请你根据医学知识进行回答。"
                        "一个题目有5个选项，请选出最合适的选项，并输出选项前字母。"
                        "注意只需要输出选项前字母，不需要输出任何其他内容。\n"
                        f"题目:\n{question['共用题干']}\n{question['题干'][idx]}\n选项:\n{question['选项'][idx]}"
                    )
                    if process_question(ques_text, question['答案'][idx]):
                        correct_question += 1

            for question in json_data.get('共用备选题', []):
                if total_question%20==0:
                    print(f"Correct question: {correct_question}/{total_question}")
                total_question += len(question['答案'])
                for idx in range(len(question['答案'])):
                    ques_text = (
                        "下面我会给你一个医学相关的问题，请你根据医学知识进行回答。"
                        "一个题目有5个选项，请选出最合适的选项，并输出选项前字母。"
                        "注意只需要输出选项前字母，不需要输出任何其他内容。\n"
                        f"题目:\n{question['题干'][idx]}\n选项:\n{question['选项']}"
                    )
                    if process_question(ques_text, question['答案'][idx]):
                        correct_question += 1

        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error processing {json_path}: {e}")
        print(f"Correct question: {correct_question}/{total_question}")
        result_list.append((json_path,(correct_question, total_question)))
    return result_list
def save_result(result_list,topic):
    with open(f"result.txt", 'a') as f:
        f.write(f"Topic: {topic}\n")
        for result in result_list:
            f.write(f"{result[0].split('/')[-1]}: {result[1][0]}/{result[1][1]}\n")

topic_list=["MedicalHumanity","Clinical","Dentistry","Medical"]
for topic in topic_list:
    path=directory_path+topic
<<<<<<< HEAD:Benchmark/Knowledge Objectives/evaluation_option.py
    result_list = get_score(path,DentalMind_o1_inference)
=======
    result_list = get_score(path,deepseek_inference)
>>>>>>> be04167d1e037d1a539d9a9dc71b8cf0a5b30070:Benchmark/OptionQuestion/evaluation_option.py
    save_result(result_list,topic)
    print(f"Finished {topic}")
    

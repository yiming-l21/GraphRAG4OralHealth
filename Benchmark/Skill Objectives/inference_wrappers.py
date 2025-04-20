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
from RAG.retriever.query_entity_extractor import extract_query_entities
from RAG.retriever.query_graph_resolver import QueryGraphResolver
from RAG.retriever.query_relation_extractor import extract_entity_relations
from RAG.storage.entity_vector_storage import EntityVectorStorage
from RAG.storage.neo4j_client import Neo4jClient
dashscope.api_key = "sk-969f4200d53442a2a1733d1c0b1fb330"
# 设置 API 密钥
#openai.api_key = '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'
# 使用目录路径
# model_name = "/home/lym/Qwen2.5-7B-Instruct"
# model = AutoModelForCausalLM.from_pretrained(
#     model_name,
#     torch_dtype="auto",
#     device_map="auto"
# )
# tokenizer = AutoTokenizer.from_pretrained(model_name)
# model_name = "/home/lym/DentalMind_o1"
# model = AutoModelForCausalLM.from_pretrained(
#     model_name,
#     torch_dtype="auto",
#     device_map="auto"
# )
# tokenizer = AutoTokenizer.from_pretrained(model_name)
model_name = "/home/lym/DentalMind_base"
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype="auto",
    device_map="auto"
)
tokenizer = AutoTokenizer.from_pretrained(model_name)
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
async def DentalMind_graph_inference(prompt):
    '''实现DentalMind模型的推理接口，输入用户的prompt，返回模型生成的文本信息'''
    # 1) 构建初始 Query‑Graph（实体+关系）
    entities = extract_query_entities(prompt)
    graph=extract_entity_relations(prompt, entities)
    vdb = EntityVectorStorage("/home/lym/GraphRAG4OralHealth/GraphRAG_System/data/node_properties_embeddings_typed.npz")
    neo4j_client = Neo4jClient(
        url="bolt://127.0.0.1:9687",
        user="neo4j",
        password="medical_neo4j"
    )
    # 3) 用QueryGraphResolver补全图信息
    resolver = QueryGraphResolver(vdb, neo4j_client)
    resolved = await resolver.resolve(graph)
    print("Resolved Query Graph:")
    print(resolved)
    prompt="你可以参考以下知识图中的实体和关系，回答以下问题：\n知识图谱:"+str(resolved)+"\n问题："+prompt+"要求：知识图谱信息不一定和问题答案相关，你需要斟酌，不一定采用，但知识图谱信息一定是正确无误的"
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
    # 提取模型生成的文本
    return response.strip(),graph
def DentalMind_base_inference(prompt):
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
    # 提取模型生成的文本
    return response.strip()
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
    match = re.search(r"<content>(.*?)<content>", response, flags=re.DOTALL)
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
        max_new_tokens=1024
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
from openai import OpenAI
client = OpenAI(api_key="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")

def GPT3_inference(prompt):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",  # 使用聊天模型
        messages=[
            {"role": "system", "content": "你是一个医学知识问答机器人。"},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1000,
        temperature=0.7
    )
    # 注意新版返回的是对象属性，不再是字典索引
    return response.choices[0].message.content.strip()


def GPT4_inference(prompt):
    response = client.chat.completions.create(
        model="gpt-4-turbo",  # 使用聊天模型
        messages=[
            {"role": "system", "content": "你是一个医学知识问答机器人。"},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1000,
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

# def GPT3_inference(prompt):
#     response = openai.ChatCompletion.create(
#         model="gpt-3.5-turbo",  # 使用聊天模型
#         messages=[
#             {"role": "system", "content": "你是一个医学知识问答机器人。"},  # 系统提示
#             {"role": "user", "content": prompt}
#         ],
#         max_tokens=50,  # 根据需要调整
#         temperature=0.7  # 控制输出的随机性
#     )
#     # 提取模型生成的文本
#     return response.choices[0].message['content'].strip()
# def GPT4_inference(prompt):
#     response = openai.ChatCompletion.create(
#         model="gpt-4-turbo",  # 使用聊天模型
#         messages=[
#             {"role": "system", "content": "你是一个医学知识问答机器人。"},  # 系统提示
#             {"role": "user", "content": prompt}
#         ],
#         max_tokens=50,  # 根据需要调整
#         temperature=0.7  # 控制输出的随机性
#     )
#     # 提取模型生成的文本
#     return response.choices[0].message['content'].strip()
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
    model="qwen-plus", # 模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
    messages=messages,
    result_format='message'
    )
    return response['output']['choices'][0]['message']['content'].strip()
def QWenMax_inference(prompt):
    messages=[{"role": "system", "content": "你是一个医学知识问答机器人。"},{"role": "user", "content": prompt}]
    response = dashscope.Generation.call(
    # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
    model="qwen-max", # 模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
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
def deepseek_r1_inference(prompt):
    import os
    from openai import OpenAI
    client = OpenAI(
        # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
        api_key="sk-969f4200d53442a2a1733d1c0b1fb330",  # 如何获取API Key：https://help.aliyun.com/zh/model-studio/developer-reference/get-api-key
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )
    completion = client.chat.completions.create(
        model="deepseek-r1",  # 此处以 deepseek-r1 为例，可按需更换模型名称。
        messages=[
            {'role': 'user', 'content': prompt}
        ]
    )
    return completion.choices[0].message.content
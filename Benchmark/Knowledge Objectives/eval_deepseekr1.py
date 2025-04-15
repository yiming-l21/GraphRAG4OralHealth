import json
import os
import glob
import openai
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
import re
directory_path = './'
def deepseekr1_inference(ques_text,total_question):
    with open("./deepseek_r1_eval.jsonl","r",encoding="utf-8") as f:
        data=f.readlines()
    ans=json.loads(data[total_question-1])['response']['body']['choices'][0]['message']['content']
    return ans
# 评估函数，输入目录路径和模型推理函数，返回正确问题数和总问题数
def get_score(directory_path, model_inference):
    def process_question(ques_text, correct_answer,total_question):
        result = model_inference(ques_text,total_question)
        print(f"Answer: {result}\nCorrect Answer: {correct_answer}")
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
                if process_question(ques_text, question['答案'],total_question):
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
                    if process_question(ques_text, question['答案'][idx],total_question):
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
                    if process_question(ques_text, question['答案'][idx],total_question):
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
    result_list = get_score(path,deepseekr1_inference)
    save_result(result_list,topic)
    print(f"Finished {topic}")
    

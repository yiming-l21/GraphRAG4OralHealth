import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI
import dashscope

# 读取数据
with open("./wanfang_abstract_sampled.json", "r", encoding="utf-8") as f:
    data = json.load(f)
print("读取 JSON 数据成功")
print("数据长度:", len(data))

# 初始化客户端
qa_client = OpenAI(base_url="http://127.0.0.1:8010/v1", api_key="sk-svcacct-Bi9jsZOB611YLuulKl1SfkKLwcpBHKU0-9U9Ztm3bylBuL_2i1DBMR04KYlGjGtT3BlbkFJ9tATCUjwUPLRY05FdX9v_mAg7gq7UoYv7smYmVaG9zUe4XY0pCxC7uIoDnNESAA")

def call_large_model(prompt: str):
    messages = [{"role": "system", "content": "你是一个医学知识问答机器人。"}, {"role": "user", "content": prompt}]
    response = dashscope.Generation.call(
        api_key="sk-969f4200d53442a2a1733d1c0b1fb330",
        model="qwen-plus",
        messages=messages,
        result_format='message'
    )
    return response['output']['choices'][0]['message']['content'].strip()

def process_item(item, field_name, prompt_template):
    count, i = item
    if count % 200 == 0:
        print(count)
    prompt = prompt_template.format(title=i['题目'])
    response = call_large_model(prompt)
    if "否" not in response:
        entity_list = response.split("\n")
        return count, i["题目"], entity_list, field_name
    return count, None, [], field_name

def main():
    # 定义不同类型的提示模板
    prompts = {
        "关联疾病": """请你从给定的论文题目中抽取包含的口腔疾病关键词，如果涉及请返回所有涉及实体(如根尖周炎、龋齿等)并用换行符分隔，如果没有涉及返回否。
        示例：题目：Protaper机用镍钛根管锉损伤形态的临床动态观察[J]。输出：根管锉损伤\n题目:{title}""",
        "关联药物": """请你从给定的论文题目中抽取包含的口腔药物关键词，如果涉及请返回所有涉及实体(如阿莫西林、布洛芬等)并用换行符分隔，如果没有涉及返回否。
        示例：题目：Vitapex糊剂与氧化锌碘仿糊剂填充治疗儿童乳牙慢性根尖周炎效果分析[J]。输出：Vitapex糊剂\n氧化锌碘仿糊剂\n题目:{title}""",
        "关联器械": """请你从给定的论文题目中抽取包含的口腔器械关键词，如果涉及请返回所有涉及实体(如牙科手机、种植机等)并用换行符分隔，如果没有涉及返回否。
        示例：题目：光固化复合树脂在牙体牙髓修复中的效果观察[J]。输出：光固化复合树脂\n题目:{title}""",
        "关联治疗方案": """请你从给定的论文题目中抽取包含的口腔治疗方法关键词，如果涉及请返回所有涉及实体(如根管治疗术、拔牙术等)并用换行符分隔，如果没有涉及返回否。
        示例：题目：浅谈老年患者全口义齿重新修复的临床体会[J]。输出：全口义齿重新修复\n题目:{title}""",
        "关联预防方案": """请你从给定的论文题目中抽取包含的口腔预防方法关键词，如果涉及请返回所有涉及实体(如氟化物涂布、窝沟封闭等)并用换行符分隔，如果没有涉及返回否。
        示例：题目：浅谈老年患者全口义齿重新修复的临床体会[J]。输出：否\n题目:{title}""",
        "关联检查": """请你从给定的论文题目中抽取包含的口腔检查方法关键词，如果涉及请返回所有涉及实体(如口腔内窥镜检查、X光片检查等)并用换行符分隔，如果没有涉及返回否。
        示例：题目：浅谈老年患者全口义齿重新修复的临床体会[J]。输出：否\n题目:{title}""",
    }

    # 使用线程池并行处理
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = []
        for field_name, prompt_template in prompts.items():
            for count, i in enumerate(data):
                futures.append(executor.submit(process_item, (count, i), field_name, prompt_template))
        
        for future in as_completed(futures):
            try:
                count, title, entity_list, field_name = future.result()
                if title:
                    print(f"题目: {title}")
                    print(entity_list)
                    data[count][field_name] = entity_list
            except Exception as e:
                print(f"生成过程中出现错误: {e}")

    # 将更新后的数据保存到新的 JSON 文件
    with open("./wanfang_abstract_sampled_updated.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()
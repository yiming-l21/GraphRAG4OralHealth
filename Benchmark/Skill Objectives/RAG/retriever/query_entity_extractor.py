# utils/query_entity_extractor.py
import dashscope
import json

dashscope.api_key = "sk-969f4200d53442a2a1733d1c0b1fb330"
ENTITY_EXTRACTION_PROMPT_SPECIAL= """
你是一个医学诊断结构化助手，任务是从提供的完整病例病史中提取结构化医学诊断信息，以便后续知识图谱匹配和问答增强。

请根据以下输入的病史材料，输出符合下列字段要求的 JSON block：

- 疾病名称,不要猜测，用?表示
- 诊断原则（包括主诉、现病史、体征、检查等方面的要点列表）
- 治疗方法（包括紧急处理、基础治疗、长期方案和预防措施等）

注意事项：
1. 请仅输出一个 JSON block；
2. 如果病例涉及多种可能疾病（如牙周炎、联合病变等），优先选择最明确的主要诊断；
3. 请参考如下格式输出：

"?": {{
    "疾病定义": "......",
    "诊断原则": [
        "...",
        "..."
    ],
    "治疗方法": [
        "...",
        "..."
    ]
}}

请对以下病例材料进行结构化处理：
{query}
"""

ENTITY_EXTRACTION_PROMPT = """
你是一个医学知识图谱实体提取助手，请根据用户的复杂问题提取所有可能参与知识图谱检索的医学实体。
每个实体请包含以下字段：

- name: 实体的专业术语，若问题中未明确出现，用 "?" 代替；
- type: 实体的类型，请仅从以下列表当中选择:[口腔疾病,器械,文献,检查,治疗,科室,药物,预防]；
- description: 查询当中包含的用于识别该实体的描述,包括实体本身属性以及与其他实体的关系，用于检索实体,如果不是该实体的特异性描述，请不要添加description；

输出格式必须是 JSON 数组。

示例：
问题：
"在一种检查中，使用某种夹持器械来评估牙齿的松动情况。这种夹持器械是否也用于一种外科手术中？该手术适用于哪些口腔疾病，并简述其适应症和主要步骤？"
输出：
[
  {{"name": "?", "type": "检查", "description": "使用某种夹持器械评估牙齿的松动情况的检查"}},
 {{"name": "?", "type": "器械"}},
  {{"name": "?", "type": "治疗"}},
  {{"name": "?", "type": "口腔疾病"}}
]
问题：
"针对一种因创伤或化脓性感染导致的以开口困难为主要表现的口腔疾病，其治疗方法中涉及一种通过截骨和移动骨段矫正面部不对称的手术。在该手术过程中，使用了一类具有杀菌和抑菌作用的药物，这类药物是否也被用于一种主要针对儿童、通过填充窝沟预防龋齿发生的措施中？如果是，请说明这类药物的具体名称及其在两种场景中的应用方式。"
输出：
[
    {{"name": "?", "type": "口腔疾病", "description": "因创伤或化脓性感染导致的以开口困难为主要表现的口腔疾病"}},
    {{"name": "?", "type": "治疗", "description": "通过截骨和移动骨段矫正面部不对称的手术"}},
    {{"name": "?", "type": "药物", "description": "具有杀菌和抑菌作用的药物"}},
    {{"name": "?", "type": "预防", "description": "主要针对儿童、通过填充窝沟预防龋齿发生的措施"}}
]
问题：
"妊娠期龈炎患者应前往哪个科室就诊，该科室有哪些特色技术"
输出：
[
    {{"name": "妊娠期龈炎", "type": "口腔疾病"}},
    {{"name": "?", "type": "科室", "description": "妊娠期龈炎患者就诊的科室"}}
]
请提取下面这个问题的实体：
"{query}"
"""
import re
def extract_wrapped_json_from_markdown(content: str):
    """
    从 markdown 中的 ```json 块中提取并包装为合法 JSON 对象。
    如果成功返回 dict，否则返回 None。
    """
    pattern = r"```json\s*(.*?)\s*```"  # 非贪婪提取 ```json ... ``` 中的内容
    match = re.search(pattern, content, re.DOTALL)

    if not match:
        return None

    json_fragment = match.group(1).strip()

    # 尝试包装为完整 JSON：添加花括号
    wrapped = f"{{{json_fragment}}}"

    try:
        return json.loads(wrapped)
    except json.JSONDecodeError as e:
        print(f"[解析失败] JSONDecodeError: {e}")
        return None
def extract_query_entities(query: str) -> list:
    prompt = ENTITY_EXTRACTION_PROMPT_SPECIAL.format(query=query)
    try:
        response = dashscope.Generation.call(
            model="qwen-plus",
            prompt=prompt,
            result_format='message'
        )
        content = response["output"]["choices"][0]["message"]["content"]
        return extract_wrapped_json_from_markdown(content)
    except Exception as e:
        print(f"❌ 实体抽取失败: {e}")
        return []

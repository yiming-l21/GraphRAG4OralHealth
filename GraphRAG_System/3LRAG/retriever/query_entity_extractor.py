# utils/query_entity_extractor.py
import dashscope
import json

dashscope.api_key = "sk-969f4200d53442a2a1733d1c0b1fb330"

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

def extract_query_entities(query: str) -> list:
    prompt = ENTITY_EXTRACTION_PROMPT.format(query=query)
    try:
        response = dashscope.Generation.call(
            model="qwen-max",
            prompt=prompt,
            result_format='message'
        )
        content = response["output"]["choices"][0]["message"]["content"]
        return json.loads(content)
    except Exception as e:
        print(f"❌ 实体抽取失败: {e}")
        return []

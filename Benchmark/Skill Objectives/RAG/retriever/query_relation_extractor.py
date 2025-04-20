# utils/query_relation_extractor.py
import dashscope
import json

dashscope.api_key = "sk-969f4200d53442a2a1733d1c0b1fb330"

RELATION_EXTRACTION_PROMPT = """
你是一个医学知识图谱关系抽取助手，请根据用户提出的问题，以及已识别出的医学实体，抽取出它们之间可能存在的有向语义关系。

每一条关系应包括：
- head：起始实体名称（必须来自实体列表）；
- relation：实体间的语义关系,必须从以下关系当中选择:[使用器械,使用药物,就诊,治疗,预防,引用]:
    (治疗)使用器械(器械)
    (预防)使用器械(器械)
    (检查)使用器械(器械)
    (治疗)使用药物(药物)
    (预防)使用药物(药物)
    (检查)使用药物(药物)
    (口腔疾病)就诊(科室)
    (治疗)治疗(口腔疾病)
    (预防)预防(口腔疾病)
    (检查)引用(文献)
    (治疗)引用(文献)
    (预防)引用(文献)
    (口腔疾病)引用(文献)
- tail：终止实体名称（必须来自实体列表）；

请仅在你能从问题语义中判断出两个实体间确实存在联系的前提下输出关系。

### 示例 1：
问题：
"在一种检查中，使用某种夹持器械来评估牙齿的松动情况。这种夹持器械是否也用于一种外科手术中？该手术适用于哪些口腔疾病，并简述其适应症和主要步骤？"
实体：
[
  {{"id":0,"name": "?", "type": "检查", "description": "使用某种夹持器械评估牙齿的松动情况的检查"}},
  {{"id":1,"name": "?", "type": "器械"}},
  {{"id":2,"name": "?", "type": "治疗"}},
  {{"id":3,"name": "?", "type": "口腔疾病"}}
]

输出：
[
    {{"head": "0", "relation": "使用器械", "tail": "1"}},
    {{"head": "2", "relation": "使用器械", "tail": "1"}},
    {{"head": "2", "relation": "治疗", "tail": "3"}}
]
### 示例 2：
问题：
"针对一种因创伤或化脓性感染导致的以开口困难为主要表现的口腔疾病，其治疗方法中涉及一种通过截骨和移动骨段矫正面部不对称的手术。在该手术过程中，使用了一类具有杀菌和抑菌作用的药物，这类药物是否也被用于一种主要针对儿童、通过填充窝沟预防龋齿发生的措施中？如果是，请说明这类药物的具体名称及其在两种场景中的应用方式。"
实体：
[
    {{"id":0,"name": "?", "type": "口腔疾病", "description": "因创伤或化脓性感染导致的以开口困难为主要表现的口腔疾病"}},
    {{"id":1,"name": "?", "type": "治疗", "description": "通过截骨和移动骨段矫正面部不对称的手术"}},
    {{"id":2,"name": "?", "type": "药物", "description": "具有杀菌和抑菌作用的药物"}},
    {{"id":3,"name": "?", "type": "预防", "description": "主要针对儿童、通过填充窝沟预防龋齿发生的措施"}}
]

输出：
[
    {{"head": "1", "relation": "使用药物", "tail": "2"}},
    {{"head": "3", "relation": "使用药物", "tail": "2"}},
    {{"head": "1", "relation": "治疗", "tail": "0"}}
]
### 示例 3：
问题：
"妊娠期龈炎患者应前往哪个科室就诊，该科室有哪些特色技术"
实体：
[
    {{"name": "妊娠期龈炎", "type": "口腔疾病"}},
    {{"name": "?", "type": "科室", "description": "妊娠期龈炎患者就诊的科室"}}
]

输出：
[
    {{"head": "0", "relation": "就诊", "tail": "1"}}
]

问题：
"{query}"

实体：
{entities}

请从上述实体中抽取实体对之间的语义关系，输出格式为 JSON 数组，不要输出其他内容
"""

def extract_entity_relations(query: str, entities: list) -> list:
    entities_with_id = []
    for idx, ent in enumerate(entities):
        ent_with_id = ent.copy()
        ent_with_id["id"] = idx
        entities_with_id.append(ent_with_id)
    prompt = RELATION_EXTRACTION_PROMPT.format(query=query, entities=json.dumps(entities_with_id, ensure_ascii=False))
    try:
        response = dashscope.Generation.call(
            model="qwen-max",
            prompt=prompt,
            result_format='message'
        )
        content = response["output"]["choices"][0]["message"]["content"]
        relations_raw = json.loads(content)
        query_graph = format_query_graph(entities_with_id, relations_raw)
        return query_graph
    except Exception as e:
        print(f"❌ 关系抽取失败: {e}")
        return {
            "entities": entities,
            "relations": []
        }
# utils/query_graph_formatter.py

from typing import List, Dict

def format_query_graph(entities_with_id: List[Dict], relations_raw: List[Dict]) -> Dict:
    # 移除 id 并保留 name, type, description
    entities = []
    id_mapping = {}  # id(str/int) → index（从0开始重排）
    for idx, ent in enumerate(entities_with_id):
        id_mapping[str(ent["id"])] = idx
        if "description" not in ent:
            entities.append({
                "name": ent["name"],
                "type": ent["type"]
            })
        else:
            entities.append({
                "name": ent["name"],
                "type": ent["type"],
                "description": ent["description"]
            })

    # 替换关系中的 head/tail 为映射后的整数索引
    relations = []
    for rel in relations_raw:
        h = id_mapping[str(rel["head"])]
        t = id_mapping[str(rel["tail"])]
        relations.append({
            "head": h,
            "relation": rel["relation"],
            "tail": t
        })

    return {
        "entities": entities,
        "relations": relations
    }

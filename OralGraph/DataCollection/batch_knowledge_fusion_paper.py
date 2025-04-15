import json
from fuzzywuzzy import fuzz, process
from sentence_transformers import SentenceTransformer, util
with open("./wanfang_abstract_sampled_updated.json", "r", encoding="utf-8") as f:
    data = json.load(f)
print("读取 JSON 数据成功")
print(len(data))
#获取目录下所有文件名
import os
file_list = os.listdir("../ClassifyTree/terms_table")
#获取所有以txt结尾的文件名
file_list = [i for i in file_list if i.endswith(".txt")]
#读取所有文件
terms = {}
for file in file_list:
    with open("../ClassifyTree/terms_table/" + file, "r", encoding="utf-8") as f:
        terms[file.split("_")[0]] = f.read().split("\n")
print(terms.keys())

# 加载预训练的Sentence-BERT模型
model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

def get_embeddings(texts):
    """获取文本的向量表示"""
    embeddings = model.encode(texts, convert_to_tensor=True)
    return embeddings

def cosine_similarity(vec1, vec2):
    """计算两个向量之间的余弦相似度"""
    return util.pytorch_cos_sim(vec1, vec2).item()

def align_entities(entities, term_set):
    """对齐实体"""
    aligned_entities = []
    term_list = list(term_set)  # 将集合转换为列表以便后续处理
    term_embeddings = get_embeddings(term_list)  # 获取术语的向量表示
    for entity in entities:
        # 去除首尾空格
        entity = entity.strip().lower()
        matched_term = None
        
        # 直接匹配
        for term in term_set:
            term_lower = term.lower()
            if term_lower == entity:
                matched_term = term
                break

        # 子串包含
        if not matched_term:
            for term in term_set:
                term_lower = term.lower()
                if entity in term_lower or term_lower in entity:
                    matched_term = term
                    break

        # 模糊匹配
        if not matched_term:
            best_match = process.extractOne(entity, term_set, scorer=fuzz.token_sort_ratio)
            if best_match and best_match[1] >= 55:  # 设置一个阈值来决定是否接受模糊匹配结果
                print(f"实体：{entity}，匹配：{best_match}")
                matched_term = best_match[0]
        if matched_term:
            aligned_entities.append(matched_term)
    return aligned_entities
for paper in data:
    if "关联疾病" in paper.keys():
        paper["对齐疾病"] = align_entities(paper["关联疾病"], terms["dicease"])
        print("对齐疾病" in paper.keys())
    if "关联药物" in paper.keys():
        paper["对齐药物"] = align_entities(paper["关联药物"], terms["medicine"])
    if "关联器械" in paper.keys():
        paper["对齐器械"] = align_entities(paper["关联器械"], terms["equitment"])
    if "关联治疗方案" in paper.keys():
        paper["对齐治疗方案"] = align_entities(paper["关联治疗方案"], terms["treatment"])
    if "关联预防方案" in paper.keys():
        paper["对齐预防方案"] = align_entities(paper["关联预防方案"], terms["prevention"])
    if "关联检查" in paper.keys():
        paper["对齐检查"] = align_entities(paper["关联检查"], terms["examination"])

with open("./wanfang_abstract_sampled_updated.json", "w", encoding="utf-8") as f:
    json.dump(data,f,ensure_ascii=False,indent=4)
# graphrag_evaluator.py

import asyncio
import json
import time
from typing import List
from retriever.query_entity_extractor import extract_query_entities
from retriever.query_relation_extractor import extract_entity_relations
from retriever.query_graph_resolver import QueryGraphResolver
from storage.entity_vector_storage import EntityVectorStorage
from storage.neo4j_client import Neo4jClient
# 5.后处理步骤
def filter_with_llm(question: str, nodes: List[str], model="qwen-plus", api_key="sk-969f4200d53442a2a1733d1c0b1fb330") -> List[str]:
    from dashscope import Generation
    filtered = []
    
    for i, node_content in enumerate(nodes):
        prompt = f"""
    你是一名口腔医学知识图谱专家，请根据以下信息判断问题是否与节点内容相关,相关标准为问题出现节点名称或涉及节点相关属性，否则一律不相关。
    【问题】
    {question}
    【节点内容】
    {node_content}
    请回答：“相关”或“不相关”,不要输出无关内容。
    """

        try:
            response = Generation.call(
                model=model,
                api_key=api_key,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                result_format="message"
            )
            reply = response["output"]["choices"][0]["message"]["content"].strip()
            if "不相关" in reply:
                continue
            else:
                filtered.append(node_content)
        except Exception as e:
            print(f"[!] LLM 筛选失败（节点{i}）：{e}")
            continue

    return filtered

# ✅ 提取 Groundtruth 实体
def find_all_values_in_dict(d):
    if "nodes" in d:
        return [node["properties"]["名称"] for node in d["nodes"]]
    else:
        return [d["properties"]["名称"]]


def extract_groundtruth_entities(item) -> List[str]:
    raw_text = json.dumps(item.get("检索文本", {}), ensure_ascii=False)
    return list(set(find_all_values_in_dict(json.loads(raw_text))))


# ✅ 指标评估
def evaluate_entities(gt_entities: List[str], pred_entities: List[str]):
    gt_set = set(gt_entities)
    pred_set = set(pred_entities)

    tp = len(gt_set & pred_set)
    fp = len(pred_set - gt_set)
    fn = len(gt_set - pred_set)

    precision = tp / (tp + fp) if (tp + fp) else 0
    recall = tp / (tp + fn) if (tp + fn) else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0
    return precision, recall, f1


# ✅ 主评测流程
async def evaluate(file_path: str):
    # 初始化资源
    vdb = EntityVectorStorage("/home/lym/GraphRAG4OralHealth/GraphRAG_System/data/node_properties_embeddings_typed.npz")
    neo4j_client = Neo4jClient(
        url="bolt://127.0.0.1:9687",
        user="neo4j",
        password="medical_neo4j"
    )
    resolver = QueryGraphResolver(vdb, neo4j_client)

    # 加载数据
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"📊 加载测试集：{file_path}，共 {len(data)} 条")

    # 初始化结果容器
    p_list, r_list, f1_list, time_list = [], [], [], []

    # 遍历每个 query 样本
    for idx, item in enumerate(data):
        query = item["问题"]
        gt_entities = extract_groundtruth_entities(item)

        print(f"\n➡️ 第 {idx+1} 条 | Query: {query}")
        try:
            # 构建图 + 链接
            start = time.time()

            ents = extract_query_entities(query)
            query_graph = extract_entity_relations(query, ents)
            resolved = await resolver.resolve(query_graph)

            end = time.time()
            duration = end - start
            time_list.append(duration)

            # 获取预测实体
            pred_entities = set(filter_with_llm(query,[ent["name"] for ent in resolved["entities"] if ent["name"] != "?"]))
            print(f"🔍 预测实体: {pred_entities}")

            # 指标
            p, r, f1 = evaluate_entities(gt_entities, pred_entities)
            print(f"🎯 Precision: {p:.2f}, Recall: {r:.2f}, F1: {f1:.2f} | ⏱️ {duration:.2f}s")

            p_list.append(p)
            r_list.append(r)
            f1_list.append(f1)

        except Exception as e:
            print(f"❌ 第 {idx+1} 条失败: {e}")
            p_list.append(0)
            r_list.append(0)
            f1_list.append(0)
            time_list.append(0)

    # 汇总结果
    print("\n📈 评测汇总结果：")
    print(f"Avg Precision: {sum(p_list)/len(p_list):.4f}")
    print(f"Avg Recall:    {sum(r_list)/len(r_list):.4f}")
    print(f"Avg F1 Score:  {sum(f1_list)/len(f1_list):.4f}")
    print(f"Avg Time:      {sum(time_list)/len(time_list):.2f}s")


if __name__ == "__main__":
    import sys
    file = sys.argv[1] if len(sys.argv) > 1 else "/home/lym/GraphRAG4OralHealth/Benchmark/GraphRAG/1hop.json"
    asyncio.run(evaluate(file))

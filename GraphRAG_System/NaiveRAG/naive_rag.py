import json
import numpy as np
import faiss
from typing import List, Tuple
from neo4j import GraphDatabase
import dashscope
from sklearn.metrics import precision_score, recall_score, f1_score

# 配置路径与参数
EMBED_PATH = "/home/lym/GraphRAG4OralHealth/GraphRAG_System/data/node_summarization_embeddings.npz"
TEST_FILES = [
    "/home/lym/GraphRAG4OralHealth/Benchmark/GraphRAG/1hop.json"
]
NEO4J_URL = "bolt://127.0.0.1:9687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "medical_neo4j"
TOP_K = 3
EMBED_DIM = 1024

dashscope.api_key = "sk-969f4200d53442a2a1733d1c0b1fb330"

# 1. 载入本地嵌入
def load_embeddings(path: str):
    data = np.load(path)
    return data["keys"], data["embeddings"]

# 2. 构建 FAISS 索引
def build_index(embeddings: np.ndarray):
    index = faiss.IndexFlatL2(EMBED_DIM)
    index.add(embeddings)
    return index

def get_embedding(texts: List[str], batch_size: int = 8) -> List[List[float]]:
    all_embeddings = []
    max_len = 3000  # 限制最大长度，避免大模型异常

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        batch = [t[:max_len] for t in batch]  # 清洗字符串
        try:
            response = dashscope.TextEmbedding.call(
                model="text-embedding-v3",
                input=batch
            )
            if not response or "output" not in response or "embeddings" not in response["output"]:
                raise ValueError(f"嵌入接口返回异常：{response}")
            all_embeddings.extend([item["embedding"] for item in response["output"]["embeddings"]])
        except Exception as e:
            print(f"嵌入生成失败（batch {i}-{i+len(batch)}）: {e}")
            all_embeddings.extend([[0.0] * 1024 for _ in batch])

    return all_embeddings


# 4. 从 Neo4j 获取名称
def fetch_names_from_neo4j(ids: List[int]) -> List[str]:
    driver = GraphDatabase.driver(NEO4J_URL, auth=(NEO4J_USER, NEO4J_PASSWORD))
    names = []
    with driver.session() as session:
        for node_id in ids:
            result = session.run("MATCH (n) WHERE n.名称 = $id RETURN n.名称 AS name", id=node_id)
            record = result.single()
            if record and record["name"]:
                names.append(str(record["name"]))
    driver.close()
    return names
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
def fetch_contents_from_neo4j(ids: List[int]) -> List[str]:
    """
    根据节点 ID 列表，从 Neo4j 获取每个节点的所有属性，并拼接成文本格式。
    """
    driver = GraphDatabase.driver(NEO4J_URL, auth=(NEO4J_USER, NEO4J_PASSWORD))
    contents = []

    with driver.session() as session:
        for node_id in ids:
            result = session.run(
                "MATCH (n) WHERE n.名称 = $id RETURN properties(n) AS props", id=node_id
            )
            record = result.single()
            if record and record["props"]:
                props = record["props"]
                # 拼接为文本：key1: val1 key2: val2 ...
                content = "\n".join([f"{k}: {v}" for k, v in props.items()])
                contents.append(content)

    driver.close()
    return contents
import re

def extract_names_from_contents(contents: List[str]) -> List[str]:
    """
    从拼接文本中提取“名称”字段的值。
    """
    names = []
    for content in contents:
        match = re.search(r"名称[:：]\s*(.+)", content)
        if match:
            name = match.group(1).strip()
            # 去除换行符或后续字段干扰（比如 名称: XXX\n其他属性: ...）
            name = name.split("\n")[0].strip()
            names.append(name)
        else:
            names.append("")  # 或者 names.append("未知名称")
    return names


# 6. 执行评估
import time

def evaluate_naive_rag():
    node_ids, embeddings = load_embeddings(EMBED_PATH)
    print("✅ 加载向量 shape:", embeddings.shape)
    index = build_index(embeddings)

    all_prec, all_rec, all_f1 = [], [], []
    all_times = []

    for file_path in TEST_FILES:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for idx, sample in enumerate(data):
            query = sample["问题"]
            gt_nodes = []

            start_time = time.time()  # ⏱️ 计时开始

            # 获取 groundtruth 名称
            gt = sample["检索文本"]
            if isinstance(gt, dict) and "nodes" in gt:
                gt_nodes = [n["properties"]["名称"] for n in gt["nodes"]]
            elif isinstance(gt, dict) and "properties" in gt:
                gt_nodes = [gt["properties"]["名称"]]
            else:
                print(f"[!] 跳过无效样本 idx={idx}")
                continue

            # 查询向量 → FAISS 检索
            query_vec = get_embedding([query])[0]
            D, I = index.search(np.array([query_vec]), TOP_K)
            pred_ids = [node_ids[i] for i in I[0]]
            node_contents = fetch_contents_from_neo4j(pred_ids)
            filtered_contents = filter_with_llm(query, node_contents)
            pred_names = extract_names_from_contents(filtered_contents)

            # 计算指标
            pred_set = set(pred_names)
            gt_set = set(gt_nodes)
            tp = len(pred_set & gt_set)
            precision = tp / len(pred_set) if pred_set else 0
            recall = tp / len(gt_set) if gt_set else 0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0

            all_prec.append(precision)
            all_rec.append(recall)
            all_f1.append(f1)

            elapsed = time.time() - start_time  # ⏱️ 计时结束
            all_times.append(elapsed)

            # 打印每条结果
            print(f"🔍 问题{idx+1}：{query}")
            print(f"GT: {gt_nodes}")
            print(f"Retrieved: {pred_names}")
            print(f"Precision: {precision:.2f}, Recall: {recall:.2f}, F1: {f1:.2f}, Time: {elapsed:.2f}s")
            print("-" * 50)

    # 汇总打印
    print("\n🎯 总体评估结果：")
    print(f"Avg Precision: {np.mean(all_prec):.3f}")
    print(f"Avg Recall: {np.mean(all_rec):.3f}")
    print(f"Avg F1: {np.mean(all_f1):.3f}")
    print(f"⏱️ Avg Time per question: {np.mean(all_times):.2f} seconds")


# 执行主流程
if __name__ == "__main__":
    evaluate_naive_rag()

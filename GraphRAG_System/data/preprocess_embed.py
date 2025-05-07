import dashscope
from neo4j import GraphDatabase
from typing import List, Tuple
import numpy as np
import json
import os

# ====================
# Step 1: 配置参数
# ====================
# 千问 API key
dashscope.api_key = "sk-969f4200d53442a2a1733d1c0b1fb330"

# Neo4j 连接信息
NEO4J_URL = "bolt://127.0.0.1:9687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "medical_neo4j"



# ====================
# Step 2: 获取节点数据
# ====================
def fetch_nodes_from_neo4j() -> Tuple[List[int], List[str]]:
    driver = GraphDatabase.driver(NEO4J_URL, auth=(NEO4J_USER, NEO4J_PASSWORD))
    node_ids, node_texts = [], []
    node_labels = []
    with driver.session() as session:
        query = "MATCH (n) RETURN ID(n) AS id, labels(n) as labels,properties(n) AS props"
        result = session.run(query)
        for record in result:
            props = record["props"]
            node_id = props.get("名称", "Unknown")
            if node_id == "Unknown":
                node_id = props.get("标题", "Unknown")
            node_label = record["labels"][0]
            node_labels.append(node_label)
            # 合并属性为单个文本
            text = "\n".join([f"{k}: {v}" for k, v in props.items()])
            node_ids.append(node_id)
            node_texts.append(text)

    driver.close()
    return node_ids, node_labels,node_texts

# ====================
# Step 3: 调用 Qwen 模型生成嵌入
# ====================
import dashscope
import time
from typing import List

def get_embedding(texts: List[str], batch_size: int = 10) -> List[List[float]]:
    all_embeddings = []
    
    # 记录失败的 batch 进行后续调试
    failed_batches = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        print(f"👉 正在处理 batch {i}-{i + len(batch)}...")
        
        try:
            # 调用 DashScope 生成嵌入
            response = dashscope.TextEmbedding.call(
                model="text-embedding-v3",
                input=batch
            )
            
            # 检查 response 是否有效
            if not response or 'output' not in response or 'embeddings' not in response['output']:
                print(f"[!] ⛔️ API 返回异常（batch {i}-{i + len(batch)}），响应内容：{response}")
                failed_batches.append((i, batch))  # 记录失败的 batch
                raise ValueError("Invalid response structure")

            # 获取当前 batch 的嵌入向量
            batch_embeddings = [item["embedding"] for item in response["output"]["embeddings"]]
            all_embeddings.extend(batch_embeddings)
            print(f"✅ batch {i}-{i + len(batch)} 处理成功！")
            # 检查所有向量维度是否一致
            lengths = [len(vec) for vec in all_embeddings]
            unique_lengths = set(lengths)
            print(f"[调试] 不同嵌入向量长度有：{unique_lengths}")

        except Exception as e:
            print(f"[!] 嵌入生成失败（batch {i}-{i + len(batch)}）: {e}")
            failed_batches.append((i, batch))  # 记录失败的 batch
            # 填充占位向量（防止数据错乱）
            all_embeddings.extend([[0.0] * 1536 for _ in batch])
            time.sleep(1)  # 防止触发请求频率限制

    return all_embeddings


# ====================
# Step 4: 保存嵌入到本地
# ====================
def save_embeddings_to_disk(node_ids: List[str],node_labels: List[str], embeddings: List[List[float]], save_path: str):
    # 检查所有向量维度是否一致
    lengths = [len(vec) for vec in embeddings]
    unique_lengths = set(lengths)
    print(f"[调试] 不同嵌入向量长度有：{unique_lengths}")

    np.savez_compressed(
        save_path,
        node_ids=np.array(node_ids),
        node_labels=np.array(node_labels),
        embeddings=np.array(embeddings, dtype=np.float32)
    )
    print(f"[✔] 嵌入向量保存完成，共 {len(node_ids)} 条，路径：{save_path}")
# 保存文件路径
SAVE_PATH1 = "node_name_embeddings_typed.npz"
SAVE_PATH2 = "node_properties_embeddings_typed.npz"
# ====================
# 主函数执行流程
# ====================
def main():
    print("🚀 正在从 Neo4j 中提取节点...")
    node_ids,node_labels, node_texts = fetch_nodes_from_neo4j()
    print(f"📦 提取到 {len(node_ids)} 个节点。")
    #检查node_ids有没有unknown
    if "Unknown" in node_ids:
        print("❌ 节点 ID 中包含 'Unknown'，请检查数据源。")
        return
    print("🧠 正在生成 Qwen text-embedding-v3 向量...")
    embeddings = get_embedding(node_ids)

    print("💾 正在保存嵌入向量到本地...")
    save_embeddings_to_disk(node_ids,node_labels,embeddings, SAVE_PATH1)
    print("🧠 正在生成 Qwen text-embedding-v3 向量...")
    embeddings = get_embedding(node_texts)

    print("💾 正在保存嵌入向量到本地...")
    save_embeddings_to_disk(node_ids,node_labels,embeddings, SAVE_PATH2)

if __name__ == "__main__":
    main()

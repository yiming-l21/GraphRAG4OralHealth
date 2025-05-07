import os
import json
import asyncio
import numpy as np
from neo4j import GraphDatabase
from typing import List, Dict
from dashscope import TextEmbedding, Generation
import dashscope
from tqdm import tqdm

# 设置 Qwen API Key
dashscope.api_key = "sk-969f4200d53442a2a1733d1c0b1fb330"

# ========== 嵌入函数 ==========
async def get_embedding(texts: List[str], batch_size: int = 8) -> List[List[float]]:
    all_embeddings = []
    max_len = 3000
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        batch = [t[:max_len] for t in batch]
        try:
            response = TextEmbedding.call(model="text-embedding-v3", input=batch)
            all_embeddings.extend([item["embedding"] for item in response["output"]["embeddings"]])
            # 检查所有向量维度是否一致
            lengths = [len(vec) for vec in all_embeddings]
            unique_lengths = set(lengths)
            print(f"[调试] 不同嵌入向量长度有：{unique_lengths}")

        except Exception as e:
            print(f"[嵌入失败] {e}")
            all_embeddings.extend([[0.0] * 1024 for _ in batch])
    return all_embeddings

# ========== 摘要生成 ==========
def summarize_properties(name: str, properties: Dict[str, str]) -> str:
    description = "\n".join([f"{k}: {v}" for k, v in properties.items() if v and isinstance(v, str)])
    prompt = f"""
你是一名口腔医学专家，擅长知识图谱构建。
请根据以下节点的属性信息，生成一段精炼的第三人称摘要，用于表示这个实体：

实体名称: {name}
实体属性:
{description}

输出格式：直接输出摘要，不要加多余的解释。
"""
    try:
        messages = [
            {"role": "system", "content": "你是一名口腔医学专家。"},
            {"role": "user", "content": prompt}
        ]
        response = Generation.call(model="qwen-plus", messages=messages, result_format="message")
        return response['output']['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"[摘要失败] {e}")
        return ""

def summarize_relationship(source_name: str, source_props: Dict, relation_type: str,
                           target_name: str, target_props: Dict) -> str:
    prompt = f"""
你是口腔医学专家，请根据以下信息，生成一段自然语言描述 "{source_name}" 与 "{target_name}" 之间的关系：

- 源实体: {source_name}
- 源实体属性（简要）: {json.dumps(source_props, ensure_ascii=False)[:500]}
- 目标实体: {target_name}
- 目标实体属性（简要）: {json.dumps(target_props, ensure_ascii=False)[:500]}
- 关系类型: {relation_type}

输出格式：只输出一段自然语言摘要，不要加标题和解释。
"""
    try:
        messages = [
            {"role": "system", "content": "你是一名口腔医学专家。"},
            {"role": "user", "content": prompt}
        ]
        response = Generation.call(model="qwen-plus", messages=messages, result_format="message")
        return response['output']['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"[关系摘要失败] {e}")
        return f"{source_name} 与 {target_name} 存在关系：{relation_type}"

# ========== 嵌入保存 ==========
def save_embeddings_to_disk(keys: List[str], embeddings: List[List[float]], save_path: str):
    print(f"保存向量大小为{len(embeddings)}，{len(embeddings[0])}")
    np.savez_compressed(
        save_path,
        keys=np.array(keys),
        embeddings=np.array(embeddings, dtype=np.float32)
    )
    print(f"[✔] 嵌入向量保存完成，共 {len(keys)} 条，路径：{save_path}")

# ========== Neo4j 抽取 ==========
class Neo4jExporter:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def extract_entities(self):
        query = "MATCH (n) RETURN coalesce(n.名称, n.标题) AS name, labels(n) AS labels, properties(n) AS props"
        with self.driver.session() as session:
            result = session.run(query)
            return [record for record in result]


    def extract_relationships(self):
        query = "MATCH (a)-[r]->(b) RETURN coalesce(a.名称, a.标题) as src_name, coalesce(b.名称, b.标题) as tgt_name, type(r) as type, properties(a) as props_src, properties(b) as props_tgt"
        with self.driver.session() as session:
            result = session.run(query)
            return [record for record in result]


# ========== 主处理流程 ==========
import asyncio
import concurrent.futures
from tqdm.asyncio import tqdm_asyncio

# 控制并发数量
semaphore = asyncio.Semaphore(8)  # 可调节并发数（建议不超过10）

# 异步封装摘要函数
async def async_summarize_properties(name: str, props: dict):
    async with semaphore:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, summarize_properties, name, props)

async def async_summarize_relationship(src, props_src, rel_type, tgt, props_tgt):
    async with semaphore:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, summarize_relationship, src, props_src, rel_type, tgt, props_tgt)


async def run_full_embedding_pipeline(exporter: Neo4jExporter, save_dir="./embed_npz"):
    os.makedirs(save_dir, exist_ok=True)

    # --- 实体处理 ---
    print("[Step 1] 提取实体...")
    entities = list(exporter.extract_entities())
    entity_keys = [r["name"] or r["props"].get("名称") or "未知实体" for r in entities]

    print("[Step 2] 并发生成实体摘要...")
    entity_texts = await tqdm_asyncio.gather(*[
        async_summarize_properties(name, dict(r["props"])) for name, r in zip(entity_keys, entities)
    ], desc="摘要实体", total=len(entity_keys))

    print("[Step 3] 嵌入实体...")
    entity_embeddings = await get_embedding(entity_texts)
    save_embeddings_to_disk(entity_keys, entity_embeddings, os.path.join(save_dir, "node_properties_entity_embeddings.npz"))

    # --- 关系处理 ---
    print("[Step 4] 提取关系...")
    relations = list(exporter.extract_relationships())
    relation_keys = [f"{r['src_name']}->{r['type']}->{r['tgt_name']}" for r in relations]

    print("[Step 5] 并发生成关系摘要...")
    relation_texts = await tqdm_asyncio.gather(*[
        async_summarize_relationship(
            r["src_name"], r["props_src"], r["type"], r["tgt_name"], r["props_tgt"]
        ) for r in relations
    ], desc="摘要关系", total=len(relations))

    print("[Step 6] 嵌入关系...")
    relation_embeddings = await get_embedding(relation_texts)
    save_embeddings_to_disk(relation_keys, relation_embeddings, os.path.join(save_dir, "relation_embeddings.npz"))

    print("✅ 全部处理完成！")


# ========== 入口 ==========
if __name__ == "__main__":
    exporter = Neo4jExporter(uri="bolt://127.0.0.1:9687", user="neo4j", password="medical_neo4j")
    asyncio.run(run_full_embedding_pipeline(exporter))
    exporter.close()

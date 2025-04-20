import numpy as np
import faiss
import json
from typing import List, Tuple
from neo4j import GraphDatabase
import dashscope
dashscope.api_key = "sk-969f4200d53442a2a1733d1c0b1fb330"
async def get_embedding(texts: List[str], batch_size: int = 8) -> List[List[float]]:
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
import numpy as np
import faiss

class EntityVectorStorage:
    def __init__(self, npz_path: str):
        data = np.load(npz_path)
        self.ids = data["node_ids"]
        self.labels = data["node_labels"]
        self.embeddings = data["embeddings"].astype('float32')

        self.label_indices = {}  # 为每个label创建单独的faiss索引
        self.label_id_maps = {}  # 保存每个label对应的ids

        unique_labels = np.unique(self.labels)
        for label in unique_labels:
            # 获取当前label对应的数据
            indices = np.where(self.labels == label)[0]
            embeddings_subset = self.embeddings[indices]
            ids_subset = self.ids[indices]
            # 创建并保存faiss索引
            index = faiss.IndexFlatL2(embeddings_subset.shape[1])
            index.add(embeddings_subset)
            self.label_indices[label] = index
            self.label_id_maps[label] = ids_subset
        # 构建全局索引（可选）
        self.global_index = faiss.IndexFlatL2(self.embeddings.shape[1])
        self.global_index.add(self.embeddings)
    async def query(self, text: str, label: str = None, top_k: int = 5):
        query_emb = await get_embedding([text])
        query_emb = np.array(query_emb).astype('float32')
        if label and label in self.label_indices:
            index = self.label_indices[label]
            id_map = self.label_id_maps[label]
            D, I = index.search(query_emb, top_k)
            print(f"查询文本: {text}")
            print(f"检索到的实体索引: {I[0]}")
            print(f"检索到的实体距离: {D[0]}")
            results = [{"entity_name": id_map[i], "label": label} for i in I[0]]
        elif label and label not in self.label_indices:
            print(f"⚠️ 指定的label '{label}' 不存在，返回空结果。")
            results = []
        else:  # 未指定label，使用全局索引
            D, I = self.global_index.search(query_emb, top_k)
            results = [{"entity_name": self.ids[i], "label": self.labels[i]} for i in I[0]]
        return results

class RelationVectorStorage:
    def __init__(self, npz_path: str):
        data = np.load(npz_path)
        self.ids = data["keys"]
        self.embeddings = data["embeddings"]
        self.index = faiss.IndexFlatL2(self.embeddings.shape[1])
        self.index.add(self.embeddings)

    async def query(self, text: str, top_k: int = 5):
        query_emb = await get_embedding([text])  # 使用你已经实现的 get_embedding
        query_emb = np.array(query_emb).astype('float32')
        D, I = self.index.search(query_emb, top_k)
        print(f"查询文本: {text}")
        print(f"检索到的关系索引: {I[0]}")
        print(f"检索到的关系距离: {D[0]}")
        return [{"relation_name": self.ids[i]} for i in I[0]]
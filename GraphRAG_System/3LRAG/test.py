import asyncio
from retriever.query_entity_extractor import extract_query_entities
from retriever.query_graph_resolver import QueryGraphResolver
from retriever.query_relation_extractor import extract_entity_relations
from storage.entity_vector_storage import EntityVectorStorage
from storage.neo4j_client import Neo4jClient
import json
async def main():
    query = "在治疗一种由牙周炎引发的牙髓组织炎症过程中，所使用的消毒药物是否也用于一种针对儿童牙齿深窝沟的预防性措施中？如果是，请描述该药物在两种情况下的具体用途及其作用机制"
    
    # 1) 构建初始 Query‑Graph（实体+关系）
    entities = extract_query_entities(query)
    graph=extract_entity_relations(query, entities)
    print("Initial Query Graph:")
    print(graph)
    # 2) 初始化存储与客户端
    vdb = EntityVectorStorage("/home/lym/GraphRAG4OralHealth/GraphRAG_System/data/node_properties_embeddings_typed.npz")
    neo4j_client = Neo4jClient(
        url="bolt://127.0.0.1:9687",
        user="neo4j",
        password="medical_neo4j"
    )
    # 3) 用QueryGraphResolver补全图信息
    resolver = QueryGraphResolver(vdb, neo4j_client)
    resolved = await resolver.resolve(graph)

    prediction=[d['name'] for d in resolved['entities']]

asyncio.run(main())

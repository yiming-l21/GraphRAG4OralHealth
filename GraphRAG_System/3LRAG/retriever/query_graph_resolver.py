# utils/query_graph_resolver.py
import asyncio
from typing import List, Dict

class QueryGraphResolver:
    def __init__(self, vdb, neo4j_client):
        """
        vdb: EntityVectorStorage 实例，用于 entity_linker(description)
        neo4j_client: Neo4jClient 实例，用于 entity_by_relation
        """
        self.vdb = vdb
        self.client = neo4j_client
    async def entity_linker_by_id(self, entity_id: str) -> str:
        """根据实体 ID 查询实体名称"""
        cypher = "MATCH (a) WHERE a.名称 = $entity_id RETURN a.名称 AS name"
        result = self.client.run(cypher, entity_id=entity_id)
        if result and isinstance(result, list):
            return result[0].get("name")
        return None
    async def entity_linker(self, label,description: str) -> str:
        """向量检索，返回最匹配的实体名称"""
        if not description:
            return None
        results = await self.vdb.query(description,label, top_k=1)
        return results[0]["entity_name"] if results else None

    def entity_by_relation(self, seed_name: str, relation: str, direction: str = "out") -> str:
        """
        在 Neo4j 中执行关系检索。
        direction="out": (seed)-[:relation]->(x)
        direction="in" : (x)-[:relation]->(seed)
        返回第一个匹配节点的 name。
        """
        if direction == "out":
            cypher = (
                f"MATCH (a {{名称: $seed}})-[r:`{relation}`]->(b) "
                "RETURN b.名称 AS name LIMIT 1"
            )
        else:
            cypher = (
                f"MATCH (b)-[r:`{relation}`]->(a {{名称: $seed}}) "
                "RETURN b.名称 AS name LIMIT 1"
            )

        print(f"Executing Cypher: {cypher} with seed: {seed_name}")

        # 修改这一段，result 是一个 list
        result = self.client.run(cypher, seed=seed_name)

        # 取第一个返回项
        if result and isinstance(result, list):
            return result[0].get("name")
        return None


    async def resolve(self, query_graph: Dict) -> Dict:
        """
        query_graph:
        {
          "entities": [
            {"name": "...", "type": "...", "description": "..."},
            ...
          ],
          "relations": [
            {"head": 0, "relation": "...", "tail": 1},
            ...
          ]
        }
        """
        entities = query_graph["entities"]
        relations = query_graph["relations"]

        # 1) Seed by description
        for ent in entities:
            if ent["name"] == "?" and ent.get("description"):
                name = await self.entity_linker(ent['type'],ent["description"])
                print(f"Entity linker result: {name}")
                if name:
                    ent["name"] = name
            # else:
            #     #判断name是否在数据库中
            #     name = await self.entity_linker_by_id(ent["name"])
            #     print(f"Entity linker result: {name}")
            #     if name:
            #         ent["name"] = name
            #     else:
            #         print(f"Entity linker failed: {ent['name']} not found in DB")
            #         ent["name"] = "?"

        # 2) Iteratively fill via relations
        filled = True
        while filled:
            filled = False
            for rel in relations:
                h_idx, t_idx = rel["head"], rel["tail"]
                rel_label = rel["relation"]
                head_name = entities[h_idx]["name"]
                tail_name = entities[t_idx]["name"]

                # head→tail
                if head_name != "?" and tail_name == "?":
                    name = self.entity_by_relation(head_name, rel_label, direction="out")
                    print(f"Head to tail: {head_name} -[{rel_label}]-> [{name}]")
                    if name:
                        entities[t_idx]["name"] = name
                        filled = True

                # tail→head
                if tail_name != "?" and head_name == "?":
                    name = self.entity_by_relation(tail_name, rel_label, direction="in")
                    print(f"Tail to head: {tail_name} -[{rel_label}]-> [{name}]")
                    if name:
                        entities[h_idx]["name"] = name
                        filled = True

        return {"entities": entities, "relations": relations}

from neo4j import GraphDatabase

class Neo4jClient:
    def __init__(self, url: str, user: str, password: str):
        self.driver = GraphDatabase.driver(url, auth=(user, password))

    def run(self, cypher: str, **params) -> list[dict]:
        """
        通用的 cypher 执行接口，返回 list[dict]
        """
        with self.driver.session() as session:
            result = session.run(cypher, **params)
            return [record.data() for record in result]

    def search_entity(self, mention: str, topk: int = 5) -> list[dict]:
        """
        原来的实体检索，根据名称或别名模糊匹配
        """
        query = (
            "MATCH (e) "
            "WHERE toLower(e.name) CONTAINS $mention "
            "   OR any(alias IN e.alias WHERE toLower(alias) CONTAINS $mention) "
            "RETURN e.name AS name, e.id AS id, labels(e) AS labels "
            "LIMIT $topk"
        )
        return self.run(query, mention=mention.lower(), topk=topk)

    def search_by_relation(
        self,
        seed: str,
        relation: str,
        direction: str = "out",
        topk: int = 1
    ) -> list[str]:
        """
        根据 seed 实体和关系，沿着出/入 边 找到下一个实体的 name
        direction="out": (seed)-[:relation]->(x)
        direction="in" : (x)-[:relation]->(seed)
        返回 topk 个匹配的 name 列表
        """
        if direction == "out":
            cypher = (
                f"MATCH (a {{name: $seed}})-[r:`{relation}`]->(b) "
                "RETURN b.name AS name LIMIT $topk"
            )
        else:
            cypher = (
                f"MATCH (b)-[r:`{relation}`]->(a {{name: $seed}}) "
                "RETURN b.name AS name LIMIT $topk"
            )
        records = self.run(cypher, seed=seed, topk=topk)
        return [r["name"] for r in records]

    def close(self):
        """关闭 driver 连接"""
        self.driver.close()

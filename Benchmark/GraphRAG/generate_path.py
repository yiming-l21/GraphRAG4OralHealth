from neo4j import GraphDatabase
import json
import random

# 数据库连接信息
uri = "bolt://localhost:9687"
username = "neo4j"
password = "medical_neo4j"

# 初始化 Neo4j 驱动
driver = GraphDatabase.driver(uri, auth=(username, password))

# === 获取对应 hop 类型的查询模板 ===
def get_query_template(hop_type: str):
    """根据 hop 类型返回对应的 Cypher 查询模板"""
    if hop_type == "1-hop":
        return """
        MATCH p=(startNode)-[r]->(endNode)
        RETURN p
        LIMIT $limit
        """
    elif hop_type == "2-hop":
        return """
        // 查询4跳路径，关系类型出现频率尽量均匀，每个子查询限制100条
        MATCH p=(startNode)-[r:使用器械]-(endNode)
        WHERE 
          size([rel IN relationships(p) WHERE type(rel) = '包含']) <= 1
          AND (size([rel IN relationships(p) WHERE type(rel) = '引用']) = 0 
               OR size([rel IN relationships(p) WHERE type(rel) = '引用']) = 2)
        RETURN p
        LIMIT 100
        UNION
        MATCH p=(startNode)-[r:使用药物]-(endNode)
        WHERE 
          size([rel IN relationships(p) WHERE type(rel) = '包含']) <= 1
          AND (size([rel IN relationships(p) WHERE type(rel) = '引用']) = 0 
               OR size([rel IN relationships(p) WHERE type(rel) = '引用']) = 2)
        RETURN p
        LIMIT 100
        UNION
        MATCH p=(startNode)-[r:包含]-(endNode)
        WHERE 
          size([rel IN relationships(p) WHERE type(rel) = '包含']) <= 1
          AND (size([rel IN relationships(p) WHERE type(rel) = '引用']) = 0 
               OR size([rel IN relationships(p) WHERE type(rel) = '引用']) = 2)
        RETURN p
        LIMIT 100
        UNION
        MATCH p=(startNode)-[r:包含组成]-(endNode)
        WHERE 
          size([rel IN relationships(p) WHERE type(rel) = '包含']) <= 1
          AND (size([rel IN relationships(p) WHERE type(rel) = '引用']) = 0 
               OR size([rel IN relationships(p) WHERE type(rel) = '引用']) = 2)
        RETURN p
        LIMIT 100
        UNION
        MATCH p=(startNode)-[r:就诊]-(endNode)
        WHERE 
          size([rel IN relationships(p) WHERE type(rel) = '包含']) <= 1
          AND (size([rel IN relationships(p) WHERE type(rel) = '引用']) = 0 
               OR size([rel IN relationships(p) WHERE type(rel) = '引用']) = 2)
        RETURN p
        LIMIT 100
        UNION
        MATCH p=(startNode)-[r:引用]-(endNode)
        WHERE 
          size([rel IN relationships(p) WHERE type(rel) = '包含']) <= 1
          AND (size([rel IN relationships(p) WHERE type(rel) = '引用']) = 0 
               OR size([rel IN relationships(p) WHERE type(rel) = '引用']) = 2)
        RETURN p
        LIMIT 100
        UNION
        MATCH p=(startNode)-[r:治疗]-(endNode)
        WHERE 
          size([rel IN relationships(p) WHERE type(rel) = '包含']) <= 1
          AND (size([rel IN relationships(p) WHERE type(rel) = '引用']) = 0 
               OR size([rel IN relationships(p) WHERE type(rel) = '引用']) = 2)
        RETURN p
        LIMIT 100
        UNION
        MATCH p=(startNode)-[r:预防]-(endNode)
        WHERE 
          size([rel IN relationships(p) WHERE type(rel) = '包含']) <= 1
          AND (size([rel IN relationships(p) WHERE type(rel) = '引用']) = 0 
               OR size([rel IN relationships(p) WHERE type(rel) = '引用']) = 2)
        RETURN p
        LIMIT 100
        """
    elif hop_type == "multi-hop":
        return """
        // 疾病 → 治疗 → 使用药物 → 药物
        MATCH p1=(d:口腔疾病)-[:治疗]-(t1:治疗)-[:使用药物]-(m:药物)-[:使用药物]-(t2:治疗)
        RETURN p1
        LIMIT $limit
        UNION
        // 疾病 → 治疗 → 使用器械 → 器械
        MATCH p2=(d:口腔疾病)-[:治疗]-(t:治疗)-[:使用器械]-(i:器械)<-[:使用器械]-(c:检查)
        RETURN p2
        LIMIT $limit
        UNION
        // 疾病 → 预防 → 使用药物 → 药物
        MATCH p3=(d:口腔疾病)-[:治疗]-(t:治疗)-[:使用药物]-(m:药物)<-[:使用药物]-(pre:预防)
        RETURN p3
        LIMIT $limit
        UNION
        // 疾病 → 包含 → 检查 → 使用器械 → 器械 ← 使用器械 ← 治疗
        MATCH p4=(d:口腔疾病)-[:包含]-(c:检查)-[:使用器械]-(i:器械)-[:使用器械]-(t:治疗)
        RETURN p4
        LIMIT $limit
        UNION
        // 疾病 → 治疗 → 使用器械 → 器械 ← 使用器械 ← 治疗
        MATCH p5=(d:口腔疾病)-[:治疗]-(t1:治疗)-[:使用器械]-(i:器械)-[:使用器械]-(t2:治疗)
        WHERE t1 <> t2
        RETURN p5
        LIMIT $limit
        UNION
        // 疾病 → 治疗 → 使用药物 → 药物 ← 使用药物 ← 预防
        MATCH p6=(d:口腔疾病)-[:治疗]-(t:治疗)-[:使用药物]-(m:药物)-[:使用药物]-(prevention:预防)
        RETURN p6
        LIMIT $limit
        """
    else:
        raise ValueError("未知的 hop 类型，请选择 '1-hop', '2-hop' 或 'multi-hop'")

# === 生成路径函数 ===
def generate_paths(tx, hop_type: str, limit=50000):
    """根据 hop 类型生成路径"""
    query_template = get_query_template(hop_type)
    
    # 执行查询并获取路径
    all_paths = []
    result = tx.run(query_template, limit=limit)
    all_paths += [record["p"] for record in result]

    return all_paths

# === 计算节点属性的字符串总长度 ===
def calculate_node_properties_length(node):
    total_length = 0
    for key, value in node.items():
        if isinstance(value, str):  # 只计算字符串类型的属性
            total_length += len(value)
    return total_length

# === 清洗路径：去除包含属性总长度小于60的节点所对应的路径 ===
def clean_paths(paths, min_length=60):
    cleaned_paths = []

    for path in paths:
        include_path = True
        for node in path.nodes:
            if calculate_node_properties_length(node) < min_length:
                include_path = False
                break
        
        if include_path:
            cleaned_paths.append(path)

    return cleaned_paths

# === 将路径解析成 JSON 格式 ===
def path_to_json(path):
    nodes = []
    relationships = []

    # 解析路径中的节点和关系
    for i, node in enumerate(path.nodes):
        node_info = {
            "id": node.id,
            "labels": list(node.labels),
            "properties": dict(node.items())
        }
        nodes.append(node_info)

        if i < len(path.relationships):
            rel = path.relationships[i]
            relationship_info = {
                "type": rel.type,
                "start_node": node.id,
                "end_node": path.nodes[i + 1].id if i + 1 < len(path.nodes) else None
            }
            relationships.append(relationship_info)

    return {"nodes": nodes, "relationships": relationships}

# === 保存路径到 JSON 文件 ===
def save_paths_to_json(paths, filename="paths.json"):
    with open(filename, mode='w', encoding='utf-8') as file:
        paths_json = [path_to_json(path) for path in paths]
        json.dump(paths_json, file, ensure_ascii=False, indent=4)

# === 主函数 ===
def main():
    output_files = {
        "1-hop": "paths_1hop.json",
        "2-hop": "paths_2hop.json",
        "multi-hop": "paths_multihop.json"
    }

    with driver.session() as session:
        for hop_type, output_file in output_files.items():
            print(f"正在生成 {hop_type} 路径...")
            
            # 生成路径
            paths = session.read_transaction(generate_paths, hop_type=hop_type, limit=50000)
            
            # 清洗路径
            cleaned_paths = clean_paths(paths)
            print(f"{hop_type} 路径清洗后剩余数量: {len(cleaned_paths)}")
            
            # 随机化路径
            random.shuffle(cleaned_paths)
            
            # 保存路径到文件
            save_paths_to_json(cleaned_paths, filename=output_file)
            print(f"{hop_type} 路径已保存为 {output_file}")

# 运行主函数
if __name__ == "__main__":
    main()
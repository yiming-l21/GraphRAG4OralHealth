label="文献"
import json
from py2neo import Graph,Node,Relationship
def get_node_block(paper):
    node_block={}
    node_block["作者"]=paper["作者"]
    node_block["标题"]=paper["题目"]
    node_block["摘要"]=paper["摘要"]
    node_block["作者部门"]=paper["作者部门"]
    node_block["期刊信息"]=paper["期刊信息"]
    return node_block
def find_or_create_node(graph, label, property_key, property_value):
        """
        查找或创建指定标签和属性值的节点。
        
        :param label: 节点标签
        :param property_key: 属性键
        :param property_value: 属性值
        :return: 找到或创建的节点
        """
        query = f"MATCH (n:{label}) WHERE n.{property_key} = $value RETURN n"
        node = graph.run(query, value=property_value).data()

        if not node:
            return None

        return node[0]['n']
def convert_json2nodes(graph,data, label, existing_nodes=None, depth=0):
    relations = []
    nodes = []
    for paper in data:
        node=get_node_block(paper)
        node_paper=Node(label, **node)
        nodes.append(node_paper)
        if "对齐疾病" in paper.keys():
            for disease in paper["对齐疾病"]:
                node_dicease = find_or_create_node(graph, "口腔疾病", "名称", disease)
                if node_dicease is not None and node_paper is not None:
                    relation = Relationship(node_dicease, "引用", node_paper)
                    relations.append(relation)
                else:
                    print(f"[警告] 疾病关系创建失败: {disease}")
        if "对齐药物" in paper.keys():
            for medicine in paper["对齐药物"]:
                node_medicine = find_or_create_node(graph, "药物", "名称", medicine)
                if node_medicine is not None and node_paper is not None:
                    relation = Relationship(node_medicine, "引用", node_paper)
                    relations.append(relation)
                else:
                    print(f"[警告] 药物关系创建失败: {medicine}")
        if "对齐器械" in paper.keys():
            for equipment in paper["对齐器械"]:
                node_equipment = find_or_create_node(graph, "器械", "名称", equipment)
                if node_equipment is not None and node_paper is not None:
                    relation = Relationship(node_equipment, "引用", node_paper)
                    relations.append(relation)
                else:
                    print(f"[警告] 器械关系创建失败: {equipment}")

        if "对齐治疗方案" in paper.keys():
            for treatment in paper["对齐治疗方案"]:
                node_treatment = find_or_create_node(graph, "治疗", "名称", treatment)
                if node_treatment is not None and node_paper is not None:
                    relation = Relationship(node_treatment, "引用", node_paper)
                    relations.append(relation)
                else:
                    print(f"[警告] 治疗关系创建失败: {treatment}")

        if "对齐预防方案" in paper.keys():
            for prevention in paper["对齐预防方案"]:
                node_prevention = find_or_create_node(graph, "预防", "名称", prevention)
                if node_prevention is not None and node_paper is not None:
                    relation = Relationship(node_prevention, "引用", node_paper)
                    relations.append(relation)
                else:
                    print(f"[警告] 预防关系创建失败: {prevention}")

        if "对齐检查" in paper.keys():
            for examination in paper["对齐检查"]:
                node_examination = find_or_create_node(graph, "检查", "名称", examination)
                if node_examination is not None and node_paper is not None:
                    relation = Relationship(node_examination, "引用", node_paper)
                    relations.append(relation)
                else:
                    print(f"[警告] 检查关系创建失败: {examination}")
    return nodes, relations
def store_nodes(data,label,url,username,password):
    graph = Graph(url, auth=(username, password))
    nodes,relations=convert_json2nodes(graph,data,label)
    for node in nodes:
        graph.create(node)
    for relation in relations:
        graph.create(relation)
    print("数据已保存到neo4j")
    return
with open("./wanfang_abstract_sampled_updated.json", "r", encoding="utf-8") as f:
    data = json.load(f)
print(len(data))
store_nodes(data,label,url="bolt://localhost:9687",username="neo4j",password="medical_neo4j")
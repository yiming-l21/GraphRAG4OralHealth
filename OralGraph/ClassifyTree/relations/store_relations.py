import os
from py2neo import Graph, NodeMatcher, Relationship, Node
class Neo4jRelationStorage:
    """
    用于将关系存储到 Neo4j 数据库的工具类。
    """
    def __init__(self, url, username, password):
        """
        初始化 Neo4j 数据库连接。
        
        :param url: Neo4j 数据库连接地址
        :param username: 数据库用户名
        :param password: 数据库密码
        """
        self.graph = Graph(url, auth=(username, password))
        self.node_matcher = NodeMatcher(self.graph)

    def find_or_create_node(self, label, property_key, property_value):
        """
        查找或创建指定标签和属性值的节点。
        
        :param label: 节点标签
        :param property_key: 属性键
        :param property_value: 属性值
        :return: 找到或创建的节点
        """
        query = f"MATCH (n:{label}) WHERE n.{property_key} = $value RETURN n"
        node = self.graph.run(query, value=property_value).data()

        if not node:
            return None

        return node[0]['n']

    def store_relations(self, relation_list, node1_label, node2_label, relation_type, property_key):
        """
        将关系列表存储到 Neo4j 数据库中。
        
        :param relation_list: 关系列表，格式为 [[节点1名称, 节点2名称], ...]
        :param node1_label: 节点1的标签
        :param node2_label: 节点2的标签
        :param relation_type: 关系类型（字符串）
        """
        for [node1_name, node2_name] in relation_list:
            # 查找或创建节点1
            node1 = self.find_or_create_node(node1_label, property_key, node1_name)
            if not node1:
                print(f"节点1（标签：{node1_label}，名称：{node1_name}）不存在")
                continue
            # 查找或创建节点2
            node2 = self.find_or_create_node(node2_label, property_key, node2_name)
            if not node2:
                print(f"节点2（标签：{node2_label}，名称：{node2_name}）不存在")
                continue
            
            # 创建或更新关系
            relationship = Relationship(node1, relation_type, node2)
            self.graph.merge(relationship)  # 使用 merge 确保不会重复创建关系
        
        print(f"关系数据（节点1标签：{node1_label}，节点2标签：{node2_label}，关系类型：{relation_type}）已成功保存到 Neo4j")

def process_files(directory, neo4j_storage):
    """
    处理目录下的所有关系文件，并将它们保存到 Neo4j 数据库中。
    
    :param directory: 包含关系文件的目录路径
    :param neo4j_storage: Neo4jRelationStorage 实例
    """
    for filename in os.listdir(directory):
        if filename.endswith(".txt"):
            file_path = os.path.join(directory, filename)
            with open(file_path, "r", encoding="utf-8") as file:
                data = file.read()
            entity_list = data.split("\n")
            relation_list = []
            for entity in entity_list:
                if entity:
                    item=entity.split(" ")
                    if len(item)!=2:
                        print(f"文件{filename}中的数据格式不正确：{entity}")
                        continue
                    relation_list.append(entity.split(" "))
            
            # 根据文件名确定节点标签和关系类型
            if "就诊" in filename:
                node1_label = "口腔疾病"
                node2_label = "科室"
                relation_type = "就诊"
            elif "包含组成" in filename:
                node1_label = "器械"
                node2_label = "器械"
                relation_type = "包含组成"
            elif "检查使用器械" in filename:
                node1_label = "检查"
                node2_label = "器械"
                relation_type = "使用器械"
            elif "治疗使用器械llm" in filename:
                node1_label = "治疗"
                node2_label = "器械"
                relation_type = "使用器械"
            elif "治疗使用药物llm" in filename:
                node1_label = "治疗"
                node2_label = "药物"
                relation_type = "使用药物"
            elif "治疗疾病llm" in filename:
                node1_label = "治疗"
                node2_label = "口腔疾病"
                relation_type = "治疗"
            elif "预防使用器械" in filename:
                node1_label = "预防"
                node2_label = "器械"
                relation_type = "使用器械"
            elif "预防使用药物" in filename:
                node1_label = "预防"
                node2_label = "药物"
                relation_type = "使用药物"
            elif "预防疾病" in filename:
                node1_label = "预防"
                node2_label = "口腔疾病"
                relation_type = "预防"
            elif "疾病表现为症状" in filename:
                node1_label = "口腔疾病"
                node2_label = "症状"
                relation_type = "表现为"
            else:
                print(f"未知文件类型：{filename}")
                continue
            
            neo4j_storage.store_relations(relation_list, node1_label, node2_label, relation_type, "名称")


# 初始化 Neo4j 存储工具
neo4j_storage = Neo4jRelationStorage(
    url="bolt://localhost:9687",
    username="neo4j",
    password="medical_neo4j"
)

# 处理关系文件
process_files("./", neo4j_storage)
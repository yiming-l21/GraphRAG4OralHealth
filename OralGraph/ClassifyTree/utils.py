import json
import argparse
from py2neo import Graph,Node,Relationship
global keys
keys=set()
'''遍历所有疾病，获取疾病术语表，也可以获取所有属性词表'''
def extract_disease_keys(data, depth=0):
    disease_keys = []
    if depth%2==0:
        for key in data.keys():
            keys.add(key)
    for key, value in data.items():
        print(key,depth)
        if isinstance(value, dict):
            if depth%2==0:
                if key == "包含":
                    print("包含")
                    disease_keys.extend(extract_disease_keys(value, depth+1))
            else:
                disease_keys.append((key,depth))
                disease_keys.extend(extract_disease_keys(value, depth+1))
    return disease_keys
'''修改JSON文件的实体属性值'''
def revise_property_keys(data):
    new_data = {}
    for key, value in data.items():
        if isinstance(value, dict):
            key= "包含" if key == "包括" else key
            new_data[key] = revise_property_keys(value)
        else:
            key="用法用量" if key=="用法" or key=="治疗方法" else key
            key="适用症" if key =="临床应用" or key=="适应症" or key== "功能主治" or key=="适用病症" else key
            key ="成份" if key=="成分" else key
            key = "预防机制" if key=="药理作用" or key =="机制作用" or key=='作用机制' else key
            key="禁忌" if key == "禁忌症" else key
            key ="处方组成" if key =="方剂组成" else key
            key="使用器械" if key=="使用设备" else key
            new_data[key] = value
    return new_data
def get_node_block(key,value):
    node_block={}
    node_block["名称"]=key
    for k,v in value.items():
        if k!="包含":
            node_block[k]=str(v)
    return node_block
def convert_json2nodes(data, label, existing_nodes=None, depth=0):
    if existing_nodes is None:
        existing_nodes = {}
        
    relations = []
    nodes = []
    
    for key, value in data.items():
        # Use a unique identifier for the node, such as 'key'
        if key not in existing_nodes:
            node_block = get_node_block(key, value)
            node = Node(label, **node_block)
            existing_nodes[key] = node
            nodes.append(node)
        else:
            node = existing_nodes[key]
        
        for k, v in value.items():
            if k == "包含":
                for k1, v1 in v.items():
                    if k1 not in existing_nodes:
                        node1_block = get_node_block(k1, v1)
                        node1 = Node(label, **node1_block)
                        existing_nodes[k1] = node1
                        nodes.append(node1)
                    else:
                        node1 = existing_nodes[k1]

                    relation = Relationship(node, "包含", node1)
                    relations.append(relation)
                
                sub_nodes, sub_relations = convert_json2nodes(v, label, existing_nodes, depth + 1)
                nodes.extend(sub_nodes)
                relations.extend(sub_relations)
    
    return nodes, relations
def store_nodes(data,label,url,username,password):
    graph = Graph(url, auth=(username, password))
    nodes,relations=convert_json2nodes(data,label)
    for node in nodes:
        graph.create(node)
    for relation in relations:
        graph.create(relation)
    print("数据已保存到neo4j")
    return
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="extract disease keys from json")
    parser.add_argument("--json_path", type=str,  help="path to the json file")
    parser.add_argument("--output_path", type=str,  help="path to the output json file")
    parser.add_argument("--output_info",type=bool,default=False,help="whether to output the information")
    parser.add_argument("--clean_data",type=bool,default=False,help="whether to clean the data")
    parser.add_argument("--store_neo4j",type=str,default=False,help="whether to store the data into neo4j")
    args = parser.parse_args()
    with open(args.json_path, "r") as f:
        data = json.load(f)
    if args.clean_data:
        revised_data = revise_property_keys(data[list(data.keys())[0]])
        revised_data={list(data.keys())[0]:revised_data}
        with open(args.output_path, 'w', encoding='utf-8') as f:
            json.dump(revised_data, f, ensure_ascii=False, indent=4)
        print("修改后的数据已保存到 {}".format(args.output_path))
    if args.output_info:
        extracted_keys=extract_disease_keys(data[list(data.keys())[0]])
        print(extracted_keys)
    if args.store_neo4j:
        label=args.store_neo4j
        store_nodes(data,label,url="bolt://localhost:9687",username="neo4j",password="medical_neo4j")
    print(keys)
    
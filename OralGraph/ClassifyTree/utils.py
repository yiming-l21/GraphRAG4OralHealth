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
                if key in ["预防措施","治疗方法","病因描述","临床表现","疾病定义","诊断原则","病理描述"]:
                    continue
                disease_keys.append((key,depth))
                disease_keys.extend(extract_disease_keys(value, depth+1))
    return disease_keys
'''修改JSON文件的实体属性值'''
def revise_property_keys(data):
    new_data = {}
    for key, value in data.items():
        print(key)
        if isinstance(value, dict):
            key= "包含" if key == "包括" else key
            new_data[key] = revise_property_keys(value)
        else:
            key = "预防措施" if key=="预防" or key =="预防方法" or key=='作用机制' else key
            key = "治疗方法" if key=="治疗" or key =="治疗原则" or key=="治疗原则与方法" else key
            key = "病因描述" if key=="病因及发病机制" or key =="原因" or key =="病因" or key == "发病机制" or key == "病因和发病机制" else key
            key = "临床表现" if key=="主要表现" or key == "口腔表现" else key
            key = "疾病定义" if key=="定义"  else key
            key = "诊断原则" if key =="诊断" or key == "诊断方法" or key == "临床表现与诊断" or key=="诊断要点" or key == "诊断与鉴别诊断" else key
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
    parser.add_argument("--store_neo4j",type=str,default=False,help="label of the neo4j node")
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
    
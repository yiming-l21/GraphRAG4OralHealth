import json

with open("./medicine_revised.json","r") as f:
    data = json.load(f)
global keys
keys=set()
'''遍历所有疾病，获取疾病术语表，也可以获取所有属性词表'''
def extract_disease_keys(data, depth=0):
    disease_keys = []
    if depth%2==0:
        for key in data.keys():
            keys.add(key)
    for key, value in data.items():
        if isinstance(value, dict):
            if depth%2==0:
                if key == "包含":
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
            key="适用症" if key =="临床应用" or key=="适应症" or key== "功能主治" else key
            key ="成份" if key=="成分" else key
            key = "作用机制" if key=="药理作用" or key =="机制作用" else key
            key="禁忌" if key == "禁忌症" else key
            key ="处方组成" if key =="方剂组成" else key
            new_data[key] = value
    return new_data
#获取词表
extract_disease_keys(data['口腔临床药物'])
print(keys)
#修改属性值
# revised_data = revise_property_keys(data['口腔临床药物'])
# revised_data={"口腔临床药物":revised_data}
# with open('./medicine_revised.json', 'w', encoding='utf-8') as f:
#     json.dump(revised_data, f, ensure_ascii=False, indent=4)

# print("修改后的数据已保存到 medicine_revised.json")

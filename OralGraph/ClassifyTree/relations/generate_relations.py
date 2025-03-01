import json
import dashscope
from tqdm import tqdm

dashscope.api_key = "sk-969f4200d53442a2a1733d1c0b1fb330"

def call_large_model(prompt):
    messages = [
        {"role": "system", "content": "你是一个医学知识图谱构建专家。"},
        {"role": "user", "content": prompt}
    ]
    try:
        response = dashscope.Generation.call(
            model="qwen-plus",
            messages=messages,
            result_format='message'
        )
        response_text = response['output']['choices'][0]['message']['content'].strip()
        return response_text
    except Exception as e:
        print(f"调用模型失败: {e}")
        return '不确定'

def format_entity_info(info):
    parts = []
    for k, v in info.items():
        if isinstance(v, dict):
            nested = ', '.join([f"{sub_k}: {sub_v}" for sub_k, sub_v in v.items()])
            parts.append(f"{k}: {nested}")
        elif isinstance(v, list):
            parts.append(f"{k}: {', '.join(map(str, v))}")
        else:
            parts.append(f"{k}: {v}")
    return '； '.join(parts)

def generate_prompt(head_entity, head_info, tail_entity, tail_info, relation_name, relation_definition):
    head_info_str = format_entity_info(head_info)
    tail_info_str = format_entity_info(tail_info)
    return f"""请严格根据以下信息和口腔医学知识判断两个实体间是否存在“{relation_name}”关系。
要求只有当头实体无法与尾实体及子集中的任何一个实体建立关系时，才判定头实体与尾实体不存在关系。也就是说只要头实体与尾实体及子集中的任何一个实体存在关系，就判定头实体与尾实体存在关系
关系定义：{relation_definition}
头实体名称：{head_entity}
头实体属性：{head_info_str}
尾实体名称：{tail_entity}
尾实体属性：{tail_info_str}
答案只能是“是”或“否”，无需解释。请不要输出任何无关信息"""
def generate_prompt1(head_entity, head_info, tail_entity, tail_info, relation_name, relation_definition):
    head_info_str = format_entity_info(head_info)
    tail_info_str = format_entity_info(tail_info)
    return f"""请严格根据以下信息和口腔医学知识判断两个实体间是否存在“{relation_name}”关系。注意以下信息可能不完整，还需要你的专业知识辅助判断。
关系定义：{relation_definition}
头实体名称：{head_entity}
头实体属性：{head_info_str}
尾实体名称：{tail_entity}
尾实体属性：{tail_info_str}
答案只能是“是”或“否”，无需解释。请不要输出任何无关信息"""
def should_prune(head_entity, head_info, tail_entity, tail_info, relation_name, relation_definition):
    """
    判断是否需要剪枝。
    - 调用大模型判断当前头实体和尾实体是否可能存在指定关系。
    - 如果大模型明确返回“否”，则剪枝；否则不剪枝。
    """
    prompt = generate_prompt(head_entity, head_info, tail_entity, tail_info, relation_name, relation_definition)
    response = call_large_model(prompt)
    print(f"判断：{head_entity} {tail_entity} {response}")
    return '否' in response

def get_json_block(data,property_list):
    """
    将树状结构的 JSON 数据展开为扁平列表。
    """
    json_block = {}
    for key, value in data.items():
        saved_info = {k: v for k, v in value.items() if k in property_list}
        json_block[key] = saved_info
        if '包含' in value:
            child_block = get_json_block(value['包含'], property_list)
            json_block.update(child_block)
    return json_block

def traverse_tail_tree(tail_data, head_entity, head_info, relation_name, relation_definition, output_file, progress_bar):
    """
    遍历尾实体的树状结构，进行剪枝和关系判断。
    """
    for tail_entity, tail_info in tail_data.items():
        if tail_entity == '口腔科急救药物' or tail_entity == '血管硬化药':
            print(f"剪枝new：{head_entity} {tail_entity}")
            continue
        saved_info = {k: v for k, v in tail_info.items() if k == '处方组成' or k=='特性描述' or k=='定义' or k=='制剂规格'}
        flag=False
        if should_prune(head_entity, head_info, tail_entity, saved_info, relation_name, relation_definition):
            print(f"剪枝：{head_entity} {tail_entity}")
            continue  # 剪枝
        else:
            output_file.write(f"{head_entity} {tail_entity}\n")
            progress_bar.update(1)
            flag=True
        if flag==False:
            prompt = generate_prompt1(head_entity, head_info, tail_entity, saved_info, relation_name, relation_definition)
            response = call_large_model(prompt)
            if '是'in response:
                output_file.write(f"{head_entity} {tail_entity}\n")
                progress_bar.update(1)
        if '包含' in tail_info:
            traverse_tail_tree(tail_info['包含'], head_entity, head_info, relation_name, relation_definition, output_file, progress_bar)

def find_relations(head_file, tail_file, relation_name, relation_definition, output_file):
    """
    主函数：生成关系头尾节点对。
    """
    with open(head_file, 'r', encoding='utf-8') as f:
        head_data = json.load(f)
        head_entities = get_json_block(head_data,['制作方法', '治疗分期', '治疗阶段', '矫治特点', '铸造金属全冠设计', '方法', '主要步骤', '操作要点', '修复原则', '治疗特点', '固位方法', '麻醉与体位', '定义', '义眼设计', '疗效标准与预后', '牙根拔除术', '现代发展', '精密附着体的位置', '治疗步骤', '黏结面的处理', '材料特点', '详细步骤', '治疗原则', '术前准备', '瓷贴面的烧烤成形', '修复特点', '使用器械', '修复设计', '矫治设计', '术后处理', '术区处理', '别名', '手术步骤', '操作步骤', '特点', '基牙预备', '附着体的选择', '使用药物', '分类设计', '操作方法', '制作要点', '常用修复材料', '模型准备', '术后护理', '适用人群', '基牙制备', '供牙处理', '临床检查', '黏结', '原理', '目的', '附着体', '与方丝弓矫治器比较', '基本理论与特点', '制作步骤', '上部结构的支持形式', '印模特点', '基托边缘设计', '特性描述', '整形矫治器'])  # 头实体扁平化
        #保存头实体的信息
        with open('head_entities1.json', 'w', encoding='utf-8') as f:
            json.dump(head_entities, f, ensure_ascii=False, indent=4)
    with open(tail_file, 'r', encoding='utf-8') as f:
        tail_data = json.load(f)  # 尾实体保留树状结构
    print(f"头实体总数：{len(head_entities)}")
    print(f"尾实体总数：{count_tail_nodes(tail_data)}")
    total = len(head_entities) * count_tail_nodes(tail_data)
    with open(output_file, 'a', encoding='utf-8') as out_f:
        progress_bar = tqdm(total=total, desc="处理进度", unit="pair")
        for head_entity, head_info in head_entities.items():
            traverse_tail_tree(tail_data, head_entity, head_info, relation_name, relation_definition, out_f, progress_bar)
        progress_bar.close()

def count_tail_nodes(tail_data):
    """
    计算尾实体树状结构的节点总数。
    """
    count = 0
    for value in tail_data.values():
        count += 1
        if '包含' in value:
            count += count_tail_nodes(value['包含'])
    return count

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='自动生成知识图谱关系')
    parser.add_argument('--head', required=True, help='头实体JSON文件路径')
    parser.add_argument('--tail', required=True, help='尾实体JSON文件路径')
    parser.add_argument('--relation', required=True, help='关系名称（如治疗）')
    parser.add_argument('--definition', required=True, help='关系定义（如该治疗方案用于治疗该疾病）')
    parser.add_argument('--output', required=True, help='输出文件路径')
    args = parser.parse_args()
    
    find_relations(args.head, args.tail, args.relation, args.definition, args.output)
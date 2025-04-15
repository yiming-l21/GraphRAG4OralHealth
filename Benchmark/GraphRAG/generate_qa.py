import json
from tqdm import tqdm
import dashscope  # DeepSeek API
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
import random

# 设置API key
dashscope.api_key = "sk-969f4200d53442a2a1733d1c0b1fb330"  # 替换成你的 API key

# === 辅助函数 ===
def load_paths(file_path: str) -> List[Dict]:
    """加载路径数据"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_prompt_template(hop_type: str) -> str:
    """根据 hop 类型返回对应的 prompt 模板"""
    if hop_type == "1-hop":
        return """
基于以上路径信息，生成一个问题，该问题 **必须依赖路径中的所有节点的信息** 来得出答案。确保问题包含了路径中的所有节点（例如，药物、文献、疾病、科室等），且答案只能通过路径中的节点属性来推导出来。
#### 要求：
1. 问题必须**依赖路径中所有节点的信息**，如药物、文献、疾病、科室等。
2. 问题应该包含**节点之间的关系**，例如药物和文献之间的引用关系，疾病和科室之间的就诊关系等。
3. 答案应仅来源于路径中的节点属性，而不依赖于路径外部的任何信息。
4. 保证问题与答案的设计 **不含歧义**，且能够通过路径数据来进行准确回答。
5. 问题不应该包含很多子问题，每一个问题至多包含2个子问题。尽量能够通过一个子问题串联多个节点内容，需要精心设计。
6. 问题中不要全部直接使用节点名称作为关键词，可以部分节点采用用节点的关键属性来描述关键词提问。
最后输出的格式参考以下例子：
问题: [问题内容]
答案: [答案内容]
"""
    elif hop_type == "2-hop":
        return """
基于以上路径信息，生成一个问题，该问题 **必须依赖路径中的所有节点的信息** 来得出答案。确保问题包含了路径中的所有节点（例如，药物、文献、疾病、科室等），且答案只能通过路径中的节点属性来推导出来。
#### 要求：
1. 问题必须**依赖路径中所有节点的信息**，如药物、文献、疾病、科室等。
2. 问题应该包含**节点之间的关系**，例如药物和文献之间的引用关系，疾病和科室之间的就诊关系等。
3. 答案应仅来源于路径中的节点属性，而不依赖于路径外部的任何信息。
4. 保证问题与答案的设计 **不含歧义**，且能够通过路径数据来进行准确回答。
5. 问题不应该包含很多子问题，每一个问题至多包含2个子问题。尽量能够通过一个子问题串联多个节点内容，需要精心设计。
6. 问题中不要全部直接使用节点名称作为关键词，可以部分节点采用用节点的关键属性来描述关键词提问。
7. 问题尽量涉及多跳推理内容。
最后输出的格式参考以下例子：
问题: [问题内容]
答案: [答案内容]
"""
    elif hop_type == "multi-hop":
        return """
请根据以下路径信息设计一个医学问答对，要求如下：

1. **问题必须涉及路径中所有实体（节点）** 的信息，且至少跨越两个不同类型的关系。
2. **问题的发问角度** 应围绕路径起点的实体（如疾病、治疗手段、检查等）进行提问，并通过路径的链条推理到终点实体的内容。
3. **问题中尽量不直接暴露所有实体的“名称”属性**，应当通过实体的描述性属性（如适应症、定义、作用、使用范围）进行语言重构，提升问法的自然性。
4. **答案只能来自路径中的节点属性**，不得引入外部知识。
5. **问题最好具备一定的临床推理复杂度**，如“哪些用于X的手段也出现在Y中”，“用于治疗X的Y类器械是否也用于Z类操作”等。

请用以下格式输出：
问题: [你的问题]
答案: [准确、结构清晰的答案]

举例参考：

路径起点：检查 → 使用器械 → 器械 → 使用器械 ← 治疗 ← 疾病  
问题: 在“牙齿松动度检查”中使用的某种夹持器械是否也应用于治疗以牙体组织磨耗为主要表现的疾病中？如果是，该治疗的操作步骤有哪些？  
答案: “牙齿松动度检查”使用的“口腔用镊、夹”同样被用于“牙磨损”的治疗过程，具体操作为“根管治疗术”，步骤包括预备、消毒、充填、修复等四个阶段。
"""
    else:
        raise ValueError("未知的 hop 类型，请选择 '1-hop', '2-hop' 或 'multi-hop'")

# === 模型调用函数 ===
def call_large_model(prompt: str) -> str:
    """调用大模型生成内容"""
    messages = [
        {"role": "system", "content": "你是一名口腔医学专家，擅长根据医学图谱路径生成高质量的问答对。"},
        {"role": "user", "content": prompt}
    ]
    try:
        response = dashscope.Generation.call(
            model="qwen-plus",
            messages=messages,
            result_format='message'
        )
        return response['output']['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"调用模型失败: {e}")
        return "模型调用失败"

# === 问题和答案生成函数 ===
def generate_question_and_answer(path: dict, hop_type: str) -> dict:
    """根据路径信息生成问答对"""
    # 获取对应 hop 类型的 prompt 模板
    prompt = get_prompt_template(hop_type)
    
    # 添加路径信息到 prompt
    prompt += "\n路径信息:\n" + json.dumps(path, ensure_ascii=False, indent=4)

    # 调用大模型生成答案
    model_output = call_large_model(prompt)

    # 使用 split 解析问题和答案
    try:
        parts = model_output.split("问题:")
        if len(parts) < 2:
            raise ValueError("无法找到 '问题:' 标记")
        
        question_part = parts[1].split("答案:")
        if len(question_part) < 2:
            raise ValueError("无法找到 '答案:' 标记")
        
        question = question_part[0].strip()
        answer = question_part[1].strip()

        # 返回生成的问答对
        return {
            "问题": question,
            "答案": answer,
            "检索文本": path
        }
    except ValueError as e:
        # 如果解析失败，返回错误信息
        return {
            "问题": f"解析失败: {str(e)}",
            "答案": "无法解析答案",
            "检索文本": path
        }

# === 生成所有问答对并保存 ===
def generate_and_save_qna(input_file: str, output_file: str, hop_type: str):
    """生成问答对并保存到文件"""
    paths_data = random.sample(load_paths(input_file), 200)
    qna_list = []

    with ThreadPoolExecutor(max_workers=16) as executor:
        # 异步生成问答对
        futures = {executor.submit(generate_question_and_answer, path, hop_type): path for path in paths_data}

        for future in tqdm(as_completed(futures), total=len(futures), desc=f"生成 {hop_type} 问答对"):
            try:
                qna = future.result()
                qna_list.append(qna)
            except Exception as e:
                print(f"生成问答对失败: {e}")

    # 保存问答对到JSON文件
    with open(output_file, 'w', encoding='utf-8') as outfile:
        json.dump(qna_list, outfile, ensure_ascii=False, indent=4)
    print(f"{hop_type} 问答对已保存为 {output_file}")

# === 主函数 ===
def main():
    input_file = 'paths.json'  # 输入的路径数据文件
    output_files = {
        "1-hop": 'qna_pairs_1hop.json',
        "2-hop": 'qna_pairs_2hop.json',
        "multi-hop": 'qna_pairs_multihop.json'
    }

    # 为每种 hop 类型生成问答对
    for hop_type, output_file in output_files.items():
        generate_and_save_qna(input_file, output_file, hop_type)

# 运行主函数
if __name__ == "__main__":
    main()
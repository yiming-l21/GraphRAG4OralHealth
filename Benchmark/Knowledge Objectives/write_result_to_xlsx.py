import os
import json
import pandas as pd
import glob
from tqdm import tqdm
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.drawing.image import Image
from PIL import Image as PILImage
from io import BytesIO
from matplotlib import pyplot as plt
from matplotlib.ticker import MaxNLocator
import numpy as np
import matplotlib.pyplot as plt

working_directory = "/home/lym/GraphRAG4OralHealth/Benchmark/Knowledge Objectives/Answer"
#获得目录下所有模型名称
def get_model_names(directory_path):
    model_names = []
    for folder_name in os.listdir(directory_path):
        folder_path = os.path.join(directory_path, folder_name)
        if os.path.isdir(folder_path):
            model_names.append(folder_name)
    return model_names
model_list = get_model_names(working_directory)
topic_list=["MedicalHumanity","Clinical","Dentistry","Medical"]
result_dict = {}
for topic in topic_list:
    result_dict[topic] = {}
    json_files = glob.glob(os.path.join("./", topic, "*.json"))
    for file in json_files:
        with open(file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for model_name in model_list:
                if model_name not in result_dict[topic]:
                    result_dict[topic][model_name] = []
                result_dict[topic][model_name].extend(data[model_name])

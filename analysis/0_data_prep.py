# 0_data_prep.py
# ---------------------------
# 不做任何清洗：仅读取并展示数据结构
# ---------------------------

import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "..", "data_clean", "RPT_cleaned_guangdong.csv")

print(">> Loading raw CSV...")
df = pd.read_csv(DATA_PATH, encoding="utf-8")

print(">> Data loaded. Shape:", df.shape)
print(df.head())
print(df.info())

print(">> DONE.")

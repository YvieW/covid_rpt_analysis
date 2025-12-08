# 2_regressions.py
# ---------------------------
# 基本回归（OLS + 固定效应），并保存输出为 txt 文件
# ---------------------------

import pandas as pd
import os
import statsmodels.formula.api as smf

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "..", "data_clean", "RPT_cleaned_guangdong.csv")
OUT_PATH = os.path.join(BASE_DIR, "..", "results")

# 创建结果文件夹
if not os.path.exists(OUT_PATH):
    os.makedirs(OUT_PATH)

print(">> Loading data...")
df = pd.read_csv(DATA_PATH, encoding="utf-8")

# ---------------------------
# 生成哑变量（不修改原始数据）
# ---------------------------
df["during"] = (df["period"] == "During-COVID").astype(int)
df["post"]   = (df["period"] == "Post-COVID").astype(int)
df["industry_fe"] = df["indusb_01"]

# ---------------------------
# 回归模型：RPT 金额 isam
# ---------------------------
print("\n>> 运行 OLS 回归：RPT 金额（isam）")

model = smf.ols(
    "isam ~ during + post + relation + repat + C(industry_fe)",
    data=df
).fit(cov_type="HC3")     # 使用稳健标准误

print(model.summary())

# ---------------------------
# 保存回归结果为 txt
# ---------------------------
result_txt_path = os.path.join(OUT_PATH, "regression_isam_results.txt")
with open(result_txt_path, "w", encoding="utf-8") as f:
    f.write("OLS 回归结果：RPT 金额 isam\n")
    f.write("-" * 60 + "\n\n")
    f.write(model.summary().as_text())

print(f"\n>> 回归结果已保存：{result_txt_path}")
print(">> DONE regressions.")

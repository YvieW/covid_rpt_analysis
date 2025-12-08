# 3_robustness.py
# ---------------------------
# 稳健性检验（分组回归、winsorize、对数化、聚类标准误）
# 输出：
#   results/robust_log_results.txt
#   results/robust_winsor_results.txt
#   results/subsample_relation_results.txt
# ---------------------------

import os
import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
from matplotlib import font_manager
import warnings
warnings.filterwarnings("ignore")

# ---------------------------
# 环境路径
# ---------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "..", "data_clean", "RPT_cleaned_guangdong.csv")
OUT_DIR = os.path.join(BASE_DIR, "..", "results")
FIG_DIR = os.path.join(BASE_DIR, "..", "figures")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(FIG_DIR, exist_ok=True)

# ---------------------------
# 中文字体设置（绘图若需）
# ---------------------------
possible_fonts = ["SimHei", "Microsoft YaHei", "Songti SC", "Arial Unicode MS"]
for f in possible_fonts:
    if f in set([font.name for font in font_manager.fontManager.ttflist]):
        import matplotlib.pyplot as plt
        plt.rcParams["font.family"] = f
        break

# ---------------------------
# 读取原始数据（不做清洗）
# ---------------------------
print(">> Loading raw CSV ...")
df = pd.read_csv(DATA_PATH, encoding="utf-8")
print("   shape:", df.shape)

# 生成哑变量（疫情分期）
df["during"] = (df["period"] == "During-COVID").astype(int)
df["post"]   = (df["period"] == "Post-COVID").astype(int)

# ----- 1) 对数化回归（log(isam+1) 作为因变量） ----------------
df["log_isam"] = np.log1p(df["isam"])

formula = "log_isam ~ during + post + relation + repat + C(indusb_01)"
print("\n>> Running log(isam) regression ...")
mod = smf.ols(formula=formula, data=df)
# cluster by firm (stkcd_01)
try:
    res_log = mod.fit(cov_type="cluster", cov_kwds={"groups": df["stkcd_01"]})
except Exception:
    res_log = mod.fit(cov_type="HC3")
print(res_log.summary())

with open(os.path.join(OUT_DIR, "robust_log_results.txt"), "w", encoding="utf-8") as f:
    f.write("Robustness: log(isam) regression\n")
    f.write("-" * 80 + "\n")
    f.write(res_log.summary().as_text())

# ----- 2) Winsorize 在事务层面（1% - 99%） ----------------
def winsorize_series(s, lower_q=0.01, upper_q=0.99):
    low = s.quantile(lower_q)
    high = s.quantile(upper_q)
    return s.clip(lower=low, upper=high)

df["isam_w"] = winsorize_series(df["isam"], 0.01, 0.99)
df["log_isam_w"] = np.log1p(df["isam_w"])

formula_w = "isam_w ~ during + post + relation + repat + C(indusb_01)"
print("\n>> Running winsorized isam regression ...")
mod_w = smf.ols(formula=formula_w, data=df)
try:
    res_w = mod_w.fit(cov_type="cluster", cov_kwds={"groups": df["stkcd_01"]})
except Exception:
    res_w = mod_w.fit(cov_type="HC3")
print(res_w.summary())

with open(os.path.join(OUT_DIR, "robust_winsor_results.txt"), "w", encoding="utf-8") as f:
    f.write("Robustness: winsorized isam regression\n")
    f.write("-" * 80 + "\n")
    f.write(res_w.summary().as_text())

# ----- 3) 分组回归（按 relation 分组：例如母公司 vs 其他） -----
# relation 编码参照你的字典（01=母公司, 10=主要投资者控制等）
# 这里示例：relation == 1 (母公司) vs others
print("\n>> Running subgroup regressions by relation == 1 (母公司) ...")
df_parent = df[df["relation"] == 1].copy()
df_nonparent = df[df["relation"] != 1].copy()

out_lines = []
if len(df_parent) > 10:
    mod_parent = smf.ols("isam ~ during + post + repat + C(indusb_01)", data=df_parent)
    try:
        res_parent = mod_parent.fit(cov_type="cluster", cov_kwds={"groups": df_parent["stkcd_01"]})
    except Exception:
        res_parent = mod_parent.fit(cov_type="HC3")
    out_lines.append("Subsample: relation==1 (母公司) \n")
    out_lines.append(res_parent.summary().as_text())
    print("\n>> relation==1 regression done. N=", len(df_parent))
else:
    out_lines.append("Subsample: relation==1 too small to run regression. N=" + str(len(df_parent)) + "\n")
    print(">> relation==1 sample too small: N=", len(df_parent))

if len(df_nonparent) > 10:
    mod_non = smf.ols("isam ~ during + post + repat + C(indusb_01)", data=df_nonparent)
    try:
        res_non = mod_non.fit(cov_type="cluster", cov_kwds={"groups": df_nonparent["stkcd_01"]})
    except Exception:
        res_non = mod_non.fit(cov_type="HC3")
    out_lines.append("\n\nSubsample: relation!=1 (非母公司相关交易)\n")
    out_lines.append(res_non.summary().as_text())
    print("\n>> relation!=1 regression done. N=", len(df_nonparent))
else:
    out_lines.append("Subsample: relation!=1 too small to run regression. N=" + str(len(df_nonparent)) + "\n")
    print(">> relation!=1 sample too small: N=", len(df_nonparent))

with open(os.path.join(OUT_DIR, "subsample_relation_results.txt"), "w", encoding="utf-8") as f:
    f.write("Subsample regressions by relation\n")
    f.write("-" * 80 + "\n")
    f.write("\n".join(out_lines))

print("\n>> Robustness checks complete. Results saved to 'results/' folder.")

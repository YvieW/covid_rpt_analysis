# 4_event_study.py
# ---------------------------
# 完整事件研究（Event Study）示例
# - 自动生成合法 lead/lag 虚拟变量
# - 计算事件窗口均值及 95% CI
# - 动态回归（isam ~ lead/lag dummies + 行业固定效应）
# - Placebo 测试（伪事件）
# ---------------------------

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import font_manager
import statsmodels.formula.api as smf
import warnings
warnings.filterwarnings("ignore")

# ---------------------------
# 路径
# ---------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "..", "data_clean", "RPT_cleaned_guangdong.csv")
OUT_DIR = os.path.join(BASE_DIR, "..", "results")
FIG_DIR = os.path.join(BASE_DIR, "..", "figures")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(FIG_DIR, exist_ok=True)

# ---------------------------
# 中文字体设置
# ---------------------------
possible_fonts = ["SimHei", "Microsoft YaHei", "Songti SC", "Arial Unicode MS"]
for f in possible_fonts:
    if f in set([font.name for font in font_manager.fontManager.ttflist]):
        plt.rcParams["font.family"] = f
        break
plt.rcParams["axes.unicode_minus"] = False

# ---------------------------
# 读取数据
# ---------------------------
print(">> Loading raw CSV ...")
df = pd.read_csv(DATA_PATH, encoding="utf-8")
print("   shape:", df.shape)

# ---------------------------
# 事件时间计算（以 2020 为事件起点）
# ---------------------------
event_year = 2020
df["event_time"] = df["year"] - event_year

# 事件窗口设定
min_k, max_k = -3, 3
df_window = df[df["event_time"].between(min_k, max_k)]

# ---------------------------
# 计算均值与 95% CI
# ---------------------------
agg = df_window.groupby("event_time")["isam"].agg(['mean','count','std']).reset_index()
# 保存事件研究均值数据到 CSV（供 6_visual_summary 使用）
agg.to_csv(os.path.join(OUT_DIR, "event_study_mean.csv"), index=False, encoding="utf-8")
print(">> Saved event study mean CSV:", os.path.join(OUT_DIR, "event_study_mean.csv"))

agg['se'] = agg['std'] / np.sqrt(agg['count'])
agg['ci95_low'] = agg['mean'] - 1.96 * agg['se']
agg['ci95_high'] = agg['mean'] + 1.96 * agg['se']

plt.figure(figsize=(8,5))
plt.plot(agg['event_time'], agg['mean'], marker='o', label='平均 isam')
plt.fill_between(agg['event_time'], agg['ci95_low'], agg['ci95_high'], alpha=0.2)
plt.axvline(0, color='red', linestyle='--', label=f'COVID 起始年 ({event_year})')
plt.xlabel("相对于事件的年份 (year - 2020)")
plt.ylabel("平均 RPT 金额 isam")
plt.title("事件研究：-3 到 +3 年的平均 RPT 金额与 95% CI")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, "event_study_mean.png"), dpi=300)
plt.close()
print(">> Saved figure:", os.path.join(FIG_DIR, "event_study_mean.png"))

# ---------------------------
# 动态回归：生成合法虚拟变量
# ---------------------------
dummies = []
for k in range(min_k, max_k+1):
    if k < 0:
        varname = f"dt_m{abs(k)}"
    elif k > 0:
        varname = f"dt_p{k}"
    else:
        varname = "dt_0"
    df[varname] = (df["event_time"] == k).astype(int)
    if k != -1:  # Pre-COVID (-1) 作为基准期
        dummies.append(varname)

formula = "isam ~ " + " + ".join(dummies) + " + C(indusb_01)"
print("\n>> Running dynamic OLS regression...")
mod = smf.ols(formula=formula, data=df)
try:
    res_dyn = mod.fit(cov_type="cluster", cov_kwds={"groups": df["stkcd_01"]})
except Exception:
    res_dyn = mod.fit(cov_type="HC3")

print(res_dyn.summary())

# 保存回归结果
with open(os.path.join(OUT_DIR, "event_dynamic_regression.txt"), "w", encoding="utf-8") as f:
    f.write("Dynamic regression: isam on lead/lag dummies\n")
    f.write("-"*80 + "\n")
    f.write(res_dyn.summary().as_text())

# ---------------------------
# Placebo 测试（2018 作为伪事件）
# ---------------------------
placebo_year = 2018
df["placebo_event_time"] = df["year"] - placebo_year
df_place = df[df["placebo_event_time"].between(min_k, max_k)]

agg_place = df_place.groupby("placebo_event_time")["isam"].agg(['mean','count','std']).reset_index()
agg_place['se'] = agg_place['std'] / np.sqrt(agg_place['count'])
agg_place['ci95_low'] = agg_place['mean'] - 1.96 * agg_place['se']
agg_place['ci95_high'] = agg_place['mean'] + 1.96 * agg_place['se']

plt.figure(figsize=(8,5))
plt.plot(agg_place['placebo_event_time'], agg_place['mean'], marker='o', label='Placebo mean isam')
plt.fill_between(agg_place['placebo_event_time'], agg_place['ci95_low'], agg_place['ci95_high'], alpha=0.2)
plt.axvline(0, color='red', linestyle='--', label=f'Placebo Event ({placebo_year})')
plt.xlabel("相对于伪事件的年份 (year - 2018)")
plt.ylabel("平均 RPT 金额 isam")
plt.title("Placebo Event Study: 平均 RPT 金额 (2018 作为伪事件)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, "event_study_placebo.png"), dpi=300)
plt.close()
print(">> Saved placebo figure:", os.path.join(FIG_DIR, "event_study_placebo.png"))

print("\n>> Event study complete. Results saved to 'figures/' and 'results/'.")

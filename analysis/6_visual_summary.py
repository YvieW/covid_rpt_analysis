# 6_visual_summary.py
# ----------------------------------------------------
# 可视化摘要图：RPT 风险分担 vs 隧道
# 自动检测 event_study_coef.csv 是否存在：如缺失则跳过动态回归图
# ----------------------------------------------------

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import font_manager
import networkx as nx

# ----------------------------------------------------
# 路径
# ----------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "..", "data_clean", "RPT_cleaned_guangdong.csv")
MEAN_PATH = os.path.join(BASE_DIR, "..", "results", "event_study_mean.csv")
COEF_PATH = os.path.join(BASE_DIR, "..", "results", "event_study_coef.csv")
FIG_DIR = os.path.join(BASE_DIR, "..", "figures")
os.makedirs(FIG_DIR, exist_ok=True)

# ----------------------------------------------------
# 中文字体
# ----------------------------------------------------
possible_fonts = ["SimHei", "Microsoft YaHei", "Songti SC", "Arial Unicode MS"]
for f in possible_fonts:
    if f in set([font.name for font in font_manager.fontManager.ttflist]):
        plt.rcParams["font.family"] = f
        break
plt.rcParams["axes.unicode_minus"] = False

# ----------------------------------------------------
# 读取主数据
# ----------------------------------------------------
print(">> Loading CSV...")
df = pd.read_csv(DATA_PATH)
agg = pd.read_csv(MEAN_PATH)
print("   Data:", df.shape, "Event mean:", agg.shape)

# 自动计算置信区间
if "ci95_low" not in agg.columns:
    if "se" not in agg.columns:
        if "std" in agg.columns and "count" in agg.columns:
            agg["se"] = agg["std"] / np.sqrt(agg["count"])
        else:
            print("!! WARNING: 'se' / 'std' / 'count' 列缺失，无法计算置信区间")
            agg["se"] = 0.0
    agg["ci95_low"] = agg["mean"] - 1.96 * agg["se"]
    agg["ci95_high"] = agg["mean"] + 1.96 * agg["se"]

# ----------------------------------------------------
# 尝试读取 event_study_coef.csv（可能不存在）
# ----------------------------------------------------
coef_available = os.path.exists(COEF_PATH)
if coef_available:
    coef = pd.read_csv(COEF_PATH)
    print("   Event coef:", coef.shape)
    if "ci95_low" not in coef.columns:
        coef["ci95_low"] = coef["coef"] - 1.96 * coef["se"]
        coef["ci95_high"] = coef["coef"] + 1.96 * coef["se"]
else:
    print("!! WARNING: event_study_coef.csv not found. Skipping dynamic regression plot.")

# ----------------------------------------------------
# 图 1：事件研究均值
# ----------------------------------------------------
def plot_event_mean(ax, agg):
    ax.plot(agg["event_time"], agg["mean"], marker="o", label="平均 RPT（isam）")
    ax.fill_between(agg["event_time"], agg["ci95_low"], agg["ci95_high"], alpha=0.25)
    ax.axvline(0, color="red", linestyle="--", label="COVID 爆发 (2020)")
    ax.set_title("RPT 动态变化（事件研究均值）")
    ax.set_xlabel("事件时间")
    ax.set_ylabel("平均 RPT 金额")
    ax.grid(True)
    ax.legend()

# ----------------------------------------------------
# 图 2（可选）：事件研究回归系数 + 显著性
# ----------------------------------------------------
def plot_event_coef(ax, coef):
    def star(p):
        if p < 0.01: return "***"
        elif p < 0.05: return "**"
        elif p < 0.1: return "*"
        return ""
    ax.errorbar(coef["event_time"], coef["coef"], yerr=1.96*coef["se"], fmt="o-")
    for _, row in coef.iterrows():
        ax.text(row["event_time"], row["coef"] + 0.02*np.nanstd(coef["coef"]), star(row["pval"]),
                fontsize=10, ha="center")
    ax.axhline(0, linestyle="--", color="gray")
    ax.axvline(0, linestyle="--", color="red")
    ax.set_title("事件研究回归系数（含显著性）")
    ax.set_xlabel("事件时间")
    ax.set_ylabel("系数估计值")
    ax.grid(True)

# ----------------------------------------------------
# 图 3：网络中心性
# ----------------------------------------------------
def plot_network_centrality(ax, df):
    years = sorted(df["year"].unique())
    cent_vals = []
    for y in years:
        df_y = df[df["year"] == y]
        G = nx.DiGraph()
        companies = set(df_y["coname_cn_01"].unique()) | set(df_y["coname_cn_02"].dropna().unique())
        G.add_nodes_from(companies)
        for _, row in df_y.iterrows():
            if pd.notna(row["coname_cn_02"]):
                G.add_edge(row["coname_cn_01"], row["coname_cn_02"], weight=row["isam"])
        cent_vals.append(np.mean(list(nx.degree_centrality(G).values())))
    ax.plot(years, cent_vals, marker="s")
    ax.axvline(2020, linestyle="--", color="red")
    ax.set_title("RPT 网络中心性（核心企业控制力）")
    ax.set_xlabel("年份")
    ax.set_ylabel("平均中心性")
    ax.grid(True)

# ----------------------------------------------------
# 图 4：Top-10 集中度
# ----------------------------------------------------
def plot_top10_concentration(ax, df):
    years = sorted(df["year"].unique())
    top10_share = []
    for y in years:
        df_y = df[df["year"] == y]
        total = df_y["isam"].sum()
        top10 = df_y["isam"].nlargest(10).sum()
        top10_share.append(top10 / total if total > 0 else np.nan)
    ax.plot(years, top10_share, marker="D")
    ax.axvline(2020, linestyle="--", color="red")
    ax.set_title("RPT 金额 Top-10 集中度趋势")
    ax.set_xlabel("年份")
    ax.set_ylabel("Top-10 占比")
    ax.grid(True)

# ----------------------------------------------------
# 生成图：根据是否有 coef 自动切换
# ----------------------------------------------------
num_plots = 4 if coef_available else 3
fig, axes = plt.subplots(num_plots, 1, figsize=(8, 5 * num_plots))

plot_event_mean(axes[0], agg)

if coef_available:
    plot_event_coef(axes[1], coef)
    plot_network_centrality(axes[2], df)
    plot_top10_concentration(axes[3], df)
else:
    plot_network_centrality(axes[1], df)
    plot_top10_concentration(axes[2], df)

plt.tight_layout()
out_path = os.path.join(FIG_DIR, "summary_panel_full.png")
plt.savefig(out_path, dpi=300)
plt.close()

print(">> Saved summary figure:", out_path)
print(">> Visual summary complete.")

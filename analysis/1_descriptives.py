# 1_descriptives.py
# ---------------------------
# 描述性统计 + 图形（含中文注释）+ 输出文本保存
# ---------------------------

import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib import font_manager

# ---------------------------
# 设置中文字体
# ---------------------------
possible_fonts = ["SimHei", "Microsoft YaHei", "Songti SC", "Arial Unicode MS"]
for f in possible_fonts:
    if f in set([font.name for font in font_manager.fontManager.ttflist]):
        plt.rcParams["font.family"] = f
        break
plt.rcParams["axes.unicode_minus"] = False

# ---------------------------
# 路径
# ---------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "..", "data_clean", "RPT_cleaned_guangdong.csv")
FIG_PATH = os.path.join(BASE_DIR, "..", "figures")
OUTPUT_PATH = os.path.join(BASE_DIR, "..", "output")

os.makedirs(FIG_PATH, exist_ok=True)
os.makedirs(OUTPUT_PATH, exist_ok=True)

OUTPUT_FILE = os.path.join(OUTPUT_PATH, "descriptives_output.txt")

print(">> Loading data...")
df = pd.read_csv(DATA_PATH, encoding="utf-8")


# ---------------------------
# 收集输出文本内容
# ---------------------------
output_lines = []

output_lines.append("\n>> Describe numerical variables:\n")
output_lines.append(df[["isam", "pannrsm"]].describe().to_string())

output_lines.append("\n\n>> RPT type distribution (repat):\n")
output_lines.append(df["repat"].value_counts().to_string())

output_lines.append("\n\n>> Relation type distribution (relation):\n")
output_lines.append(df["relation"].value_counts().to_string())

output_lines.append("\n\n>> Period distribution:\n")
output_lines.append(df["period"].value_counts().to_string())


# ---------------------------
# 图形 1：金额随疫情阶段（箱线图）
# ---------------------------
plt.figure(figsize=(9, 6))
ax = sns.boxplot(data=df, x="period", y="isam")
plt.title("不同疫情阶段的关联交易金额分布（箱线图）", fontsize=14)
plt.xlabel("疫情阶段")
plt.ylabel("关联交易金额（isam）")

# 添加注释（Highlight）
medians = df.groupby("period")["isam"].median()
for idx, (x, median) in enumerate(medians.items()):
    ax.text(idx, median, f"中位数={median:.2f}", 
            ha='center', va='bottom', fontsize=10, color="red")

plt.tight_layout()
plt.savefig(os.path.join(FIG_PATH, "box_amount_period_annotated.png"), dpi=300)
plt.close()


# ---------------------------
# 图形 2：行业平均交易金额 + 注释
# ---------------------------
industry_mean = df.groupby("indusb_01")["isam"].mean().sort_values()

plt.figure(figsize=(9, 10))
ax2 = industry_mean.plot(kind="barh")
plt.title("各行业平均关联交易金额（带注释）", fontsize=14)
plt.xlabel("平均金额（isam）")
plt.ylabel("行业")

# 中文注释：最大与最小值
max_industry = industry_mean.idxmax()
min_industry = industry_mean.idxmin()

plt.annotate(f"最高行业：{max_industry}\n金额={industry_mean.max():.2f}",
             xy=(industry_mean.max(), len(industry_mean)-1),
             xytext=(industry_mean.max()*1.1, len(industry_mean)-2),
             arrowprops=dict(arrowstyle="->", lw=1.5))

plt.annotate(f"最低行业：{min_industry}\n金额={industry_mean.min():.2f}",
             xy=(industry_mean.min(), 0),
             xytext=(industry_mean.min()*1.1, 2),
             arrowprops=dict(arrowstyle="->", lw=1.5))

plt.tight_layout()
plt.savefig(os.path.join(FIG_PATH, "industry_amount_annotated.png"), dpi=300)
plt.close()


# ---------------------------
# 保存输出文字为 TXT
# ---------------------------
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(output_lines))

print(f">> Text outputs saved to: {OUTPUT_FILE}")
print(">> DONE descriptives (figures + annotated Chinese labels).")

import os
import pandas as pd
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt
from matplotlib import font_manager

# -----------------------------
# 1. 设置路径
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "..", "data_clean", "RPT_cleaned_guangdong.csv")
OUTPUT_XLSX = os.path.join(BASE_DIR, "..", "results", "grouped_regression_results.xlsx")
OUTPUT_PLOT_DIR = os.path.join(BASE_DIR, "..", "results", "plots")

os.makedirs(os.path.dirname(OUTPUT_XLSX), exist_ok=True)
os.makedirs(OUTPUT_PLOT_DIR, exist_ok=True)

# ------------------------------------------------------
# 中文字体设置
# ------------------------------------------------------
possible_fonts = ["SimHei", "Microsoft YaHei", "Songti SC", "Arial Unicode MS"]
for f in possible_fonts:
    if f in set([font.name for font in font_manager.fontManager.ttflist]):
        plt.rcParams["font.family"] = f
        break
plt.rcParams["axes.unicode_minus"] = False

# -----------------------------
# 2. 读取数据
# -----------------------------
df = pd.read_csv(DATA_PATH)

# -----------------------------
# 3. 回归公式设置
# -----------------------------
y_var = 'isam'
x_vars = ['pannrsm']  # 可扩展控制变量
fe_vars = ['C(coname_cn_01)', 'C(year)']  # 公司和年份固定效应
formula = y_var + ' ~ ' + ' + '.join(x_vars + fe_vars)

# -----------------------------
# 4. 定义分组回归函数
# -----------------------------
def run_grouped_regression(df, group_col, min_obs=10):
    results_list = []
    for group_name, group_data in df.groupby(group_col):
        if len(group_data) < min_obs:
            continue
        model = smf.ols(formula, data=group_data).fit(cov_type='HC1')
        res = pd.DataFrame({
            'variable': model.params.index,
            'coef': model.params.values,
            'se': model.bse.values,
            't': model.tvalues.values,
            'p': model.pvalues.values,
            'n_obs': len(group_data)
        })
        res['group'] = group_name
        results_list.append(res)
    if results_list:
        return pd.concat(results_list, ignore_index=True)
    else:
        return pd.DataFrame()

# -----------------------------
# 5. 按行业和省份分组回归
# -----------------------------
industry_results = run_grouped_regression(df, 'indusb_01')
province_results = run_grouped_regression(df, 'prvn_02')

# -----------------------------
# 6. 保存结果到 Excel，每个分组单独 sheet
# -----------------------------
with pd.ExcelWriter(OUTPUT_XLSX, engine='xlsxwriter') as writer:
    for group_name, group_df in industry_results.groupby('group'):
        group_df.to_excel(writer, sheet_name=f'Industry_{group_name[:20]}', index=False)
    for group_name, group_df in province_results.groupby('group'):
        group_df.to_excel(writer, sheet_name=f'Province_{group_name[:20]}', index=False)

# -----------------------------
# 7. 绘制行业和省份系数对比图
# -----------------------------
def plot_comparison(industry_df, province_df, var_name='pannrsm', output_file=None):
    # 筛选目标变量
    ind_df = industry_df[industry_df['variable'] == var_name].copy()
    prov_df = province_df[province_df['variable'] == var_name].copy()
    
    # 添加类别列
    ind_df['type'] = '行业'
    prov_df['type'] = '省份'
    
    # 合并数据
    plot_df = pd.concat([ind_df, prov_df], ignore_index=True)
    
    # 排序：先行业再省份
    plot_df = plot_df.sort_values(['type','coef'], ascending=[True, False]).reset_index(drop=True)
    
    # 绘图
    plt.figure(figsize=(max(10, len(plot_df)//2), 6))
    colors = {'行业':'skyblue', '省份':'salmon'}
    
    x_pos = range(len(plot_df))
    plt.bar(x_pos, plot_df['coef'], yerr=1.96*plot_df['se'], capsize=5,
            color=[colors[t] for t in plot_df['type']])
    
    plt.xticks(x_pos, plot_df['group'], rotation=90)
    plt.ylabel('Coefficient')
    plt.title(f'{var_name} 系数及 95% CI - 行业 vs 省份')
    plt.legend(handles=[plt.Line2D([0],[0],color='skyblue', lw=6, label='行业'),
                        plt.Line2D([0],[0],color='salmon', lw=6, label='省份')])
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file)
        plt.close()
    else:
        plt.show()

# 绘制对比图
plot_comparison(
    industry_results,
    province_results,
    var_name='pannrsm',
    output_file=os.path.join(OUTPUT_PLOT_DIR, 'industry_province_comparison.png')
)

print(f"分组回归完成，结果已保存到: {OUTPUT_XLSX}")
print(f"可视化图表已保存到: {OUTPUT_PLOT_DIR}")

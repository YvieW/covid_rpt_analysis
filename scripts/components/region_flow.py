# components/region_flow.py
# 【地区交易流向分析】主公司省份 × 关联方省份（金额流向）
import os
import pandas as pd
import plotly.express as px
from dash import Dash, html, dcc

def create_region_flow_layout(df):
    # 按 主公司省份 × 关联方省份 汇总交易额
    df_region = (
        df.groupby(["prvn_01", "prvn_02"], as_index=False)["isam"]
        .sum()
        .sort_values("isam", ascending=False)
    )

    # 热力图展示
    fig_heat = px.density_heatmap(
        df_region,
        x="prvn_01", y="prvn_02",
        z="isam", color_continuous_scale="Viridis",
        title="主公司省份 × 关联方省份：交易金额热力图",
        labels={"prvn_01": "主公司省份", "prvn_02": "关联方省份", "isam": "交易金额"}
    )

    return html.Div([
        html.H3("🌏 地区间交易流向分析", className="text-center mb-3"),
        html.P("分析主公司与关联方公司在不同省份之间的交易流向，反映跨区域经济联系。"),
        dcc.Graph(figure=fig_heat, id="region-heatmap"),
    ])

if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    DATA_PATH = os.path.join(BASE_DIR, "data_clean", "RPT_cleaned_guangdong.csv")

    print(f">>> 正在加载数据文件：{DATA_PATH}")
    df = pd.read_csv(DATA_PATH)

    app = Dash(__name__)
    app.title = "Region Flow - 跨地区交易流向"
    app.layout = create_region_flow_layout(df)
    app.run(debug=True, port=8052)

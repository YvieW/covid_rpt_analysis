# components/industry_view.py
# 【行业分布分析】行业内关联交易总额及疫情阶段分布
import os
import pandas as pd
import plotly.express as px
from dash import Dash, html, dcc

def create_industry_view_layout(df):
    # 按行业与疫情阶段汇总
    df_ind = (
        df.groupby(["indusb_01", "period"], as_index=False)["isam"]
        .sum()
        .sort_values("isam", ascending=False)
    )

    # 前十行业展示
    top_inds = df_ind.groupby("indusb_01")["isam"].sum().nlargest(10).index
    df_top = df_ind[df_ind["indusb_01"].isin(top_inds)]

    fig_bar = px.bar(
        df_top,
        x="indusb_01", y="isam", color="period",
        title="各行业关联交易金额（前十行业）",
        labels={"indusb_01": "行业", "isam": "交易金额"},
        text_auto=".2s"
    )

    fig_bar.update_layout(xaxis_tickangle=-30)

    return html.Div([
        html.H3("🏭 行业关联交易分析", className="text-center mb-3"),
        html.P("展示不同产业在疫情前后关联交易金额的变化，分析行业差异与恢复趋势。"),
        dcc.Graph(figure=fig_bar, id="industry-bar"),
    ])

if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    DATA_PATH = os.path.join(BASE_DIR, "data_clean", "RPT_cleaned_guangdong.csv")

    print(f">>> 正在加载数据文件：{DATA_PATH}")
    df = pd.read_csv(DATA_PATH)

    app = Dash(__name__)
    app.title = "Industry View - 行业分析"
    app.layout = create_industry_view_layout(df)
    app.run(debug=True, port=8053)

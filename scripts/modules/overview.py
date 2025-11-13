# components/overview.py
# 【总体趋势】分析不同年份、疫情阶段下的交易总额走势与分布

import os
import pandas as pd
import plotly.express as px
from dash import Dash, html, dcc

def create_overview_layout(df):
    df_year = (
        df.groupby(["year", "period"], as_index=False)["isam"]
        .sum()
        .sort_values("year")
    )

    fig_line = px.line(
        df_year,
        x="year", y="isam", color="period",
        markers=True,
        title="年度关联交易总额趋势（按疫情阶段）",
        labels={"isam": "交易金额（元）", "year": "年份"}
    )

    df_period = df.groupby("period", as_index=False)["isam"].sum()
    fig_bar = px.bar(
        df_period, x="period", y="isam", text_auto=".2s",
        color="period",
        title="不同疫情阶段的关联交易总额"
    )

    return html.Div([
        html.H3("📈 总体趋势分析", className="text-center mb-3"),
        html.P("展示广东省上市公司在不同年份与疫情阶段的关联交易规模变化趋势。"),
        dcc.Graph(figure=fig_line, id="overview-line"),
        dcc.Graph(figure=fig_bar, id="overview-bar"),
    ])

if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    DATA_PATH = os.path.join(BASE_DIR, "data_clean", "RPT_cleaned_guangdong.csv")

    print(f">>> 正在加载数据文件：{DATA_PATH}")
    df = pd.read_csv(DATA_PATH)

    app = Dash(__name__)
    app.title = "Overview - 广东省关联交易总体趋势"
    app.layout = create_overview_layout(df)

    # ✅ 新写法（Dash v3+）
    app.run(debug=True, port=8051)

# components/overview.py
# 【总体趋势】分析不同年份、疫情阶段下的交易总额走势与分布

import pandas as pd
import plotly.express as px
from dash import html, dcc

def create_overview_layout(df):
    """返回总体趋势分析布局（包含两张图表）"""
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

    layout = html.Div([
        html.H3("📈 总体趋势分析", className="text-center mb-3"),
        html.P("展示广东省上市公司在不同年份与疫情阶段的关联交易规模变化趋势。"),
        dcc.Graph(figure=fig_line, id="overview-line", style={"height": "45vh"}),
        dcc.Graph(figure=fig_bar, id="overview-bar", style={"height": "45vh"}),
    ], style={"height": "100%", "overflow": "auto"})  # 滚动支持

    return layout

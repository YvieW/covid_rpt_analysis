# components/industry_view.py
# 【行业分布分析】行业内关联交易总额及疫情阶段分布

import pandas as pd
import plotly.express as px
from dash import html, dcc


def create_industry_view_layout(df):
    """
    返回行业关联交易分析布局组件。
    展示各行业在疫情阶段下的关联交易规模与变化趋势。
    """

    # ===== 数据汇总 =====
    df_ind = (
        df.groupby(["indusb_01", "period"], as_index=False)["isam"]
        .sum()
        .sort_values("isam", ascending=False)
    )

    # 选取前10大行业
    top_inds = df_ind.groupby("indusb_01")["isam"].sum().nlargest(10).index
    df_top = df_ind[df_ind["indusb_01"].isin(top_inds)]

    # ===== 绘制分组柱状图 =====
    fig_bar = px.bar(
        df_top,
        x="indusb_01",
        y="isam",
        color="period",
        text_auto=".2s",
        title="各行业关联交易金额（前十行业）",
        labels={
            "indusb_01": "行业",
            "isam": "交易金额（元）",
            "period": "疫情阶段",
        },
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )

    fig_bar.update_layout(
        xaxis_tickangle=-30,
        margin=dict(l=40, r=40, t=60, b=40),
        legend_title_text="疫情阶段",
        yaxis_title="交易金额（元）",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )

    # ===== 返回布局 =====
    layout = html.Div(
        [
            html.H3("🏭 行业关联交易分析", className="text-center mb-3"),
            html.P(
                "展示不同行业在疫情前后关联交易金额的变化趋势，"
                "帮助分析产业结构与经济恢复情况。",
                className="text-muted",
            ),
            dcc.Graph(figure=fig_bar, id="industry-bar", style={"height": "75vh"}),
        ],
        style={"height": "100%", "overflow": "auto"},
    )

    return layout

# components/region_flow.py
# 【地区交易流向分析】主公司省份 × 关联方省份（金额流向）

import pandas as pd
import plotly.express as px
from dash import html, dcc


def create_region_flow_layout(df):
    """
    返回地区交易流向分析布局组件。
    展示主公司省份与关联方省份之间的交易金额分布。
    """

    # 数据聚合：主公司省份 × 关联方省份
    df_region = (
        df.groupby(["prvn_01", "prvn_02"], as_index=False)["isam"]
        .sum()
        .sort_values("isam", ascending=False)
    )

    # 热力图（省份间交易额）
    fig_heat = px.density_heatmap(
        df_region,
        x="prvn_01",
        y="prvn_02",
        z="isam",
        color_continuous_scale="Viridis",
        title="主公司省份 × 关联方省份：交易金额热力图",
        labels={"prvn_01": "主公司省份", "prvn_02": "关联方省份", "isam": "交易金额（元）"},
    )

    fig_heat.update_layout(
        margin=dict(l=40, r=40, t=80, b=40),
        coloraxis_colorbar=dict(title="交易金额（元）"),
        xaxis_tickangle=-45,
    )

    # 返回 Dash 布局
    layout = html.Div(
        [
            html.H3("🌏 地区间交易流向分析", className="text-center mb-3"),
            html.P(
                "分析主公司与关联方公司在不同省份之间的交易流向，"
                "反映跨区域经济联系与资金往来。",
                className="text-muted",
            ),
            dcc.Graph(figure=fig_heat, id="region-heatmap", style={"height": "80vh"}),
        ],
        style={"height": "100%", "overflow": "auto"},
    )

    return layout

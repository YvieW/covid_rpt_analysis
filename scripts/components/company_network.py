# components/company_network.py
# 【公司网络分析】展示主公司与关联方之间的交易网络

import pandas as pd
import networkx as nx
import plotly.graph_objects as go
from dash import html, dcc


def create_company_network_layout(df):
    """
    返回公司关联交易网络分析布局组件。
    展示主公司与关联方之间的交易网络结构，反映集团化与资金流向关系。
    """

    # ===== 数据准备 =====
    # 判断目标列名是否存在
    target_col = (
        "衡南县湘建泓泰环保有限责任公司"
        if "衡南县湘建泓泰环保有限责任公司" in df.columns
        else "repart"
    )

    # 构建无向图：主公司 ↔ 关联方
    G = nx.from_pandas_edgelist(
        df,
        source="coname_cn_01",
        target=target_col,
        edge_attr="isam",
        create_using=nx.Graph(),
    )

    if len(G) == 0:
        return html.Div(
            [
                html.H3("🏢 公司关联网络分析", className="text-center mb-3"),
                html.P("暂无可展示的公司关系网络数据。"),
            ],
            style={"textAlign": "center", "padding": "2rem"},
        )

    # ===== 网络布局（力导向算法） =====
    pos = nx.spring_layout(G, k=0.5, iterations=50, seed=42)

    # 边坐标
    edge_x, edge_y = [], []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        line=dict(width=0.5, color="#888"),
        hoverinfo="none",
        mode="lines",
    )

    # 节点坐标与标签
    node_x, node_y, node_text, node_size = [], [], [], []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(node)
        # 节点大小与度数成比例
        node_size.append(5 + 3 * nx.degree(G, node))

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        text=node_text,
        textposition="top center",
        hoverinfo="text",
        marker=dict(
            size=node_size,
            color="skyblue",
            line=dict(width=2, color="darkblue"),
            opacity=0.8,
        ),
    )

    # ===== 绘制网络图 =====
    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(
        title="🏢 公司间关联交易网络",
        title_x=0.5,
        title_font=dict(size=18),
        showlegend=False,
        hovermode="closest",
        margin=dict(b=0, l=0, r=0, t=50),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor="white",
    )

    # ===== 返回布局组件 =====
    layout = html.Div(
        [
            html.H3("🏢 公司关联网络分析", className="text-center mb-3"),
            html.P(
                "展示主公司与关联方之间的关联交易网络结构，"
                "可反映企业集团化程度及交易关系密集度。",
                className="text-muted",
            ),
            dcc.Graph(figure=fig, id="company-network", style={"height": "85vh"}),
        ],
        style={"height": "100%", "overflow": "hidden"},
    )

    return layout

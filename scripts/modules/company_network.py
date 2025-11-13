# components/company_network.py
# 【公司网络分析】展示主公司与关联方之间的交易网络
import os
import pandas as pd
import networkx as nx
import plotly.graph_objects as go
from dash import Dash, html, dcc

def create_company_network_layout(df):
    # 构建网络图：主公司 ↔ 关联方
    G = nx.from_pandas_edgelist(
        df,
        source="coname_cn_01",
        target="衡南县湘建泓泰环保有限责任公司" if "衡南县湘建泓泰环保有限责任公司" in df.columns else "repart",
        edge_attr="isam",
        create_using=nx.Graph()
    )

    # 获取布局
    pos = nx.spring_layout(G, k=0.5, iterations=50, seed=42)

    # 节点坐标
    node_x, node_y = zip(*[pos[node] for node in G.nodes()])
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode="markers+text",
        text=list(G.nodes()),
        textposition="top center",
        marker=dict(size=10, color="lightblue", line_width=2),
        hoverinfo="text"
    )

    # 边线
    edge_x, edge_y = [], []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.5, color="#888"),
        hoverinfo="none",
        mode="lines"
    )

    # 绘制图形
    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(
        title="🏢 公司间关联交易网络",
        showlegend=False,
        hovermode="closest",
        margin=dict(b=0, l=0, r=0, t=40),
        xaxis=dict(showgrid=False, zeroline=False),
        yaxis=dict(showgrid=False, zeroline=False)
    )

    return html.Div([
        html.H3("🏢 公司关联网络分析", className="text-center mb-3"),
        html.P("展示主公司与关联方之间的关联交易网络关系结构，可反映集团化关联度。"),
        dcc.Graph(figure=fig, id="company-network"),
    ])

if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    DATA_PATH = os.path.join(BASE_DIR, "data_clean", "RPT_cleaned_guangdong.csv")

    print(f">>> 正在加载数据文件：{DATA_PATH}")
    df = pd.read_csv(DATA_PATH)

    app = Dash(__name__)
    app.title = "Company Network - 公司关联网络"
    app.layout = create_company_network_layout(df)
    app.run(debug=True, port=8054)

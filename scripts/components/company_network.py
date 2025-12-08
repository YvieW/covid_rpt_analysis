# components/company_network.py
# ============================================================
# 🏢 公司网络分析（动态版）
# - 增加年份和区域筛选按钮
# - 根据选择动态更新公司网络图
# - 支持 Abstract filter-store 联动
# ============================================================

import pandas as pd
import networkx as nx
import plotly.graph_objects as go
import dash
from dash import html, dcc, Input, Output, State, callback_context

from .filters import year_options, year_groups, province_groups, apply_filters
from .province_coords import province_coords


# ============================================================
# 🅰 Layout 构建
# ============================================================
def create_company_network_layout(df, compact=False):
    years_all = sorted(df["year"].dropna().unique())
    provinces = sorted(list(province_coords.keys()))

    layout = html.Div(
        [
            # ================= 网络图 =================
            dcc.Graph(
                id="company-network",
                style={"height": "100%" if compact else "90vh", "width": "100%"},
                config={"displayModeBar": False},
            ),

            html.H3("🏢 公司关联网络分析", className="text-center mb-2"),
            html.P(
                "展示主公司与关联方之间的关联交易网络结构，反映产业集团化与交易关系密集程度。",
                className="text-muted",
            ),

            # ================= 筛选器 =================
            html.Div(
                [
                    # 年份筛选
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Button("Pre-COVID", id="cn-year-pre", n_clicks=0, style={"marginRight": "6px"}),
                                    html.Button("During-COVID", id="cn-year-during", n_clicks=0, style={"marginRight": "6px"}),
                                    html.Button("Post-COVID", id="cn-year-post", n_clicks=0, style={"marginRight": "6px"}),
                                    html.Button("全选", id="cn-year-select-all", n_clicks=0, style={"marginRight": "6px"}),
                                    html.Button("全不选", id="cn-year-select-none", n_clicks=0),
                                ],
                                style={"marginBottom": "6px"},
                            ),
                            dcc.Dropdown(
                                id="cn-year-dropdown",
                                options=year_options,
                                value=years_all,
                                multi=True,
                                clearable=False,
                                style={"width": "100%"},
                            ),
                        ],
                        style={"minWidth": "280px", "width": "32%", "marginRight": "24px"},
                    ),

                    # 省份筛选
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Button("东北", id="cn-grp-ne", n_clicks=0, style={"marginRight": "6px"}),
                                    html.Button("华北", id="cn-grp-north", n_clicks=0, style={"marginRight": "6px"}),
                                    html.Button("华东", id="cn-grp-east", n_clicks=0, style={"marginRight": "6px"}),
                                    html.Button("华中", id="cn-grp-central", n_clicks=0, style={"marginRight": "6px"}),
                                    html.Button("华南", id="cn-grp-south", n_clicks=0, style={"marginRight": "6px"}),
                                    html.Button("西南", id="cn-grp-sw", n_clicks=0, style={"marginRight": "6px"}),
                                    html.Button("西北", id="cn-grp-nw", n_clicks=0, style={"marginRight": "6px"}),
                                    html.Button("全选", id="cn-province-select-all", n_clicks=0, style={"marginLeft": "6px"}),
                                    html.Button("全不选", id="cn-province-select-none", n_clicks=0, style={"marginLeft": "6px"}),
                                ],
                                style={"marginBottom": "8px", "display": "flex", "flexWrap": "wrap"},
                            ),
                            dcc.Dropdown(
                                id="cn-region-dropdown",
                                options=[{"label": p, "value": p} for p in provinces],
                                value=provinces,
                                multi=True,
                                clearable=False,
                                style={"width": "100%"},
                            ),
                        ],
                        style={"minWidth": "460px", "width": "60%"},
                    ),
                ],
                style={"display": "flex", "flexWrap": "wrap", "marginBottom": "20px"},
            ),
        ],
        style={"height": "100%" if compact else "100vh", "overflow": "hidden" if compact else "auto"},
    )

    return layout


# ============================================================
# 🅱 Callback 注册
# ============================================================
def register_company_network_callbacks(app, df):
    # ---------------- 年份按钮 ----------------
    @app.callback(
        Output("cn-year-dropdown", "value"),
        [
            Input("cn-year-pre", "n_clicks"),
            Input("cn-year-during", "n_clicks"),
            Input("cn-year-post", "n_clicks"),
            Input("cn-year-select-all", "n_clicks"),
            Input("cn-year-select-none", "n_clicks"),
        ],
        State("cn-year-dropdown", "value"),
    )
    def update_years(btn_pre, btn_during, btn_post, btn_all, btn_none, current):
        ctx = callback_context
        if not ctx.triggered:
            return current
        btn_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if btn_id == "cn-year-select-all":
            all_years = []
            for group, years in year_groups.items():
                all_years += years
            return sorted(list(set(all_years)))

        if btn_id == "cn-year-select-none":
            return []

        if btn_id == "cn-year-pre":
            return sorted(year_groups["pre"])
        if btn_id == "cn-year-during":
            return sorted(year_groups["during"])
        if btn_id == "cn-year-post":
            return sorted(year_groups["post"])

        return current

    # ---------------- 区域按钮 ----------------
    @app.callback(
        Output("cn-region-dropdown", "value"),
        [
            Input("cn-grp-ne", "n_clicks"),
            Input("cn-grp-north", "n_clicks"),
            Input("cn-grp-east", "n_clicks"),
            Input("cn-grp-central", "n_clicks"),
            Input("cn-grp-south", "n_clicks"),
            Input("cn-grp-sw", "n_clicks"),
            Input("cn-grp-nw", "n_clicks"),
            Input("cn-province-select-all", "n_clicks"),
            Input("cn-province-select-none", "n_clicks"),
        ],
        State("cn-region-dropdown", "value"),
    )
    def update_provinces(n1, n2, n3, n4, n5, n6, n7, n_all, n_none, current):
        ctx = callback_context
        if not ctx.triggered:
            return current
        btn = ctx.triggered[0]["prop_id"].split(".")[0]

        if btn == "cn-province-select-all":
            all_p = []
            for lst in province_groups.values():
                all_p += lst
            return sorted(list(set(all_p)))

        if btn == "cn-province-select-none":
            return []

        mapping = {
            "cn-grp-ne": "东北",
            "cn-grp-north": "华北",
            "cn-grp-east": "华东",
            "cn-grp-central": "华中",
            "cn-grp-south": "华南",
            "cn-grp-sw": "西南",
            "cn-grp-nw": "西北",
        }

        if btn in mapping:
            grp = mapping[btn]
            return sorted(province_groups[grp])

        return current

    # ---------------- 更新网络图 ----------------
    @ app.callback(
        Output("company-network", "figure"),
        Input("cn-year-dropdown", "value"),
        Input("cn-region-dropdown", "value"),
        Input("filter-store", "data"),  # Abstract 联动
    )
    def update_company_network(years_selected, provinces_selected, store_data):
        ctx = callback_context
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

        # 仅在 filter-store 触发时覆盖
        if trigger_id == "filter-store" and store_data:
            years_selected = store_data.get("years", years_selected)
            provinces_selected = store_data.get("provinces", provinces_selected)

        dff = apply_filters(df, years=years_selected, provinces=provinces_selected)

        target_col = "coname_cn_02" if "coname_cn_02" in dff.columns else "repart"

        G = nx.from_pandas_edgelist(
            dff,
            source="coname_cn_01",
            target=target_col,
            edge_attr="isam",
            create_using=nx.Graph(),
        )

        if len(G) == 0:
            fig = go.Figure()
            fig.update_layout(
                title="暂无可展示的公司关系网络数据",
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
            )
            return fig

        pos = nx.spring_layout(G, k=0.5, iterations=50, seed=42)

        # 边
        edge_x, edge_y = [], []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x += [x0, x1, None]
            edge_y += [y0, y1, None]

        edge_trace = go.Scatter(
            x=edge_x,
            y=edge_y,
            mode="lines",
            line=dict(width=0.7, color="#999"),
            hoverinfo="none",
        )

        # 节点
        node_x, node_y, node_text, node_size = [], [], [], []
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(node)
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
                opacity=0.85,
            ),
        )

        fig = go.Figure(data=[edge_trace, node_trace])
        fig.update_layout(
            autosize=True,
            height=None,
            showlegend=False,
            hovermode="closest",
            margin=dict(l=20, r=20, t=20, b=20),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor="white",
            paper_bgcolor="rgba(0,0,0,0)",
        )

        return fig


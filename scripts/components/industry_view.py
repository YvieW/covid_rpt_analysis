# components/industry_view.py
# ============================================================
# 🏭 行业分布分析（动态版）
# - 年份与区域筛选（按钮+下拉）
# - 显示行业关联交易总额
# - 显示疫情阶段分布（饼图）
# - 饼图右侧显示行业前三（含占比）
# - 主图：行业交易额 Top10 柱状图
# ============================================================

import pandas as pd
import plotly.express as px
import dash
from dash import html, dcc, Input, Output, State

from .filters import year_options, year_groups, province_groups, apply_filters
from .province_coords import province_coords


# ============================================================
# 🅰 Layout 构建
# ============================================================
def create_industry_view_layout(df):
    years_all = sorted(df["year"].dropna().unique())
    provinces = sorted(list(province_coords.keys()))

    layout = html.Div(
        [
            # ================= 缩略图：饼图（左） + 总额 + 行业前三（右） =================
            html.Div(
                [
                    # ---- 疫情阶段饼图（宽度=总额区域的 2 倍） ----
                    html.Div(
                        [
                            dcc.Graph(
                                id="industry-period-pie",
                                config={"displayModeBar": False},
                                style={"height": "180px"},
                            )
                        ],
                        style={
                            "flex": "2",
                            "padding": "5px",
                            "backgroundColor": "white",
                            "borderRadius": "10px",
                            "marginRight": "12px",
                            "boxShadow": "0 2px 5px rgba(0,0,0,0.1)",
                        },
                    ),

                    # ---- 右侧：总额 + 行业前三 ----
                    html.Div(
                        [
                            html.H5("行业关联交易总额（亿元）", style={"marginBottom": "4px"}),

                            html.H2(
                                id="industry-total-amt",
                                style={
                                    "fontWeight": "bold",
                                    "color": "#2A4D69",
                                    "marginTop": "0px",
                                    "marginBottom": "10px"
                                },
                            ),

                            html.H6("行业Top3：", style={"marginBottom": "6px"}),

                            html.Ul(
                                id="industry-top3-list",
                                style={
                                    "paddingLeft": "20px",
                                    "marginTop": "0px",
                                    "fontSize": "12px",
                                    "lineHeight": "18px",
                                },
                            ),
                        ],
                        style={
                            "flex": "1",
                            "padding": "12px",
                            "backgroundColor": "white",
                            "borderRadius": "10px",
                            "boxShadow": "0 2px 5px rgba(0,0,0,0.1)",
                        },
                    ),
                ],
                style={"display": "flex", "marginBottom": "20px"},
            ),

            html.H3("🏭 行业关联交易分析", className="text-center mb-3"),
            html.P(
                "展示不同行业在疫情前后关联交易金额的变化趋势，帮助分析产业结构与经济恢复情况。",
                className="text-muted",
            ),

            # ================= 主图：行业交易柱状图 =================
            dcc.Graph(
                id="industry-bar",
                style={"height": "100%", "width": "100%"},
            ),

            # ================= 筛选器 =================
            html.Div(
                [
                    # 年份筛选
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Button("Pre-COVID", id="iv-year-pre", n_clicks=0, style={"marginRight": "6px"}),
                                    html.Button("During-COVID", id="iv-year-during", n_clicks=0, style={"marginRight": "6px"}),
                                    html.Button("Post-COVID", id="iv-year-post", n_clicks=0, style={"marginRight": "6px"}),
                                    html.Button("全选", id="iv-year-select-all", n_clicks=0, style={"marginRight": "6px"}),
                                    html.Button("全不选", id="iv-year-select-none", n_clicks=0),
                                ],
                                style={"marginBottom": "6px"},
                            ),
                            dcc.Dropdown(
                                id="industry-year-dropdown",
                                options=year_options,
                                value=years_all,
                                multi=True,
                                clearable=False,
                            ),
                        ],
                        style={"minWidth": "280px", "width": "32%", "marginRight": "24px"},
                    ),

                    # 区域筛选
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Button("东北", id="iv-grp-ne", n_clicks=0, style={"marginRight": "6px"}),
                                    html.Button("华北", id="iv-grp-north", n_clicks=0, style={"marginRight": "6px"}),
                                    html.Button("华东", id="iv-grp-east", n_clicks=0, style={"marginRight": "6px"}),
                                    html.Button("华中", id="iv-grp-central", n_clicks=0, style={"marginRight": "6px"}),
                                    html.Button("华南", id="iv-grp-south", n_clicks=0, style={"marginRight": "6px"}),
                                    html.Button("西南", id="iv-grp-sw", n_clicks=0, style={"marginRight": "6px"}),
                                    html.Button("西北", id="iv-grp-nw", n_clicks=0, style={"marginRight": "6px"}),

                                    html.Button("全选", id="iv-province-select-all", n_clicks=0, style={"marginLeft": "6px"}),
                                    html.Button("全不选", id="iv-province-select-none", n_clicks=0, style={"marginLeft": "6px"}),
                                ],
                                style={"marginBottom": "8px", "display": "flex", "flexWrap": "wrap"},
                            ),
                            dcc.Dropdown(
                                id="industry-region-dropdown",
                                options=[{"label": p, "value": p} for p in provinces],
                                value=provinces,
                                multi=True,
                                clearable=False,
                            ),
                        ],
                        style={"minWidth": "460px", "width": "60%"},
                    ),
                ],
                style={"display": "flex", "flexWrap": "wrap", "marginBottom": "20px"},
            ),
        ]
    )

    return layout


# ============================================================
# 🅱 Callback 注册（支持 Abstract filter-store 联动）
# ============================================================
def register_industry_view_callbacks(app, df):

    # ---------------- 年份按钮 ----------------
    @app.callback(
        Output("industry-year-dropdown", "value"),
        [
            Input("iv-year-pre", "n_clicks"),
            Input("iv-year-during", "n_clicks"),
            Input("iv-year-post", "n_clicks"),
            Input("iv-year-select-all", "n_clicks"),
            Input("iv-year-select-none", "n_clicks"),
        ],
        State("industry-year-dropdown", "value"),
    )
    def update_years(btn_pre, btn_during, btn_post, btn_all, btn_none, current):
        ctx = dash.callback_context
        if not ctx.triggered:
            return current
        btn = ctx.triggered[0]["prop_id"].split(".")[0]

        if btn == "iv-year-select-all":
            all_years = []
            for g in year_groups.values():
                all_years += g
            return sorted(list(set(all_years)))

        if btn == "iv-year-select-none":
            return []

        if btn == "iv-year-pre":
            return year_groups["pre"]
        if btn == "iv-year-during":
            return year_groups["during"]
        if btn == "iv-year-post":
            return year_groups["post"]

        return current

    # ---------------- 区域按钮 ----------------
    @app.callback(
        Output("industry-region-dropdown", "value"),
        [
            Input("iv-grp-ne", "n_clicks"),
            Input("iv-grp-north", "n_clicks"),
            Input("iv-grp-east", "n_clicks"),
            Input("iv-grp-central", "n_clicks"),
            Input("iv-grp-south", "n_clicks"),
            Input("iv-grp-sw", "n_clicks"),
            Input("iv-grp-nw", "n_clicks"),
            Input("iv-province-select-all", "n_clicks"),
            Input("iv-province-select-none", "n_clicks"),
        ],
        State("industry-region-dropdown", "value"),
    )
    def update_provinces(*args):
        ctx = dash.callback_context
        if not ctx.triggered:
            return args[-1]

        btn = ctx.triggered[0]["prop_id"].split(".")[0]

        if btn == "iv-province-select-all":
            allp = []
            for lst in province_groups.values():
                allp += lst
            return sorted(list(set(allp)))

        if btn == "iv-province-select-none":
            return []

        mapping = {
            "iv-grp-ne": "东北",
            "iv-grp-north": "华北",
            "iv-grp-east": "华东",
            "iv-grp-central": "华中",
            "iv-grp-south": "华南",
            "iv-grp-sw": "西南",
            "iv-grp-nw": "西北",
        }

        if btn in mapping:
            return sorted(province_groups[mapping[btn]])

        return args[-1]

    # ---------------- 更新总额 ----------------
    @app.callback(
        Output("industry-total-amt", "children"),
        Input("industry-year-dropdown", "value"),
        Input("industry-region-dropdown", "value"),
        Input("filter-store", "data"),  # ← Abstract 联动
    )
    def update_industry_total(years, provinces, store_data):
        ctx = dash.callback_context
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        if trigger_id == "filter-store" and store_data:
            years = store_data.get("years", years)
            provinces = store_data.get("provinces", provinces)

        dff = apply_filters(df, years=years, provinces=provinces)
        total_amt = dff["isam"].sum() / 1e8
        return f"{total_amt:,.1f}"


    # ---------------- 行业前三列表 ----------------
    @app.callback(
        Output("industry-top3-list", "children"),
        Input("industry-year-dropdown", "value"),
        Input("industry-region-dropdown", "value"),
        Input("filter-store", "data"),
    )
    def update_industry_top3(years, provinces, store_data):
        ctx = dash.callback_context
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        if trigger_id == "filter-store" and store_data:
            years = store_data.get("years", years)
            provinces = store_data.get("provinces", provinces)

        dff = apply_filters(df, years=years, provinces=provinces)
        df_ind = dff.groupby("indusb_01", as_index=False)["isam"].sum().sort_values("isam", ascending=False)
        if df_ind.empty:
            return [html.Li("无数据")]

        top3 = df_ind.head(3)
        total = df_ind["isam"].sum()
        return [html.Li(f"{row['indusb_01']} — {row['isam']/total*100:.1f}%") for _, row in top3.iterrows()]


    # ---------------- 饼图 ----------------
    @app.callback(
        Output("industry-period-pie", "figure"),
        Input("industry-year-dropdown", "value"),
        Input("industry-region-dropdown", "value"),
        Input("filter-store", "data"),
    )
    def update_period_pie(years, provinces, store_data):
        ctx = dash.callback_context
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        if trigger_id == "filter-store" and store_data:
            years = store_data.get("years", years)
            provinces = store_data.get("provinces", provinces)

        dff = apply_filters(df, years=years, provinces=provinces)
        df_pie = dff.groupby("period", as_index=False)["isam"].sum().sort_values("isam", ascending=False)
        period_colors = {"Pre-COVID": "#2241EC", "During-COVID": "#E89483", "Post-COVID": "#41DA90"}
        fig = px.pie(df_pie, names="period", values="isam", hole=0.45, color="period", color_discrete_map=period_colors)
        fig.update_layout(title="疫情阶段交易分布", margin=dict(l=10, r=10, t=40, b=10), legend_title_text="", height=180)
        return fig


    # ---------------- Top10 柱状图 ----------------
    @app.callback(
        Output("industry-bar", "figure"),
        Input("industry-year-dropdown", "value"),
        Input("industry-region-dropdown", "value"),
        Input("filter-store", "data"),
    )
    def update_industry_graph(years, provinces, store_data):
        ctx = dash.callback_context
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        if trigger_id == "filter-store" and store_data:
            years = store_data.get("years", years)
            provinces = store_data.get("provinces", provinces)

        dff = apply_filters(df, years=years, provinces=provinces)
        df_ind = dff.groupby(["indusb_01", "period"], as_index=False)["isam"].sum().sort_values("isam", ascending=False)
        top_inds = df_ind.groupby("indusb_01")["isam"].sum().nlargest(10).index
        df_top = df_ind[df_ind["indusb_01"].isin(top_inds)]

        fig_bar = px.bar(
            df_top,
            x="indusb_01",
            y="isam",
            color="period",
            text_auto=".2s",
            title="各行业关联交易金额（前十行业）",
            labels={"indusb_01": "行业", "isam": "交易金额（元）", "period": "疫情阶段"},
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        fig_bar.update_layout(
            autosize=True,
            xaxis_tickangle=-30,
            margin=dict(l=10, r=10, t=40, b=20),
            legend_title_text="疫情阶段",
            yaxis_title="交易金额（元）",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        return fig_bar

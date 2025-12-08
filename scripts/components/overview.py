# components/overview.py
# ============================================================
# 【总体趋势页】按钮筛选 + 年份父级自动展开 + 区域按钮选择
# 摘要小图 + 总体趋势折线图 + 阶段柱状图
# ============================================================

import pandas as pd
import plotly.express as px
import dash
from dash import html, dcc, Input, Output, State

# 公共筛选变量
from .filters import (
    year_options,
    year_groups,
    province_groups,
    apply_filters,
)
from .province_coords import province_coords


# ============================================================
# 🅰 Layout 构建
# ============================================================
def create_overview_layout(df):
    years_all = sorted(df["year"].dropna().unique())
    provinces = sorted(list(province_coords.keys()))

    layout = html.Div(
        [
            # =======================================================
            # ⭐ 摘要小图（Compact Bar）
            # =======================================================
            html.Div(
                [
                    dcc.Graph(
                        id="overview-bar-small",
                        style={"height": "200px", "width": "100%"},
                        config={"displayModeBar": False},
                    )
                ]
            ),

            html.H3("📈 总体趋势分析", className="text-center mb-3"),
            html.P("展示不同年份与疫情阶段内的上市公司关联交易规模趋势变化。"),

            # =======================================================
            # 🔧 顶部筛选器：按钮 + Dropdown
            # =======================================================
            html.Div(
                [
                    # ---------------- 年份 ----------------
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Button("Pre-COVID", id="ov-year-pre",
                                                n_clicks=0, style={"marginRight": "6px"}),
                                    html.Button("During-COVID", id="ov-year-during",
                                                n_clicks=0, style={"marginRight": "6px"}),
                                    html.Button("Post-COVID", id="ov-year-post",
                                                n_clicks=0, style={"marginRight": "6px"}),

                                    html.Button("全选", id="ov-year-select-all",
                                                n_clicks=0, style={"marginRight": "6px"}),
                                    html.Button("全不选", id="ov-year-select-none",
                                                n_clicks=0),
                                ],
                                style={"marginBottom": "6px"},
                            ),

                            dcc.Dropdown(
                                id="overview-year-dropdown",
                                options=year_options,
                                value=years_all,
                                multi=True,
                                clearable=False,
                                style={"width": "100%"},
                            ),
                        ],
                        style={"minWidth": "280px", "width": "32%", "marginRight": "24px"},
                    ),

                    # ---------------- 省份（含区域按钮） ----------------
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Button("东北", id="ov-grp-ne", n_clicks=0, style={"marginRight": "6px"}),
                                    html.Button("华北", id="ov-grp-north", n_clicks=0, style={"marginRight": "6px"}),
                                    html.Button("华东", id="ov-grp-east", n_clicks=0, style={"marginRight": "6px"}),
                                    html.Button("华中", id="ov-grp-central", n_clicks=0, style={"marginRight": "6px"}),
                                    html.Button("华南", id="ov-grp-south", n_clicks=0, style={"marginRight": "6px"}),
                                    html.Button("西南", id="ov-grp-sw", n_clicks=0, style={"marginRight": "6px"}),
                                    html.Button("西北", id="ov-grp-nw", n_clicks=0, style={"marginRight": "6px"}),

                                    html.Button("全选", id="ov-province-select-all",
                                                n_clicks=0, style={"marginLeft": "6px"}),
                                    html.Button("全不选", id="ov-province-select-none",
                                                n_clicks=0, style={"marginLeft": "6px"}),
                                ],
                                style={"marginBottom": "8px", "display": "flex", "flexWrap": "wrap"},
                            ),

                            dcc.Dropdown(
                                id="overview-region-dropdown",
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

            # =======================================================
            # ⭐ 完整图（折线 + 阶段柱状）
            # =======================================================
            html.Div(
                [
                    dcc.Graph(id="overview-line-full"),
                    dcc.Graph(id="overview-bar-full"),
                ],
                style={"display": "flex", "flexDirection": "column", "gap": "0.7rem"},
            ),
        ]
    )

    return layout


# ============================================================
# 🅱 Callback
# ============================================================
def register_overview_callbacks(app, df):

    # =========================================================
    # 🔁 1) 年份按钮：全选 / 全不选 / 父级展开（直接替换，不叠加）
    # =========================================================
    @app.callback(
        Output("overview-year-dropdown", "value"),
        [
            Input("ov-year-pre", "n_clicks"),
            Input("ov-year-during", "n_clicks"),
            Input("ov-year-post", "n_clicks"),
            Input("ov-year-select-all", "n_clicks"),
            Input("ov-year-select-none", "n_clicks"),
        ],
        State("overview-year-dropdown", "value"),
    )
    def update_years(btn_pre, btn_during, btn_post, btn_all, btn_none, current):
        ctx = dash.callback_context
        if not ctx.triggered:
            return current
        btn_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if btn_id == "ov-year-select-all":
            all_years = []
            for group, years in year_groups.items():
                all_years += years
            return sorted(list(set(all_years)))
        if btn_id == "ov-year-select-none":
            return []
        if btn_id == "ov-year-pre":
            return sorted(year_groups["pre"])
        if btn_id == "ov-year-during":
            return sorted(year_groups["during"])
        if btn_id == "ov-year-post":
            return sorted(year_groups["post"])

        return current

    # =========================================================
    # 🔁 2) 省份按钮：区域父级 + 全选/全不选（直接替换，不累加）
    # =========================================================
    @app.callback(
        Output("overview-region-dropdown", "value"),
        [
            Input("ov-grp-ne", "n_clicks"),
            Input("ov-grp-north", "n_clicks"),
            Input("ov-grp-east", "n_clicks"),
            Input("ov-grp-central", "n_clicks"),
            Input("ov-grp-south", "n_clicks"),
            Input("ov-grp-sw", "n_clicks"),
            Input("ov-grp-nw", "n_clicks"),
            Input("ov-province-select-all", "n_clicks"),
            Input("ov-province-select-none", "n_clicks"),
        ],
        State("overview-region-dropdown", "value"),
    )
    def update_provinces(n1, n2, n3, n4, n5, n6, n7, n_all, n_none, current):
        ctx = dash.callback_context
        if not ctx.triggered:
            return current
        btn = ctx.triggered[0]["prop_id"].split(".")[0]

        if btn == "ov-province-select-all":
            all_p = []
            for lst in province_groups.values():
                all_p += lst
            return sorted(list(set(all_p)))
        if btn == "ov-province-select-none":
            return []

        mapping = {
            "ov-grp-ne": "东北",
            "ov-grp-north": "华北",
            "ov-grp-east": "华东",
            "ov-grp-central": "华中",
            "ov-grp-south": "华南",
            "ov-grp-sw": "西南",
            "ov-grp-nw": "西北",
        }
        if btn in mapping:
            grp = mapping[btn]
            return sorted(province_groups[grp])

        return current

    # =========================================================
    # 🔁 3) 图表更新：监听 dropdown + filter-store
    # =========================================================
    @app.callback(
        Output("overview-bar-small", "figure"),
        Output("overview-line-full", "figure"),
        Output("overview-bar-full", "figure"),
        Input("overview-year-dropdown", "value"),
        Input("overview-region-dropdown", "value"),
        Input("filter-store", "data"),  # ← Abstract 界面联动
    )
    def update_overview_graphs(years_selected, provinces_selected, store_data):
        ctx = dash.callback_context
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

        # 仅当触发源为 filter-store 时才覆盖 dropdown 选择
        if trigger_id == "filter-store" and store_data:
            years_selected = store_data.get("years", years_selected)
            provinces_selected = store_data.get("provinces", provinces_selected)

        # 使用统一过滤
        dff = apply_filters(df, years=years_selected, provinces=provinces_selected)

        # 聚合数据
        df_year = dff.groupby(["year", "period"], as_index=False)["isam"].sum()
        period_order = ["Pre-COVID", "During-COVID", "Post-COVID"]
        color_map = {"Pre-COVID": "#2241EC", "During-COVID": "#E89483", "Post-COVID": "#41DA90"}

        # ---------------- 小条形图 ----------------
        fig_small = px.bar(
            df_year,
            x="year",
            y="isam",
            color="period",
            text=df_year["isam"].apply(lambda v: f"{v:.2e}"),
            barmode="group",
            category_orders={"period": period_order},
            color_discrete_map=color_map,
        )
        fig_small.update_layout(
            margin=dict(l=10, r=10, t=20, b=10),
            height=180,
            showlegend=False,
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            plot_bgcolor="rgba(0,0,0,0)",
        )
        fig_small.update_traces(textposition="inside", textfont_color="white")

        # ---------------- 折线图 ----------------
        fig_line = px.line(
            df_year,
            x="year",
            y="isam",
            color="period",
            markers=True,
            category_orders={"period": period_order},
            color_discrete_map=color_map,
            title="年度关联交易总额趋势（按疫情阶段）",
        )
        fig_line.update_layout(margin=dict(l=10, r=10, t=40, b=10))

        # ---------------- 阶段柱状图 ----------------
        df_bar = df_year.copy()
        df_bar["period"] = pd.Categorical(df_bar["period"], categories=period_order, ordered=True)
        df_bar = df_bar.sort_values(["period", "year"])
        fig_bar = px.bar(
            df_bar,
            x="period",
            y="isam",
            color="period",
            text_auto=".2s",
            category_orders={"period": period_order},
            color_discrete_map=color_map,
            title="不同疫情阶段的年度关联交易总额",
        )
        fig_bar.update_layout(margin=dict(l=10, r=10, t=40, b=10))

        return fig_small, fig_line, fig_bar

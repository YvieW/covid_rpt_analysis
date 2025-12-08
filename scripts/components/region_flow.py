# components/region_flow.py
# =============================================
# 🌏 地区交易流向分析（优化版）
# - 年份分组选择（Pre / During / Post）
# - 省份筛选框宽度增强 + 自适应换行
# - 热力图 + 中国省份箭头交易流向图
# - 安全联动模式支持 filter-store
# =============================================

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import html, dcc, Input, Output, State, callback_context
import numpy as np

from .province_coords import province_coords
from .filters import year_groups, year_options, province_groups


# -------------------------------------------------
# 📌 创建交易流向布局（优化版）
# -------------------------------------------------
def create_region_flow_layout(df):
    years_all = sorted(df["year"].dropna().unique())
    provinces = sorted(list(province_coords.keys()))

    return html.Div(
        [
            # ================= 图表区 =================
            html.Div(
                [
                    dcc.Graph(
                        id="region-flow-map",
                        style={"height": "90vh", "width": "100%"},
                        config={"displayModeBar": False},
                    ),
                    dcc.Graph(id="region-flow-heat", style={"height": "40vh"}),
                ],
                style={"width": "100%", "overflow": "auto"},
            ),

            html.H3("🌏 地区间交易流向分析", className="text-center mb-3"),

            # ============ 筛选框 ===============
            html.Div(
                [
                    # ---------------- 年份 ----------------
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Button("Pre-COVID", id="year-pre", n_clicks=0, style={"marginRight": "6px"}),
                                    html.Button("During-COVID", id="year-during", n_clicks=0, style={"marginRight": "6px"}),
                                    html.Button("Post-COVID", id="year-post", n_clicks=0, style={"marginRight": "6px"}),
                                    html.Button("全选", id="year-select-all", n_clicks=0, style={"marginRight": "6px"}),
                                    html.Button("全不选", id="year-select-none", n_clicks=0),
                                ],
                                style={"marginBottom": "6px"},
                            ),
                            dcc.Dropdown(
                                id="region-flow-year",
                                options=year_options,
                                value=years_all,
                                multi=True,
                                clearable=False,
                                style={"width": "100%"},
                            ),
                        ],
                        style={"minWidth": "260px", "width": "30%", "marginRight": "25px"},
                    ),

                    # ---------------- 省份（含区域按钮） ----------------
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Button("东北", id="grp-ne", n_clicks=0, style={"marginRight": "6px"}),
                                    html.Button("华北", id="grp-north", n_clicks=0, style={"marginRight": "6px"}),
                                    html.Button("华东", id="grp-east", n_clicks=0, style={"marginRight": "6px"}),
                                    html.Button("华中", id="grp-central", n_clicks=0, style={"marginRight": "6px"}),
                                    html.Button("华南", id="grp-south", n_clicks=0, style={"marginRight": "6px"}),
                                    html.Button("西南", id="grp-sw", n_clicks=0, style={"marginRight": "6px"}),
                                    html.Button("西北", id="grp-nw", n_clicks=0, style={"marginRight": "6px"}),
                                    html.Button("全选", id="province-select-all", n_clicks=0, style={"marginLeft": "6px"}),
                                    html.Button("全不选", id="province-select-none", n_clicks=0, style={"marginLeft": "6px"}),
                                ],
                                style={"marginBottom": "8px", "display": "flex", "flexWrap": "wrap"},
                            ),
                            dcc.Dropdown(
                                id="region-flow-province",
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
        style={"padding": "10px 30px"},
    )


# =====================================================
# ✨ 图表生成函数（供 callback 调用）
# =====================================================
def generate_region_flow_figures(df):
    # =======================
    # ① 热力图
    # =======================
    df_region = (
        df.groupby(["prvn_01", "prvn_02"], as_index=False)["isam"]
        .sum()
        .sort_values("isam", ascending=False)
    )

    fig_heat = px.density_heatmap(
        df_region,
        x="prvn_01",
        y="prvn_02",
        z="isam",
        color_continuous_scale="Viridis",
        title="主公司省份 × 关联方省份：交易金额热力图",
    )
    fig_heat.update_layout(
        autosize=True,
        margin=dict(l=10, r=10, t=40, b=10),
        xaxis_tickangle=-45,
    )

    # =======================
    # ② 箭头地图
    # =======================
    df_flow = df.groupby(["prvn_01", "prvn_02", "direction"], as_index=False)["isam"].sum()
    df_flow = df_flow[
        df_flow["prvn_01"].isin(province_coords) & df_flow["prvn_02"].isin(province_coords)
    ]
    max_isam = df_flow["isam"].max() if not df_flow.empty else 1

    fig_map = go.Figure()

    # ----- 省份散点 -----
    fig_map.add_trace(go.Scattergeo(
        lon=[province_coords[p][0] for p in province_coords],
        lat=[province_coords[p][1] for p in province_coords],
        text=list(province_coords.keys()),
        mode="markers+text",
        textposition="bottom center",
        marker=dict(size=9, color="black"),
        hoverinfo="text",
    ))

    # ----- 箭头绘制 -----
    for _, row in df_flow.iterrows():
        p1, p2, direction, amount = row["prvn_01"], row["prvn_02"], row["direction"], row["isam"]

        if direction == 1:
            slon, slat = province_coords[p1]
            elon, elat = province_coords[p2]
            color = "red"
        else:
            slon, slat = province_coords[p2]
            elon, elat = province_coords[p1]
            color = "blue"

        dx, dy = elon - slon, elat - slat
        dist = np.sqrt(dx**2 + dy**2)
        offset = dist * 0.1

        lon_mid = (slon + elon) / 2 + offset * (dy / dist if dist != 0 else 0)
        lat_mid = (slat + elat) / 2 - offset * (dx / dist if dist != 0 else 0)

        t = np.linspace(0, 1, 50)
        lon_curve = (1 - t) ** 2 * slon + 2 * (1 - t) * t * lon_mid + t ** 2 * elon
        lat_curve = (1 - t) ** 2 * slat + 2 * (1 - t) * t * lat_mid + t ** 2 * elat

        width = 1.5 + 8 * (amount / max_isam)

        label = f"{p1} → {p2}" if direction == 1 else f"{p2} → {p1}"

        fig_map.add_trace(go.Scattergeo(
            lon=lon_curve,
            lat=lat_curve,
            mode="lines",
            line=dict(width=width, color=color),
            opacity=0.75,
            hoverinfo="text",
            text=f"{label}<br>金额：{amount:,.0f}",
        ))

        # ---- 箭头头部 ----
        x0, y0 = lon_curve[-2], lat_curve[-2]
        x1, y1 = lon_curve[-1], lat_curve[-1]
        dx_arrow, dy_arrow = x1 - x0, y1 - y0
        length = np.sqrt(dx_arrow ** 2 + dy_arrow ** 2)
        if length > 0:
            ux, uy = dx_arrow / length, dy_arrow / length
        else:
            ux = uy = 0
        arrow_len = 0.3
        left_x = x1 - arrow_len * (ux + uy * 0.5)
        left_y = y1 - arrow_len * (uy - ux * 0.5)
        right_x = x1 - arrow_len * (ux - uy * 0.5)
        right_y = y1 - arrow_len * (uy + ux * 0.5)

        fig_map.add_trace(go.Scattergeo(
            lon=[x1, left_x],
            lat=[y1, left_y],
            mode="lines",
            line=dict(width=width / 2, color=color),
            hoverinfo="skip",
        ))
        fig_map.add_trace(go.Scattergeo(
            lon=[x1, right_x],
            lat=[y1, right_y],
            mode="lines",
            line=dict(width=width / 2, color=color),
            hoverinfo="skip",
        ))

    fig_map.update_layout(
        geo=dict(
            scope="asia",
            projection_type="mercator",
            showcountries=False,
            lataxis=dict(range=[18, 54]),
            lonaxis=dict(range=[73, 135]),
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
    )

    return fig_heat, fig_map


# =====================================================
# 🔁 Callback 注册（安全联动版）
# =====================================================
def register_region_flow_callbacks(app, df):
    # ---------------- 年份按钮 ----------------
    @app.callback(
        Output("region-flow-year", "value"),
        [
            Input("year-pre", "n_clicks"),
            Input("year-during", "n_clicks"),
            Input("year-post", "n_clicks"),
            Input("year-select-all", "n_clicks"),
            Input("year-select-none", "n_clicks"),
        ],
        State("region-flow-year", "value"),
    )
    def update_years(btn_pre, btn_during, btn_post, btn_all, btn_none, current):
        ctx = callback_context
        if not ctx.triggered:
            return current
        btn_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if btn_id == "year-select-all":
            all_years = []
            for g in year_groups.values():
                all_years += g
            return sorted(list(set(all_years)))
        if btn_id == "year-select-none":
            return []
        if btn_id == "year-pre":
            return sorted(year_groups["pre"])
        if btn_id == "year-during":
            return sorted(year_groups["during"])
        if btn_id == "year-post":
            return sorted(year_groups["post"])
        return current

    # ---------------- 省份按钮 ----------------
    @app.callback(
        Output("region-flow-province", "value"),
        [
            Input("grp-ne", "n_clicks"),
            Input("grp-north", "n_clicks"),
            Input("grp-east", "n_clicks"),
            Input("grp-central", "n_clicks"),
            Input("grp-south", "n_clicks"),
            Input("grp-sw", "n_clicks"),
            Input("grp-nw", "n_clicks"),
            Input("province-select-all", "n_clicks"),
            Input("province-select-none", "n_clicks"),
        ],
        State("region-flow-province", "value"),
    )
    def update_provinces(*args):
        ctx = callback_context
        if not ctx.triggered:
            return args[-1]

        btn_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if btn_id == "province-select-all":
            allp = []
            for lst in province_groups.values():
                allp += lst
            return sorted(list(set(allp)))
        if btn_id == "province-select-none":
            return []

        mapping = {
            "grp-ne": "东北",
            "grp-north": "华北",
            "grp-east": "华东",
            "grp-central": "华中",
            "grp-south": "华南",
            "grp-sw": "西南",
            "grp-nw": "西北",
        }
        if btn_id in mapping:
            return sorted(province_groups[mapping[btn_id]])

        return args[-1]

    # ---------------- 更新图表 ----------------
    @app.callback(
        Output("region-flow-heat", "figure"),
        Output("region-flow-map", "figure"),
        Input("region-flow-year", "value"),
        Input("region-flow-province", "value"),
        Input("filter-store", "data"),  # ← Abstract 联动
    )
    def update_region_flow_figs(years_selected, provinces_selected, store_data):
        ctx = callback_context
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

        # 仅当触发源为 filter-store 时覆盖下拉选择
        if trigger_id == "filter-store" and store_data:
            years_selected = store_data.get("years", years_selected)
            provinces_selected = store_data.get("provinces", provinces_selected)

        # 统一过滤数据
        dff = df[
            df["year"].isin(years_selected) &
            df["prvn_02"].isin(provinces_selected)
        ]

        # 生成图表
        fig_heat, fig_map = generate_region_flow_figures(dff)
        return fig_heat, fig_map

# scripts/app.py
# ============================================================
# 📊 广东省上市公司关联交易可视化仪表盘（Dash）
# ============================================================

import os
import pandas as pd
from dash import Dash, html, dcc, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import plotly.express as px

# 导入自定义组件
from components.overview import create_overview_layout, register_overview_callbacks
from components.region_flow import create_region_flow_layout, generate_region_flow_figures, register_region_flow_callbacks
from components.industry_view import create_industry_view_layout, register_industry_view_callbacks
from components.company_network import create_company_network_layout, register_company_network_callbacks
from components.province_coords import province_coords

# ⭐ 统一过滤逻辑
from components.filters import apply_filters, year_groups, province_groups

# ============================================================
# 🧩 数据加载
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "..", "data_clean", "RPT_cleaned_guangdong.csv")

df = pd.read_csv(DATA_PATH)
print(f"✅ 数据加载完成，共 {len(df):,} 条记录")
df_original = df.copy()

years = sorted(df_original["year"].dropna().unique())
provinces = sorted(list(province_coords.keys()))

# ============================================================
# 🖥️ 初始化 Dash 应用
# ============================================================
app = Dash(
    __name__,
    use_pages=False,
    suppress_callback_exceptions=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
)
app.title = "广东省上市公司关联交易可视化仪表盘"
server = app.server

# 注册模块回调
register_overview_callbacks(app, df)
register_industry_view_callbacks(app, df)
register_company_network_callbacks(app, df)
register_region_flow_callbacks(app, df)

# ============================================================
# 🎨 顶部导航栏
# ============================================================
navbar = dbc.Navbar(
    dbc.Container(
        [
            dbc.NavbarBrand("📊 广东省上市公司关联交易分析仪表盘", className="fw-bold text-white"),
            dbc.Nav(
                [
                    dbc.NavLink("🏠 总览 (Abstract)", href="/", active="exact"),
                    dbc.NavLink("📈 总体趋势", href="/overview", active="exact"),
                    dbc.NavLink("🌏 地区流向", href="/region", active="exact"),
                    dbc.NavLink("🏭 行业分析", href="/industry", active="exact"),
                    dbc.NavLink("🏢 公司网络", href="/network", active="exact"),
                ],
                pills=True,
            ),
        ],
        fluid=True,
    ),
    color="primary",
    dark=True,
    sticky="top",
)

# ============================================================
# ===================== Abstract 筛选器 =====================
# ============================================================
def create_abstract_filter_layout(df):
    years_all = sorted(df["year"].dropna().unique())
    provinces_all = sorted(list(province_coords.keys()))

    small_btn_style = {
        "margin": "2px",
        "fontSize": "0.65rem",
        "padding": "2px 6px",
        "height": "26px",
        "minWidth": "50px",
        "borderRadius": "4px",
    }

    small_dropdown_style = {
        "fontSize": "0.7rem",
        "minHeight": "28px",
        "lineHeight": "1.2",
    }

    btn_container_style = {
        "display": "flex",
        "flexWrap": "wrap",
        "gap": "4px",
        "marginBottom": "6px",
    }

    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.Button("Pre-COVID", id="abs-year-pre", n_clicks=0, style=small_btn_style),
                            html.Button("During-COVID", id="abs-year-during", n_clicks=0, style=small_btn_style),
                            html.Button("Post-COVID", id="abs-year-post", n_clicks=0, style=small_btn_style),
                            html.Button("全选", id="abs-year-select-all", n_clicks=0, style=small_btn_style),
                            html.Button("全不选", id="abs-year-select-none", n_clicks=0, style=small_btn_style),
                        ],
                        style=btn_container_style,
                    ),
                    dcc.Dropdown(
                        id="abs-year-dropdown",
                        options=[{"label": y, "value": y} for y in years_all],
                        value=years_all,
                        multi=True,
                        clearable=False,
                        style=small_dropdown_style,
                    ),
                ],
                style={"marginBottom": "8px"},
            ),

            html.Div(
                [
                    html.Div(
                        [
                            html.Button("东北", id="abs-grp-ne", n_clicks=0, style=small_btn_style),
                            html.Button("华北", id="abs-grp-north", n_clicks=0, style=small_btn_style),
                            html.Button("华东", id="abs-grp-east", n_clicks=0, style=small_btn_style),
                            html.Button("华中", id="abs-grp-central", n_clicks=0, style=small_btn_style),
                            html.Button("华南", id="abs-grp-south", n_clicks=0, style=small_btn_style),
                            html.Button("西南", id="abs-grp-sw", n_clicks=0, style=small_btn_style),
                            html.Button("西北", id="abs-grp-nw", n_clicks=0, style=small_btn_style),
                            html.Button("全选", id="abs-province-select-all", n_clicks=0, style=small_btn_style),
                            html.Button("全不选", id="abs-province-select-none", n_clicks=0, style=small_btn_style),
                        ],
                        style=btn_container_style,
                    ),
                    dcc.Dropdown(
                        id="abs-province-dropdown",
                        options=[{"label": p, "value": p} for p in provinces_all],
                        value=provinces_all,
                        multi=True,
                        clearable=False,
                        style=small_dropdown_style,
                    ),
                ],
            ),
        ],
        style={
            "padding": "0.4rem",
            "backgroundColor": "white",
            "borderRadius": "10px",
            "boxShadow": "0 2px 5px rgba(0,0,0,0.1)",
        },
    )

# ============================================================
# ===================== Abstract 总览页 =====================
# ============================================================
abstract_layout = html.Div(
    style={
        "height": "calc(100vh - 70px)",
        "display": "grid",
        "gridTemplateRows": "25% 75%",
        "gridTemplateColumns": "1fr 1fr",
        "gap": "0.5rem",
        "padding": "0.5rem",
        "backgroundColor": "#f8f9fa",
    },
    children=[
        html.Div(create_overview_layout(df),
                 style={"gridColumn": "1 / span 1", "backgroundColor": "white",
                        "borderRadius": "12px", "boxShadow": "0 2px 5px rgba(0,0,0,0.1)",
                        "padding": "0.5rem", "overflow": "hidden"}),
        html.Div(create_industry_view_layout(df),
                 style={"gridColumn": "2 / span 1", "backgroundColor": "white",
                        "borderRadius": "12px", "boxShadow": "0 2px 5px rgba(0,0,0,0.1)",
                        "padding": "0.5rem", "overflow": "hidden"}),

        html.Div(
            style={"display": "grid", "gridTemplateRows": "0.25fr 0.75fr", "gap": "0.5rem"},
            children=[
                html.Div(create_abstract_filter_layout(df), style={"overflow": "hidden"}),
                html.Div(create_company_network_layout(df, compact=True),
                         style={"backgroundColor": "white",
                                "borderRadius": "12px",
                                "boxShadow": "0 2px 5px rgba(0,0,0,0.1)",
                                "padding": "0.5rem", "overflow": "hidden"}),
            ],
        ),

        html.Div(create_region_flow_layout(df),
                 style={"backgroundColor": "white",
                        "borderRadius": "12px",
                        "boxShadow": "0 2px 5px rgba(0,0,0,0.1)",
                        "padding": "0.5rem", "overflow": "hidden"}),
    ],
)

# ============================================================
# ===================== 单页布局 =====================
# ============================================================
overview_page = dbc.Container(create_overview_layout(df), fluid=True, class_name="p-3")
region_page = dbc.Container(create_region_flow_layout(df), fluid=True, class_name="p-3")
industry_page = dbc.Container(create_industry_view_layout(df), fluid=True, class_name="p-3")
network_page = dbc.Container(create_company_network_layout(df, compact=False), fluid=True, class_name="p-3")

# ============================================================
# ===================== 主体框架 =====================
# ============================================================
app.layout = html.Div([
    dcc.Location(id="url"),
    navbar,
    dcc.Store(id="filter-store", data={"years": years, "provinces": provinces}),
    html.Div(id="page-content", style={"height": "100vh"}),
])

# ============================================================
# 页面切换回调
# ============================================================
@app.callback(Output("page-content", "children"), Input("url", "pathname"))
def render_page(pathname):
    if pathname == "/overview":
        return overview_page
    elif pathname == "/region":
        return region_page
    elif pathname == "/industry":
        return industry_page
    elif pathname == "/network":
        return network_page
    else:
        return abstract_layout

# ============================================================
# ===================== Store 联动回调（按钮触发） =====================
# ============================================================
@app.callback(
    Output("filter-store", "data"),
    [
        Input("abs-year-pre", "n_clicks"),
        Input("abs-year-during", "n_clicks"),
        Input("abs-year-post", "n_clicks"),
        Input("abs-year-select-all", "n_clicks"),
        Input("abs-year-select-none", "n_clicks"),
        Input("abs-grp-ne", "n_clicks"),
        Input("abs-grp-north", "n_clicks"),
        Input("abs-grp-east", "n_clicks"),
        Input("abs-grp-central", "n_clicks"),
        Input("abs-grp-south", "n_clicks"),
        Input("abs-grp-sw", "n_clicks"),
        Input("abs-grp-nw", "n_clicks"),
        Input("abs-province-select-all", "n_clicks"),
        Input("abs-province-select-none", "n_clicks"),
    ],
    State("filter-store", "data"),
    prevent_initial_call=True
)
def update_filter_store_buttons(
    year_pre, year_during, year_post, year_all, year_none,
    grp_ne, grp_north, grp_east, grp_central, grp_south, grp_sw, grp_nw,
    province_all, province_none,
    store_data
):
    if not isinstance(store_data, dict):
        store_data = {"years": years, "provinces": provinces}

    years_sel = store_data.get("years", years)
    provinces_sel = store_data.get("provinces", provinces)
    ctx = callback_context.triggered_id

    if ctx == "abs-year-pre":
        years_sel = year_groups["pre"]
    elif ctx == "abs-year-during":
        years_sel = year_groups["during"]
    elif ctx == "abs-year-post":
        years_sel = year_groups["post"]
    elif ctx == "abs-year-select-all":
        years_sel = year_groups["pre"] + year_groups["during"] + year_groups["post"]
    elif ctx == "abs-year-select-none":
        years_sel = []

    group_map = {
        "abs-grp-ne": "东北",
        "abs-grp-north": "华北",
        "abs-grp-east": "华东",
        "abs-grp-central": "华中",
        "abs-grp-south": "华南",
        "abs-grp-sw": "西南",
        "abs-grp-nw": "西北",
    }
    if ctx in group_map:
        provinces_sel = province_groups[group_map[ctx]]
    elif ctx == "abs-province-select-all":
        provinces_sel = sorted(list(province_coords.keys()))
    elif ctx == "abs-province-select-none":
        provinces_sel = []

    return {"years": years_sel, "provinces": provinces_sel}

# ============================================================
# ===================== Store 同步 Dropdown =====================
# ============================================================
@app.callback(
    Output("abs-year-dropdown", "value"),
    Output("abs-province-dropdown", "value"),
    Input("filter-store", "data")
)
def sync_dropdown_from_store(store_data):
    return store_data.get("years", years), store_data.get("provinces", provinces)

# ============================================================
# ===================== Dropdown 更新 Store =====================
# ============================================================
@app.callback(
    Output("filter-store", "data", allow_duplicate=True),
    Input("abs-year-dropdown", "value"),
    Input("abs-province-dropdown", "value"),
    State("filter-store", "data"),
    prevent_initial_call=True
)
def update_store_from_dropdown(dropdown_years, dropdown_provinces, store_data):
    return {
        "years": dropdown_years or [],
        "provinces": dropdown_provinces or []
    }

# ============================================================
# 各模块监听 Store
# ============================================================
# Input("filter-store", "data") 来实现联动，这里保留现有注册函数

# ============================================================
# 🚀 启动应用
# ============================================================
if __name__ == "__main__":
    app.run(debug=True, port=8050)

import streamlit as st
import pandas as pd


# 一、读取admin区划信息
@st.cache_data
def load_admin():
    df = pd.read_stata('county_2015.dta')
    df['province_city_county'] = df['province'] + ' ' + df['city'] + ' ' + df['county']
    return df


admin_df = load_admin()
# 提供全省/全市/全县
admin_df['county'] = admin_df['county'].fillna('全县')
admin_df['city'] = admin_df['city'].fillna('全市')
admin_df['province'] = admin_df['province'].fillna('全省')

# 用于最终数据录入
if 'input_records' not in st.session_state:
    st.session_state.input_records = []

st.title("光伏补贴政策录入工具")

# 二、录入区域
st.subheader("选择行政区（两种方式任选其一）")

# 1. 方案一：模糊搜索整体匹配
query_text = st.text_input("（推荐）请输入省/市/县任意名称进行模糊搜索:")

search_candidates = pd.DataFrame()
if query_text.strip():  # 输入了查询文本
    # 可同时在省、市、县、拼接字段模糊匹配
    mask = admin_df['province'].str.contains(query_text, na=False) \
           | admin_df['city'].str.contains(query_text, na=False) \
           | admin_df['county'].str.contains(query_text, na=False) \
           | admin_df['province_city_county'].str.contains(query_text, na=False)
    search_candidates = admin_df[mask]

    if not search_candidates.empty:
        # 只展示前50条，防卡
        selected_idx = st.selectbox("请选择匹配行政区:",
                                    search_candidates.head(50).apply(
                                        lambda row: f"{row['province']} / {row['city']} / {row['county']}", axis=1
                                    )
                                    )
        # 解析目前select的省、市、县
        selected_row = search_candidates[
            search_candidates['province'] + ' / ' + search_candidates['city'] + ' / ' + search_candidates[
                'county'] == selected_idx].iloc[0]
        province, city, county = selected_row['province'], selected_row['city'], selected_row['county']
    else:
        selected_row = None
        province, city, county = '', '', ''

else:
    selected_row = None
    province, city, county = '', '', ''

st.markdown("___\n或手动选择：")

# 2. 方案二：级联选择（下拉框）
all_provinces = sorted(admin_df['province'].unique().tolist())
province_sel = st.selectbox("省份", all_provinces,
                            index=all_provinces.index(province) if province in all_provinces else 0)
cities = sorted(admin_df[admin_df['province'] == province_sel]['city'].unique().tolist() + ['全省'])
city_sel = st.selectbox("城市", cities, index=cities.index(city) if city in cities else 0)

counties = sorted(
    admin_df[(admin_df['province'] == province_sel) & (admin_df['city'] == city_sel)]['county'].unique().tolist() + [
        '全市'])
county_sel = st.selectbox("县/区", counties, index=counties.index(county) if county in counties else 0)

# 补贴字段
st.subheader("补贴政策填写")
st.caption("补贴数据的对象为分布式农户用光伏这一类型")

# 起始时间和终止时间分开填写年、月、日
col1, col2, col3 = st.columns(3)
with col1:
    year_from = st.number_input("起始年份", min_value=2000, max_value=2050, value=2023, step=1)
    year_to = st.number_input("终止年份", min_value=2000, max_value=2050, value=2025, step=1)
with col2:
    month_from = st.number_input("起始月份", min_value=1, max_value=12, value=1, step=1)
    month_to = st.number_input("终止月份", min_value=1, max_value=12, value=12, step=1)
with col3:
    day_from = st.number_input("起始日期", min_value=1, max_value=31, value=1, step=1)
    day_to = st.number_input("终止日期", min_value=1, max_value=31, value=31, step=1)

# 补贴类型
subsidy_type = st.selectbox(
    "补贴类型",
    options=["度电补贴", "初装补贴"],
    index=0
)

# 补贴价格
price = st.number_input("补贴价格", min_value=0.0, step=0.01, value=0.10, format="%.3f")

# 单位选择（含其它，允许自定义输入）
unit_options = ["W", "kW", "KWh", "其它"]
unit_selected = st.selectbox("单位", options=unit_options, index=0)

if unit_selected == "其它":
    unit = st.text_input("请自定义单位")
else:
    unit = unit_selected

remark = st.text_input("备注(可选)", value='')

# 保存录入
if st.button("添加本条数据"):
    # 时间格式整理为yyyy-mm-dd
    from_str = f"{int(year_from):04d}-{int(month_from):02d}-{int(day_from):02d}"
    to_str = f"{int(year_to):04d}-{int(month_to):02d}-{int(day_to):02d}"
    record = {
        'province': province_sel,
        'city': city_sel,
        'county': county_sel,
        'date_from': from_str,
        'date_to': to_str,
        'subsidy_type': subsidy_type,
        'price': price,
        'unit': unit,
        '备注': remark,
    }
    st.session_state.input_records.append(record)
    st.success("记录添加成功！")


# 三、录入数据汇总展示
st.subheader("已录入政策数据")
if st.session_state.input_records:
    df_input = pd.DataFrame(st.session_state.input_records)
    st.dataframe(df_input)
    st.download_button("下载全部数据为CSV", df_input.to_csv(index=False), file_name="policy_input.csv")
else:
    st.info("暂无录入数据。")

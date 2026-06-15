import streamlit as st
import re
import datetime
import pandas as pd


# ========== 核心验证逻辑（完全复用你的代码）==========
def clean_id_card(id_card):
    """清理身份证号码中的特殊字符"""
    if not id_card:
        return ""
    cleaned = re.sub(r"['\s\n\t]", "", str(id_card))
    return cleaned


def validate_id_card(id_card):
    """验证单个身份证号码的合法性（复用你的逻辑）"""
    if not id_card:
        return "身份证号码为空"

    id_card = clean_id_card(id_card)

    if not re.match(r'^\d{15}$|^\d{17}[\dXx]$', id_card):
        return f"格式错误：必须是15位或18位数字，当前为{len(id_card)}位"

    area_code = id_card[:6]
    if not area_code.isdigit():
        return "地区码错误：必须为数字"

    if len(id_card) == 15:
        birth_date = "19" + id_card[6:12]
    else:
        birth_date = id_card[6:14]

    try:
        year = int(birth_date[:4])
        month = int(birth_date[4:6])
        day = int(birth_date[6:8])
        current_year = datetime.datetime.now().year
        if year < 1900 or year > current_year:
            return f"出生年份错误：{year}"
        if month < 1 or month > 12:
            return f"出生月份错误：{month}"
        if day < 1 or day > 31:
            return f"出生日期错误：{day}"
        datetime.datetime.strptime(birth_date, '%Y%m%d')
    except ValueError:
        return f"出生日期错误：{birth_date}"

    if len(id_card) == 15:
        return "正确（15位）"

    # 校验码验证
    check_result = calculate_check_code(id_card)
    if id_card[17].upper() != check_result:
        return f"校验码错误：应为{check_result}，实际为{id_card[17]}"

    return "正确"


def calculate_check_code(id_card):
    """计算18位身份证的校验码"""
    if len(id_card) != 18:
        return "长度错误"
    factors = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    check_codes = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']
    first_17 = id_card[:17]
    if not first_17.isdigit():
        return "前17位必须为数字"
    total = 0
    for i in range(17):
        total += int(first_17[i]) * factors[i]
    return check_codes[total % 11]


def extract_id_card_from_columns(columns):
    """从列数据中提取身份证号码"""
    for i in range(len(columns) - 1, -1, -1):
        cleaned = clean_id_card(columns[i])
        if re.match(r'^\d{15}$|^\d{17}[\dXx]$', cleaned):
            return cleaned, i
    return None, -1


def is_header_row(columns):
    """判断是否为标题行"""
    if len(columns) < 2:
        return False
    second_column = columns[1]
    return not any(char.isdigit() for char in str(second_column))


def process_validation(input_data):
    """执行验证并返回结果DataFrame和统计信息"""
    if not input_data:
        return None, 0, 0

    lines = input_data.strip().split('\n')
    results_data = []
    valid_count = 0
    total_count = 0

    for line_num, line in enumerate(lines, 1):
        original_line = line.strip()
        if not original_line:
            continue

        columns = re.split(r'\s+', original_line)

        # 标题行处理
        if line_num == 1 and is_header_row(columns):
            continue

        total_count += 1
        id_card, _ = extract_id_card_from_columns(columns)

        if id_card is None:
            result = {
                "原始数据": original_line,
                "身份证号": "未识别",
                "验证结果": "❌ 未找到身份证号码",
                "状态": "错误"
            }
        else:
            validation_result = validate_id_card(id_card)
            if "正确" in validation_result:
                valid_count += 1
                result = {
                    "原始数据": original_line,
                    "身份证号": id_card,
                    "验证结果": f"✅ {validation_result}",
                    "状态": "正确"
                }
            else:
                result = {
                    "原始数据": original_line,
                    "身份证号": id_card,
                    "验证结果": f"❌ {validation_result}",
                    "状态": "错误"
                }
        results_data.append(result)

    df = pd.DataFrame(results_data)
    return df, valid_count, total_count


# ========== Streamlit UI 部分 ==========
st.set_page_config(page_title="身份证号码检验工具", page_icon="🪪", layout="wide")

# 标题
st.title("身份证号码检验工具")
st.caption("Design by Leo")

# 侧边栏说明
with st.sidebar:
    st.markdown("### 📖 使用说明")
    st.markdown("""
    1. 在下方文本框中粘贴数据
    2. 支持格式：
       - 序号 + 身份证
       - 姓名 + 身份证
       - 多列数据（自动识别哪列是身份证）
    3. 点击「开始检验」
    4. 可使用筛选功能查看结果（不会丢失数据）
    """)
    st.markdown("---")
    st.markdown("### ✨ 功能提示")
    st.markdown("""
    - ✅ 支持15位/18位身份证
    - ✅ 自动识别身份证列
    - ✅ 验证地区码、出生日期、校验码
    - ✅ 可导出结果
    - ✅ 筛选不丢失数据
    - ✅ 错误信息仅供参考，请自行核对
    """)

# 主区域分两列
col1, col2 = st.columns([3, 2])

with col1:
    # 数据输入区
    st.subheader("📝 数据输入")
    input_data = st.text_area(
        "请粘贴数据（支持从Excel复制多行多列）",
        height=250,
        placeholder="示例：\n张三 11010119900307663X\n李四 310101198001011234\n或者带序号：\n1. 11010119900307663X\n2. 310101198001011234",
        help="每行一条数据，列之间用空格或Tab分隔",
        key="input_text_area"  # 添加key避免重复渲染问题
    )

    # 操作按钮
    btn_col1, btn_col2, btn_col3, btn_col4 = st.columns(4)
    with btn_col1:
        validate_btn = st.button("🔍 开始检验", type="primary", use_container_width=True)
    with btn_col2:
        clear_btn = st.button("🗑️ 清空", use_container_width=True)
    with btn_col3:
        # 添加一个重置筛选的按钮
        reset_filter_btn = st.button("🔄 重置筛选", use_container_width=True)
    with btn_col4:
        st.markdown(" ")  # 占位

with col2:
    st.subheader("📊 统计信息")
    stats_placeholder = st.empty()

# ========== 使用session_state保存验证结果 ==========
# 初始化session_state
if 'validation_df' not in st.session_state:
    st.session_state.validation_df = None
if 'valid_count' not in st.session_state:
    st.session_state.valid_count = 0
if 'total_count' not in st.session_state:
    st.session_state.total_count = 0
if 'last_input' not in st.session_state:
    st.session_state.last_input = ""
if 'status_filter' not in st.session_state:
    st.session_state.status_filter = "全部"
if 'search_term' not in st.session_state:
    st.session_state.search_term = ""

# 处理清空
if clear_btn:
    st.session_state.validation_df = None
    st.session_state.valid_count = 0
    st.session_state.total_count = 0
    st.session_state.last_input = ""
    st.session_state.status_filter = "全部"
    st.session_state.search_term = ""
    st.rerun()

# 处理重置筛选
if reset_filter_btn:
    st.session_state.status_filter = "全部"
    st.session_state.search_term = ""
    st.rerun()

# 处理验证（点击按钮或者数据变化时自动验证）
need_validate = False

if validate_btn:
    if input_data:
        need_validate = True
        st.session_state.last_input = input_data
    else:
        st.warning("⚠️ 请在文本框中输入数据")

# 如果session中有数据但没有验证结果，且有输入数据，自动验证
elif st.session_state.last_input and st.session_state.validation_df is None:
    need_validate = True
    input_data = st.session_state.last_input

# 执行验证
if need_validate and input_data:
    df, valid_count, total_count = process_validation(input_data)
    if df is not None and not df.empty:
        st.session_state.validation_df = df
        st.session_state.valid_count = valid_count
        st.session_state.total_count = total_count
        # 重置筛选状态
        st.session_state.status_filter = "全部"
        st.session_state.search_term = ""

# 显示统计和结果（如果有验证结果）
if st.session_state.validation_df is not None and not st.session_state.validation_df.empty:
    df = st.session_state.validation_df

    # 显示统计
    error_count = st.session_state.total_count - st.session_state.valid_count
    with stats_placeholder:
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("总计", st.session_state.total_count)
        col_b.metric("正确", st.session_state.valid_count)
        col_c.metric("错误", error_count, delta=None if error_count == 0 else f"-{error_count}")

    # 筛选器（使用session_state保持状态）
    st.subheader("🔎 筛选与查看")
    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        # 使用session_state保持筛选值
        current_filter = st.selectbox(
            "按状态筛选",
            ["全部", "正确", "错误"],
            index=["全部", "正确", "错误"].index(st.session_state.status_filter),
            key="status_filter_select"
        )
        st.session_state.status_filter = current_filter
    with filter_col2:
        current_search = st.text_input(
            "搜索关键词",
            value=st.session_state.search_term,
            placeholder="输入姓名或身份证号",
            key="search_input"
        )
        st.session_state.search_term = current_search

    # 应用筛选
    filtered_df = df.copy()
    if st.session_state.status_filter != "全部":
        filtered_df = filtered_df[filtered_df["状态"] == st.session_state.status_filter]
    if st.session_state.search_term:
        filtered_df = filtered_df[
            filtered_df["原始数据"].str.contains(st.session_state.search_term, na=False) |
            filtered_df["身份证号"].str.contains(st.session_state.search_term, na=False)
            ]

    # 显示结果表格
    st.subheader("📋 验证结果")

    # 显示筛选结果数量
    st.caption(f"当前显示 {len(filtered_df)} 条记录（共 {len(df)} 条）")


    # 使用自定义颜色样式
    def color_status(val):
        if "✅" in str(val):
            return "background-color: #90EE90"
        elif "❌" in str(val):
            return "background-color: #FFB6C1"
        return ""


    styled_df = filtered_df.style.map(color_status, subset=["验证结果"])
    st.dataframe(styled_df, use_container_width=True, height=400)

    # 导出功能
    if not filtered_df.empty:
        csv = filtered_df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            label="📥 导出结果为CSV",
            data=csv,
            file_name=f"身份证验证结果_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )

    # 如果当前显示的是筛选后的错误数据，添加一个快速定位按钮
    if st.session_state.status_filter == "错误" and len(filtered_df) > 0:
        st.info(f"💡 发现 {len(filtered_df)} 条错误记录，可点击上方「导出结果为CSV」保存错误列表")

elif validate_btn and input_data and (st.session_state.validation_df is None or st.session_state.validation_df.empty):
    st.warning("⚠️ 没有找到有效的身份证数据，请检查输入格式")

# 页脚
st.markdown("---")
st.caption("💡 提示：支持15位和18位身份证号码，自动验证地区码、出生日期和校验码。筛选和搜索不会丢失验证结果。")
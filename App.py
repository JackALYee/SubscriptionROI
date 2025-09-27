import streamlit as st

st.set_page_config(page_title="Subscription Price & ROI Calculator", layout="centered")

st.title("Subscription Pricing & ROI Calculator")
st.write("锐明产品市场一部  jcyi@streamax.com")

with st.sidebar:
    st.header("设备参数")
    currency = st.selectbox("Currency", ["USD", "EUR", "CNY", "Other"], index=0)
    # 原始设备成本（未折价前）
    C_E_input = st.number_input("Equipment cost (C_E)", min_value=0.0, value=200.0, step=1.0, help="设备DDP成本")
    S_E = 0.0
    
    sale_mode = st.radio("销售策略", ["Free Equipment", "Equipment Sales"],help="当Equipement售价为0时，即等于Free Equipment")
  
    # 销售模式
    if sale_mode == "Free Equipment":
        S_E = 0.0
    else:
        S_E = st.number_input("Equipment Selling Price", min_value=0.0, value=240.0, step=1.0, help="设备售价")
       #More code here
      
    st.subheader("运营参数")
    C_h = st.number_input("Monthly hosting cost", min_value=0.0, value=1.0, step=0.05, help="运营平台月成本")
    C_c = st.number_input("Monthly capital cost", min_value=0.0, value=0.3, step=0.05, help="贷款利息")
    C_o = st.number_input("Other monthly cost", min_value=0.0, value=0.3, step=0.05, help="其他成本如流量运营商月费等")
    C_d = st.number_input("Data cost per GB per month (C_d)", min_value=0.0, value=4.00, step=0.10, help="每GB价格")
    Q_gb = st.number_input("Monthly data usage (Q_gb, GB)", min_value=0.0, value=3.0, step=0.5)

    st.subheader("选择订阅价计算模式")
    pricing_mode = st.radio("Pricing mode", ["By Target Margin", "By Target Payback (months)"], help="建议的订阅价将根据选择的目标回本时间或目标利润率计算得出")
    amort_months = st.number_input("Amortization months (for margin calculation)", min_value=1, value=36, step=1, help="将设备成本月度化。月度值应为订阅合同时长期限。")

    if pricing_mode == "By Target Margin":
        margin_pct_input = st.number_input("Target margin (%)", min_value=0.0, value=30.0, step=1.0, help="期望的margin")
        payback_target_months = None
    else:
        payback_target_months = st.number_input("Target payback period (months)", min_value=1.0, value=18.0, step=1.0, help="期望的回本时间")
        margin_pct_input = None

    st.subheader("锚定参考价")
    p_samsara = st.number_input("Benchmark Price", min_value=0.0, value=25.00, step=0.5, help="订阅费参考价格, 默认Samsara的25 USD/mo.")

# ---------------------------
# 核心派生值（不涉及“折价设备”的特殊处理）
# ---------------------------
C_p = C_h + C_c + C_o
monthly_cost_ops = C_p + C_d * Q_gb  # 仅运营的月成本

# 记录原始设备成本（折价前）
C_E_old = C_E_input

# 计算“折价后设备成本”
C_E_effective = C_E_old - S_E  # 作为成本基数参与后续逻辑

# 设备月度化（仅当有效设备成本>0时计入）
equip_amort_per_month = (C_E_effective / amort_months) if (amort_months > 0 and C_E_effective > 0) else 0.0
cost_base_for_margin = monthly_cost_ops + equip_amort_per_month  # 用于利润率计算的成本基数（运营+设备月度化）

# ---------------------------
# 定价与盈利逻辑
# ---------------------------
# 统一的输出占位
suggested_price = 0.0
monthly_gross_profit = 0.0
effective_margin_pct = None
payback_months = None
roi_annual = None

# 特殊规则：只有在“Equipment Sales”模式下，才触发“负设备成本”的处理分支
if sale_mode == "Equipment Sales" and C_E_effective < 0:
    # 1) 禁用“By Target Payback (months)”模式（强制切换为 margin 模式）
    if pricing_mode == "By Target Payback (months)":
        st.warning("设备折价后为负成本（C_E - S_E < 0），已禁用 “By Target Payback (months)” 模式并自动切换为 “By Target Margin”。")
    pricing_mode = "By Target Margin"

    # 2) 计算设备销售带来的“当前利润率”（相对于原始设备成本）
    margin_current = ((S_E - C_E_old) / C_E_old) if C_E_old > 0 else 0.0

    # 取目标利润率（若用户未输入则按0）
    target_margin = (margin_pct_input or 0.0) / 100.0

    # 3) 按指令执行：
    # i) 若 target_margin > margin_current，则订阅费设为 0；
    if target_margin > margin_current:
        suggested_price = 0.0
        monthly_gross_profit = 0.0
        effective_margin_pct = target_margin * 100.0
        payback_months = None  # 已关闭回本模式
        amort_total = monthly_cost_ops  # 不再计入设备月度成本
        roi_annual = None
    else:
        # ii) 否则（target_margin <= margin_current）：
        #     订阅利润率仅基于运营月成本，不再考虑设备月度化成本；
        #     且“订阅利润率 + 设备折价利润率 = 目标利润率”
        sub_margin = max(0.0, target_margin - margin_current)  # 理论上应为0
        monthly_gross_profit = sub_margin * monthly_cost_ops
        suggested_price = monthly_cost_ops + monthly_gross_profit
        effective_margin_pct = (sub_margin * 100.0)  # 显示订阅端利润率
        payback_months = None  # 已关闭回本模式
        amort_total = monthly_cost_ops  # 不计设备月度成本
        roi_annual = None
else:
    # 其余情况（包含 Free Equipment，或 Discounted 但 C_E_effective >= 0）：
    # 原始逻辑保持不变：利润率要考虑设备月度化成本
    if pricing_mode == "By Target Margin":
        margin = (margin_pct_input or 0.0) / 100.0
        monthly_gross_profit = margin * cost_base_for_margin
        suggested_price = monthly_cost_ops + monthly_gross_profit
        effective_margin_pct = margin_pct_input
        payback_months = (C_E_effective / monthly_gross_profit) if monthly_gross_profit > 0 and C_E_effective > 0 else None
    else:
        # By Target Payback (months)
        monthly_gross_profit = (C_E_effective / payback_target_months) if C_E_effective > 0 else 0.0
        suggested_price = monthly_cost_ops + monthly_gross_profit
        effective_margin_pct = (monthly_gross_profit / cost_base_for_margin * 100.0) if cost_base_for_margin > 0 else None
        payback_months = payback_target_months if C_E_effective > 0 else None

    amort_total = monthly_cost_ops + equip_amort_per_month
    roi_annual = (monthly_gross_profit * 12.0 / C_E_effective) if C_E_effective > 0 else None

# 年化利润
annual_gross_profit = monthly_gross_profit * 12.0
if roi_annual is None and C_E_effective > 0:
    roi_annual = (annual_gross_profit / C_E_effective) if C_E_effective > 0 else None

# ---------------------------
# 手动订阅价输入（当设备售价 > 设备成本时启用）
# 需求：若 S_E > C_E_old，则出现可编辑输入框；否则展示禁用输入框。
# 并计算：订阅端利润率（基于运营成本）+ 设备销售利润率（相对设备成本）的“合并利润率”
# ---------------------------
enable_manual_price = (sale_mode == "Equipment Sales" and S_E > C_E_old)

st.subheader("手动订阅费设置")
if enable_manual_price:
    manual_sub_price = st.number_input(
        "Set Subscription Price (Manual)",
        min_value=0.0,
        value=float(f"{max(suggested_price, monthly_cost_ops):.2f}"),
        step=0.5,
        help="当设备售价高于设备成本时可手动设定订阅费，用于查看合并利润率。"
    )
else:
    manual_sub_price = st.number_input(
        "Set Subscription Price (Manual)",
        min_value=0.0,
        value=0.0,
        step=0.5,
        disabled=True,
        help="设备售价未高于设备成本，手动订阅价不可用。"
    )

# 计算合并利润率（仅在启用时展示）
combined_margin_pct = None
equip_margin_pct = None
sub_margin_pct_manual = None
if enable_manual_price:
    # 设备销售利润率（相对设备成本）
    equip_margin_pct = ((S_E - C_E_old) / C_E_old * 100.0) if C_E_old > 0 else None
    # 订阅端利润率（仅基于运营月成本，不计设备月度化成本）
    sub_margin_pct_manual = ((manual_sub_price - monthly_cost_ops) / monthly_cost_ops * 100.0) if monthly_cost_ops > 0 else None
    # 合并利润率：设备 + 订阅（百分比求和）
    if (equip_margin_pct is not None) and (sub_margin_pct_manual is not None):
        combined_margin_pct = equip_margin_pct + sub_margin_pct_manual

# ---------------------------
# 展示
# ---------------------------
st.subheader("Suggested Subscription Pricing")
col_1, col_2 = st.columns(2)
col_1.metric(label="Monthly cost basis (仅运营)", value=f"{monthly_cost_ops:,.2f} {currency}")
col_2.metric(label="Monthly cost basis (运营+设备月度成本)", value=f"{amort_total:,.2f} {currency}")
col_2.caption("*设备月度成本=设备总成本/合同期限（当折价后设备成本≤0时不计入）")

if effective_margin_pct is not None:
    st.metric(label="Margin (%)", value=f"{effective_margin_pct:.1f} %")
    st.caption("*利润率=月利润/(月运营成本+设备月度成本)。若折价后设备成本为负，订阅端利润率仅基于运营成本。")
else:
    st.metric(label="Margin (%)", value="N/A")

if suggested_price > p_samsara:
    st.metric(
        label="Suggested monthly price",
        value=f"{suggested_price:,.2f} {currency}",
        delta=f"+{suggested_price - p_samsara:,.2f}",
        delta_color="inverse"
    )
    st.caption(f"Comparing with benchmarked price {p_samsara} {currency}")
else:
    st.metric(
        label="Suggested monthly price",
        value=f"{suggested_price:,.2f} {currency}",
        delta=f"{suggested_price - p_samsara:,.2f}",
        delta_color="inverse"
    )
    st.caption(f"Comparing with benchmarked price {p_samsara:,.2f} {currency}")

st.subheader("Profitability")
col1, col2, col3 = st.columns(3)
col1.metric(label="Monthly gross profit", value=f"{monthly_gross_profit:,.2f} {currency}")
col2.metric(label="Annual gross profit", value=f"{annual_gross_profit:,.2f} {currency}")
if roi_annual is not None:
    col3.metric(label="Annual ROI vs. equipment", value=f"{roi_annual*100:,.1f}%")
else:
    col3.metric(label="Annual ROI vs. equipment", value="N/A")

st.subheader("Payback Period")
if payback_months is None:
    st.info("Payback period: N/A (monthly gross profit is 0 or negative, 或设备折价为负已禁用回本模式)。")
else:
    years = payback_months / 12.0
    c1, c2 = st.columns(2)
    c1.metric(label="Payback (months)", value=f"{payback_months:,.1f}")
    c1.caption(f"≈ {years:,.2f} years")
    c2.metric(
        label=f"Total Profit Earned for a Contract of {amort_months} mo.",
        value=f"{(amort_months - payback_months) * monthly_gross_profit:,.2f} {currency}"
    )
    c2.caption(f"You earn {amort_months - payback_months:,.2f} mo. of profit")

st.subheader("Cost & Price Breakdown (Monthly)")
st.table({
    "Item": [
        "Monthly Fixed Cost",
        "Data (C_d × Q_gb)",
        (f"Equipment amort. (C_E ÷ {amort_months} mo)" if C_E_effective > 0 else "Equipment amort. (not applied)"),
        "Total cost base (for margin)",
        "Margin %",
        "Suggested price"
    ],
    "Value": [
        f"{C_p:,.2f} {currency}",
        f"{(C_d * Q_gb):,.2f} {currency}",
        f"{equip_amort_per_month:,.2f} {currency}" if C_E_effective > 0 else "0.00",
        f"{cost_base_for_margin:,.2f} {currency}" if C_E_effective > 0 else f"{monthly_cost_ops:,.2f} {currency}",
        f"{effective_margin_pct:.1f} %" if effective_margin_pct is not None else "N/A",
        f"{suggested_price:,.2f} {currency}"
    ]
})

# 手动订阅价的合并利润率展示
if enable_manual_price and combined_margin_pct is not None:
    st.subheader("Combined Margin (Equipment Sale + Subscription, Manual Price)")
    cm1, cm2, cm3 = st.columns(3)
    cm1.metric("Equipment margin (%)", value=f"{equip_margin_pct:.1f}%")
    cm2.metric("Subscription margin (%)", value=f"{sub_margin_pct_manual:.1f}%")
    cm3.metric("Combined margin (%)", value=f"{combined_margin_pct:.1f}%")
    st.caption("合并利润率 = 设备销售利润率（相对设备成本） + 订阅利润率（相对运营月成本）。")

st.caption(
    "Notes: In 'By Target Margin' mode, margin is applied to (Ops cost + equipment amortization) when 折价后设备成本>0；"
    "若折价后设备成本<0，则禁用回本模式，订阅端利润率仅基于运营成本，且需与设备折价所得的当前利润率合计满足目标利润率。"
    "当设备售价高于设备成本时，可手动设定订阅价以查看“设备+订阅”的合并利润率。"
)

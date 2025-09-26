import streamlit as st

st.set_page_config(page_title="Subscription Price & ROI Calculator", layout="centered")

st.title("Subscription Pricing & ROI Calculator")
st.write("锐明产品市场一部 内部计算器")

with st.sidebar:
    st.header("参数")
    currency = st.selectbox("Currency", ["USD", "EUR", "CNY", "Other"], index=0)
    C_E = st.number_input("Equipment cost (C_E)", min_value=0.0, value=200.0, step=10.0, help="请用DDP成本")
    C_h = st.number_input("Monthly hosting cost", min_value=0.0, value=1.0, step=0.05, help="运营平台月成本")
    C_c = st.number_input("Monthly capital cost", min_value=0.0, value=0.3, step=0.05, help="贷款利息")
    C_o = st.number_input("Other monthly cost", min_value=0.0, value=0.3, step=0.05, help="其他成本如流量运营商月费等")
    C_d = st.number_input("Data cost per GB per month (C_d)", min_value=0.0, value=4.00, step=0.10, help="每GB价格")
    Q_gb = st.number_input("Monthly data usage (Q_gb, GB)", min_value=0.0, value=3.0, step=0.5)
    st.subheader("选择订阅价计算模式")
    pricing_mode = st.radio("Pricing mode", ["By Target Margin", "By Target Payback (months)"],help="建议的订阅价将根据选择的目标回本时间或目标利润率计算得出")
    amort_months = st.number_input("Amortization months (for margin calculation)", min_value=1, value=36, step=1,help="将设备成本月度化")

    if pricing_mode == "By Target Margin":
        margin_pct_input = st.number_input("Target margin (%)", min_value=0.0, value=30.0, step=1.0, help="期望的margin")
        payback_target_months = None
    else:
        payback_target_months = st.number_input("Target payback period (months)", min_value=1.0, value=18.0, step=1.0, help="期望的回本时间")
        margin_pct_input = None
    st.subheader("锚定参考价")
    p_samsara = st.number_input("Benchmark Price", min_value=0.0, value=25.0, step=0.5, help="订阅费参考价格, 默认Samsara的25 USD/mo.")
# Core derived values
C_p=C_h+C_c+C_o
monthly_cost_ops = C_p + C_d * Q_gb  # ops-only monthly cost
equip_amort_per_month = C_E / amort_months if amort_months > 0 else 0.0
cost_base_for_margin = monthly_cost_ops + equip_amort_per_month  # margin considers equipment amortization

if pricing_mode == "By Target Margin":
    margin = (margin_pct_input or 0.0) / 100.0
    suggested_price = cost_base_for_margin * (1.0 + margin)
    monthly_gross_profit = suggested_price - cost_base_for_margin
    effective_margin_pct = margin_pct_input
    payback_months = (C_E / monthly_gross_profit) if monthly_gross_profit > 0 else None
else:
    monthly_gross_profit = C_E / payback_target_months
    suggested_price = monthly_cost_ops + monthly_gross_profit
    effective_margin_pct = (monthly_gross_profit / cost_base_for_margin * 100.0) if cost_base_for_margin > 0 else None
    payback_months = payback_target_months

annual_gross_profit = monthly_gross_profit * 12.0
roi_annual = (annual_gross_profit / C_E) if C_E > 0 else None
amort_total=monthly_cost_ops+equip_amort_per_month

st.subheader("Suggested Subscription Pricing")
col_1, col_2 =st.columns(2)
col_1.metric(label="Monthly cost basis (Ops only)", value=f"{monthly_cost_ops:,.2f} {currency}")
col_2.metric(label="Monthly cost basis (With equipment amortization)", value=f"{amort_total:,.2f} {currency}")

if effective_margin_pct is not None:
    st.metric(label="Margin (%)", value=f"{effective_margin_pct:.1f} %")
else:
    st.metric(label="Margin (%)", value="N/A")
if suggested_price>=25:
    st.metric(label="Suggested monthly price", value=f"{suggested_price:,.2f} {currency}", delta=f"+{suggested_price-p_samsara:,.2f}", delta_color="inverse")
    st.caption(f"Comparing with benchmarked price {p_samsara} {currency}")
else:
    st.metric(label="Suggested monthly price", value=f"{suggested_price:,.2f} {currency}", delta=f"{suggested_price-p_samsara:,.2f}", delta_color="normal")
    st.caption(f"Comparing with benchmarked price {p_samsara} {currency}")

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
    st.info("Payback period: N/A (monthly gross profit is 0 or negative). Increase margin or reduce costs.")
else:
    years = payback_months / 12.0
    st.metric(label="Payback (months)", value=f"{payback_months:,.1f}")
    st.caption(f"≈ {years:,.2f} years")

st.subheader("Cost & Price Breakdown (Monthly)")
st.table({
    "Item": [
        "Monthly Fixed Cost",
        "Data (C_d × Q_gb)",
        f"Equipment amort. (C_E ÷ {amort_months} mo)",
        "Total cost base (for margin)",
        "Margin %",
        "Suggested price"
    ],
    "Value": [
        f"{C_p:,.2f} {currency}",
        f"{(C_d*Q_gb):,.2f} {currency}",
        f"{equip_amort_per_month:,.2f} {currency}",
        f"{cost_base_for_margin:,.2f} {currency}",
        f"{effective_margin_pct:.1f} %" if effective_margin_pct is not None else "N/A",
        f"{suggested_price:,.2f} {currency}"
    ]
})

st.caption(
    "Notes: In 'By Target Margin' mode, margin is applied to (Ops cost + equipment amortization). "
    "In 'By Target Payback' mode, price is set so monthly gross profit = C_E ÷ target months, and the shown margin is the effective margin on the same cost base."
)

import streamlit as st

st.set_page_config(page_title="Subscription Price & ROI Calculator", layout="centered")

st.title("Subscription Pricing & ROI Calculator")
st.write("锐明产品市场一部  jcyi@streamax.com")
st.image("streamax_logo.png", width=120)

# =========================
# Sidebar — Common Inputs
# =========================
with st.sidebar:
    st.header("应用模式", help="获取建议订阅费用“Subscription Suggestion”，设定订阅费计算利润用“Profit Calculator”")
    app_mode = st.radio("请选择模式", ["Subscription Suggestion", "Profit Calculator"], index=0)

    st.header("设备参数")
    currency = st.selectbox("Currency", ["USD", "EUR", "CNY", "Other"], index=0)
    C_E_input = st.number_input("Equipment cost (C_E)", min_value=0.0, value=200.0, step=1.0, help="设备DDP成本（未折价前）")
    S_E = 0.0
    
    sale_mode = st.radio("销售策略", ["Free Equipment", "Equipment Sales"], help="当设备售价为0时，即等于Free Equipment")
    if sale_mode == "Free Equipment":
        S_E = 0.0
    else:
        S_E = st.number_input("Equipment Selling Price", min_value=0.0, value=240.0, step=1.0, help="设备售价")

    st.subheader("运营参数")
    C_h = st.number_input("Monthly hosting cost", min_value=0.0, value=1.0, step=0.05, help="运营平台月成本")
    C_c = st.number_input("Monthly capital cost", min_value=0.0, value=0.3, step=0.05, help="贷款利息")
    C_o = st.number_input("Other monthly cost", min_value=0.0, value=0.3, step=0.05, help="其他成本如流量运营商月费等")
    C_d = st.number_input("Data cost per GB per month (C_d)", min_value=0.0, value=4.00, step=0.10, help="每GB价格")
    Q_gb = st.number_input("Monthly data usage (Q_gb, GB)", min_value=0.0, value=3.0, step=0.5)

    st.subheader("锚定参考值")
    p_samsara = st.number_input("Benchmark Subscription Price", min_value=0.0, value=25.00, step=0.5, help="订阅费参考价格, 默认Samsara的25 USD/mo.")
    target_profit = st.number_input("Benchmark Profit (contract horizon)", min_value=0.0, value=56.00, step=0.5, help="合同期总利润的参考值")

# -------------- Shared Derived Values --------------
C_p = C_h + C_c + C_o
monthly_cost_ops = C_p + C_d * Q_gb

C_E_old = C_E_input
C_E_effective = C_E_old - S_E  # 用于是否计入设备月度成本与回本/ROI计算
amort_months_default = 36  # 仅作兜底，实际由模式内输入提供
enable_manual_price = (sale_mode == "Equipment Sales" and S_E > C_E_old)

# 设备一次性利润（售价-成本）
equip_profit_once = S_E - C_E_old

# =========================
# Mode A: Subscription Suggestion
# =========================
if app_mode == "Subscription Suggestion":
    with st.sidebar:
        st.subheader("选择订阅价计算模式")
        pricing_mode = st.radio("Pricing mode", ["By Target Margin", "By Target Payback (months)"], help="建议的订阅价将根据选择的目标回本时间或目标利润率计算得出")
        amort_months = st.number_input("Amortization months (for margin calculation)", min_value=1, value=36, step=1, help="将设备成本月度化。月度值应为订阅合同时长期限。")

        if pricing_mode == "By Target Margin":
            margin_pct_input = st.number_input("Target margin (%)", min_value=0.0, value=30.0, step=1.0, help="期望的margin")
            payback_target_months = None
        else:
            payback_target_months = st.number_input("Target payback period (months)", min_value=1.0, value=18.0, step=1.0, help="期望的回本时间")
            margin_pct_input = None

    # 按设备有效成本决定是否计提月度摊销
    equip_amort_per_month = (C_E_effective / amort_months) if (amort_months > 0 and C_E_effective > 0) else 0.0
    cost_base_for_margin = monthly_cost_ops + equip_amort_per_month

    suggested_price = 0.0
    monthly_gross_profit = 0.0
    effective_margin_pct = None
    payback_months = None
    roi_annual = None

    if sale_mode == "Equipment Sales" and C_E_effective < 0:
        if enable_manual_price:
            st.warning("设备折价后为负成本（C_E - S_E < 0），请划至页面下方手动调试订阅费以查看利润。")
        if pricing_mode == "By Target Payback (months)":
            st.warning("设备折价后为负成本（C_E - S_E < 0），已禁用 “By Target Payback (months)” 模式并自动切换为 “By Target Margin”。")
        pricing_mode = "By Target Margin"

        margin_current = ((S_E - C_E_old) / C_E_old) if C_E_old > 0 else 0.0
        target_margin = (margin_pct_input or 0.0) / 100.0

        if target_margin > margin_current:
            suggested_price = 0.0
            monthly_gross_profit = 0.0
            effective_margin_pct = target_margin * 100.0
            payback_months = None
            amort_total = monthly_cost_ops
            roi_annual = None
        else:
            sub_margin = max(0.0, target_margin - margin_current)
            monthly_gross_profit = sub_margin * monthly_cost_ops
            suggested_price = monthly_cost_ops + monthly_gross_profit
            effective_margin_pct = (sub_margin * 100.0)
            payback_months = None
            amort_total = monthly_cost_ops
            roi_annual = None
    else:
        if pricing_mode == "By Target Margin":
            margin = (margin_pct_input or 0.0) / 100.0
            monthly_gross_profit = margin * cost_base_for_margin
            suggested_price = monthly_cost_ops + monthly_gross_profit
            effective_margin_pct = margin_pct_input
            payback_months = (C_E_effective / monthly_gross_profit) if monthly_gross_profit > 0 and C_E_effective > 0 else None
        else:
            monthly_gross_profit = (C_E_effective / payback_target_months) if C_E_effective > 0 else 0.0
            suggested_price = monthly_cost_ops + monthly_gross_profit
            effective_margin_pct = (monthly_gross_profit / cost_base_for_margin * 100.0) if cost_base_for_margin > 0 else None
            payback_months = payback_target_months if C_E_effective > 0 else None

        amort_total = monthly_cost_ops + equip_amort_per_month
        roi_annual = (monthly_gross_profit * 12.0 / C_E_effective) if C_E_effective > 0 else None

    annual_gross_profit = monthly_gross_profit * 12.0
    if roi_annual is None and C_E_effective > 0:
        roi_annual = (annual_gross_profit / C_E_effective) if C_E_effective > 0 else None

    total_profit = monthly_gross_profit * amort_months + equip_profit_once

    st.subheader("Suggested Subscription Pricing")
    col_1, col_2 = st.columns(2)
    col_1.metric(label="Monthly cost basis (运营+设备月度成本)", value=f"{amort_total:,.2f} {currency}")
    col_1.caption(f"设备月度成本=设备总成本/合同期限={equip_amort_per_month:,.2f} {currency}。仅运营月成本: {monthly_cost_ops:,.2f} {currency}")

    if effective_margin_pct is not None:
        col_2.metric(label="Margin (%)", value=f"{effective_margin_pct:.1f} %")
        col_2.caption("*利润率=月利润/(月运营成本+设备月度成本)")
    else:
        col_2.metric(label="Margin (%)", value="N/A")

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
        c1.caption(f"≈ {years:,.2f} years.")
        c1.caption(f"You earn {amort_months - payback_months:,.2f} mo. of profit")
        c2.metric(
        label=f"Total Profit Earned for a Contract of {amort_months} mo.",
        value=f"{total_profit:,.2f} {currency}",
        delta=f"+{total_profit-target_profit:,.2f}" if total_profit-target_profit>0 else f"{total_profit-target_profit:,.2f}",
        delta_color="normal")
        c2.caption(f"Comparing with benchmarked profit {target_profit:,.2f} {currency}")

     # —— 基准利润校验 & 最低订阅价 —— 
    min_price_for_benchmark = monthly_cost_ops + max(0.0, (target_profit - equip_profit_once) / amort_months)
    meets_benchmark = (total_profit >= target_profit)
    color = "green" if meets_benchmark else "red"
    symbol = "≥" if meets_benchmark else "<"
    #st.markdown(
     #   f"<b>Benchmark Profit Check:</b> "
      #  f"<span style='color:{color}'>{total_profit:,.2f} {currency} {symbol} {target_profit:,.2f} {currency}</span>",
       # unsafe_allow_html=True
    #)
    enough_price = (suggested_price >= min_price_for_benchmark)
    color2 = "green" if enough_price else "red"
    st.markdown(
        f"Minimum subscription price to exceed benchmark profit:{min_price_for_benchmark:,.2f} {currency}",
        unsafe_allow_html=True
    )
    
    # 成本&价格分解
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
            f"{(monthly_cost_ops + equip_amort_per_month):,.2f} {currency}" if C_E_effective > 0 else f"{monthly_cost_ops:,.2f} {currency}",
            f"{effective_margin_pct:.1f} %" if effective_margin_pct is not None else "N/A",
            f"{suggested_price:,.2f} {currency}"
        ]
    })

   

    # 手动订阅费（仅当设备售价>设备成本时启用）- 合并利润率/利润演示
    st.subheader("手动订阅费设置")
    if enable_manual_price:
        manual_sub_price = st.number_input(
            "Set Subscription Price (Manual)",
            min_value=0.0,
            value=float(f"{max(suggested_price, monthly_cost_ops):.2f}"),
            step=0.1,
            help="当设备售价高于设备成本时可手动设定订阅费，用于查看合并利润率与利润。"
        )
    else:
        manual_sub_price = st.number_input(
            "Set Subscription Price (Manual)",
            min_value=0.0,
            value=0.0,
            step=0.1,
            disabled=True,
            help="设备售价未高于设备成本，手动订阅价不可用。"
        )

    combined_margin_pct = None
    equip_margin_pct = None
    sub_margin_pct_manual = None
    equip_profit_once_manual = None
    sub_profit_monthly = None
    sub_profit_annual = None
    total_profit_contract = None

    if enable_manual_price:
        equip_profit_once_manual = equip_profit_once
        equip_margin_pct = ((S_E - C_E_old) / C_E_old * 100.0) if C_E_old > 0 else None
        sub_profit_monthly = manual_sub_price - monthly_cost_ops
        sub_profit_annual = sub_profit_monthly * 12.0
        sub_margin_pct_manual = ((manual_sub_price - monthly_cost_ops) / monthly_cost_ops * 100.0) if monthly_cost_ops > 0 else None
        if (equip_margin_pct is not None) and (sub_margin_pct_manual is not None):
            combined_margin_pct = equip_margin_pct + sub_margin_pct_manual
        total_profit_contract = equip_profit_once_manual + sub_profit_monthly * amort_months

    if enable_manual_price and (combined_margin_pct is not None):
        st.subheader("Combined Margin & Profit")
        cm1, cm2, cm3 = st.columns(3)
        cm1.metric("Equipment margin (%)", value=f"{equip_margin_pct:.1f}%")
        cm2.metric("Subscription margin (%)", value=f"{sub_margin_pct_manual:.1f}%")
        cm3.metric("Combined margin (%)", value=f"{combined_margin_pct:.1f}%")
        st.caption("合并利润率 = 设备销售利润率（相对设备成本） + 订阅利润率（相对运营月成本）。")

        p1, p2, p3 = st.columns(3)
        p1.metric("Equipment profit (one-time)", value=f"{equip_profit_once_manual:,.2f} {currency}")
        p2.metric("Subscription profit / month", value=f"{sub_profit_monthly:,.2f} {currency}")
        p3.metric("Subscription profit / year", value=f"{sub_profit_annual:,.2f} {currency}")
        st.metric(f"Total profit over contract ({amort_months} mo.)", value=f"{total_profit_contract:,.2f} {currency}")

# =========================
# Mode B: Profit Calculator
# =========================
else:
    with st.sidebar:
        amort_months = st.number_input("Amortization months", min_value=1, value=36, step=1, help="用于合同期总利润的计算")
        st.subheader("订阅价设置")
        subscription_price_input = st.number_input("Subscription Price (manual)", min_value=0.0, value=25.0, step=0.1)

    # 在利润计算器模式中：月利润 = 订阅价 - 仅运营月成本（不扣设备月度成本）
    monthly_gross_profit = subscription_price_input - monthly_cost_ops
    annual_gross_profit = monthly_gross_profit * 12.0

    # ROI与回本：只在有效设备成本为正且月利润为正时计算
    roi_annual = (annual_gross_profit / C_E_effective) if (C_E_effective > 0 and annual_gross_profit > 0) else None
    payback_months = (C_E_effective / monthly_gross_profit) if (C_E_effective > 0 and monthly_gross_profit > 0) else None

    # 显示的“Margin (%)”：相对于(运营成本+设备月度摊销)的有效利润率（若设备有效成本<=0，则仅相对运营成本）
    equip_amort_per_month = (C_E_effective / amort_months) if (amort_months > 0 and C_E_effective > 0) else 0.0
    cost_base_for_margin = monthly_cost_ops + (equip_amort_per_month if C_E_effective > 0 else 0.0)
    effective_margin_pct = (monthly_gross_profit / cost_base_for_margin * 100.0) if cost_base_for_margin > 0 else None

    # 合同期总利润（含设备一次性利润 + 订阅在合同期内的利润）
    total_profit_contract = equip_profit_once + monthly_gross_profit * amort_months

    # —— 展示：仅 Profitability / Payback / Margin —— 
    st.subheader("Profitability")
    col1, col2, col3 = st.columns(3)
    col1.metric(label="Monthly gross profit", value=f"{monthly_gross_profit:,.2f} {currency}")
    col2.metric(label="Annual gross profit", value=f"{annual_gross_profit:,.2f} {currency}")
    col3.metric(label="Equipment profit (one-time)", value=f"{equip_profit_once:,.2f} {currency}")

    if effective_margin_pct is not None:
        st.metric(label="Margin (%)", value=f"{effective_margin_pct:.1f}%")
        st.caption("*利润率=月利润 / (月运营成本 + 设备月度成本)")
    else:
        st.metric(label="Margin (%)", value="N/A")

    st.subheader("Payback Period")
    if payback_months is None:
        st.info("Payback period: N/A（设备有效成本≤0或月利润≤0）")
    else:
        years = payback_months / 12.0
        c1, c2 = st.columns(2)
        c1.metric(label="Payback (months)", value=f"{payback_months:,.1f}")
        c1.caption(f"≈ {years:,.2f} years")
        c2.metric(
            label=f"Total Profit over Contract ({amort_months} mo.)",
            value=f"{total_profit_contract:,.2f} {currency}"
        )

    # —— 基准利润校验 & 最低订阅价 —— 
    min_price_for_benchmark = monthly_cost_ops + max(0.0, (target_profit - equip_profit_once) / amort_months)
    meets_benchmark = (total_profit_contract >= target_profit)
    color = "green" if meets_benchmark else "red"
    symbol = "≥" if meets_benchmark else "<"
    st.markdown(
        f"<b>Benchmark Profit Check:</b> "
        f"<b><span style='color:{color}'>{total_profit_contract:,.2f} {currency} <b>{symbol} {target_profit:,.2f} {currency}</span>",
        unsafe_allow_html=True
    )
    below_price = (subscription_price_input >= p_samsara)
    color2 = "green" if below_price else "red"
    st.metric(label="Subscription Price", 
              value=f"{subscription_price_input} {currency}", 
              delta=f"+{subscription_price_input-p_samsara}" if subscription_price_input-p_samsara>0 else f"{subscription_price_input-p_samsara}",
              delta_color="inverse"
             )
    st.caption(f"Comparing with benchmarked price {p_samsara:,.2f} {currency}")
    st.caption(
        f"Minimum subscription price to exceed benchmark profit: {min_price_for_benchmark:,.2f} {currency}",
        unsafe_allow_html=True
    )

st.image("kun.png", width=120)
st.write("PS：这margin的计算方法给我写麻了💔")

import streamlit as st

st.set_page_config(page_title="Subscription Price & ROI Calculator", layout="centered")

st.title("Subscription Pricing & ROI Calculator")

with st.sidebar:
    st.header("Inputs")
    currency = st.selectbox("Currency", ["USD", "EUR", "CNY", "Other"], index=0)
    C_E = st.number_input("Equipment cost (C_E)", min_value=0.0, value=300.0, step=10.0)
    C_p = st.number_input("Platform cost per month (C_p)", min_value=0.0, value=8.0, step=1.0)
    C_d = st.number_input("Data cost per GB per month (C_d)", min_value=0.0, value=0.50, step=0.10, format="%.4f")
    Q_gb = st.number_input("Monthly data usage (Q_gb, GB)", min_value=0.0, value=5.0, step=0.5)
    margin_pct = st.number_input("Target margin (%)", min_value=0.0, value=30.0, step=1.0)

# Core calculations
monthly_cost = C_p + C_d * Q_gb
margin = margin_pct / 100.0
suggested_price = monthly_cost * (1.0 + margin)
monthly_gross_profit = suggested_price - monthly_cost
annual_gross_profit = monthly_gross_profit * 12.0

roi_annual = (annual_gross_profit / C_E) if C_E > 0 else None
payback_months = (C_E / monthly_gross_profit) if monthly_gross_profit > 0 else None

# Display results
st.subheader("Suggested Subscription Pricing")
st.metric(label="Monthly cost basis", value=f"{monthly_cost:,.2f} {currency}")
st.metric(label="Target margin", value=f"{margin_pct:.1f} %")
st.metric(label="Suggested monthly price", value=f"{suggested_price:,.2f} {currency}")

st.subheader("Profitability")
col1, col2, col3 = st.columns(3)
col1.metric(label="Monthly gross profit", value=f"{monthly_gross_profit:,.2f} {currency}")
col2.metric(label="Annual gross profit", value=f"{annual_gross_profit:,.2f} {currency}")
if roi_annual is not None and C_E > 0:
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

# Breakdown table
st.subheader("Cost & Price Breakdown (Monthly)")
st.table({
    "Item": ["Platform (C_p)", "Data (C_d × Q_gb)", "Total cost", "Margin %", "Suggested price"],
    "Value": [f"{C_p:,.2f} {currency}",
              f"{(C_d*Q_gb):,.2f} {currency}",
              f"{monthly_cost:,.2f} {currency}",
              f"{margin_pct:.1f} %",
              f"{suggested_price:,.2f} {currency}"]
})

st.caption("Notes: Price = (C_p + C_d × Q_gb) × (1 + margin%). "
           "Annual ROI is calculated as (12 × monthly gross profit) ÷ C_E. "
           "Payback period is C_E ÷ monthly gross profit (in months).")

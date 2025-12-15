#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import io
import streamlit as st
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt

from calculations import StrategyCalculator
from options_charts import OptionsChartGenerator
from transaction_parser import TransactionAnalyzer


st.set_page_config(page_title="Options Dashboard", layout='wide')

st.title("Options Strategy Dashboard")

with st.sidebar.expander("Strategy Parameters", expanded=True):
    current_price = st.number_input("Underlying Price", value=25990.0, min_value=1.0)
    risk_free_rate = st.number_input("Risk-Free Rate", value=0.2, min_value=0.0, format="%.4f")
    days_to_expiry = st.number_input("Days to Expiry", value=5, min_value=1)
    implied_vol = st.number_input("Implied Volatility", value=0.69, min_value=0.01, format="%.2f")

st.markdown("---")

col1, col2 = st.columns([2, 3])

with col1:
    st.subheader("Positions")

    # Upload transaction file
    uploaded = st.file_uploader("Upload transaction Excel (optional)", type=["xlsx", "xls"])

    positions = []
    if uploaded is not None:
        try:
            df = TransactionAnalyzer.parse_transaction_file(uploaded)
            txs = TransactionAnalyzer.extract_option_transactions(df)
            positions = TransactionAnalyzer.calculate_positions(txs)
            st.success(f"Detected {len(positions)} open positions from file")
        except Exception as e:
            st.error(str(e))

    # Manual position entry
    with st.form(key='add_position'):
        st.write("Add / Edit Position")
        p_type = st.selectbox("Type", ["Call", "Put"], index=0)
        p_position = st.selectbox("Position", ["Long", "Short"], index=0)
        p_strike = st.number_input("Strike", value=26000.0, step=100.0)
        p_qty = st.number_input("Quantity", value=1, min_value=1, step=1)
        p_premium = st.number_input("Premium", value=1500.0, step=100.0)
        add_btn = st.form_submit_button("Add Position")
        if add_btn:
            positions.append({
                'type': p_type,
                'position': p_position.lower(),
                'strike': float(p_strike),
                'quantity': int(p_qty),
                'premium': float(p_premium)
            })

    if positions:
        df_pos = pd.DataFrame(positions)
        st.dataframe(df_pos)
    else:
        st.info("No positions — add manually or upload a transaction file.")

with col2:
    st.subheader("Charts & Analysis")

    if st.button("Calculate Strategy"):
        if not positions:
            st.warning("Add at least one position first.")
        else:
            price_min = current_price * 0.7
            price_max = current_price * 1.3
            S_range = np.linspace(price_min, price_max, 500)

            metrics = StrategyCalculator.calculate_strategy_metrics(
                positions, S_range, current_price, int(days_to_expiry), float(risk_free_rate), float(implied_vol)
            )

            pnl_fig = OptionsChartGenerator.generate_pnl_chart(metrics['price_range'], metrics['pnl'], current_price)
            delta_fig = OptionsChartGenerator.generate_greek_chart(metrics['price_range'], metrics['delta'], current_price, 'Delta', 'g')
            gamma_fig = OptionsChartGenerator.generate_greek_chart(metrics['price_range'], metrics['gamma'], current_price, 'Gamma', 'r')
            theta_fig = OptionsChartGenerator.generate_greek_chart(metrics['price_range'], metrics['theta'], current_price, 'Theta', 'c')
            vega_fig = OptionsChartGenerator.generate_greek_chart(metrics['price_range'], metrics['vega'], current_price, 'Vega', 'm')

            st.subheader('Profit / Loss')
            st.pyplot(pnl_fig)

            cols = st.columns(3)
            with cols[0]:
                st.subheader('Delta')
                st.pyplot(delta_fig)
            with cols[1]:
                st.subheader('Gamma')
                st.pyplot(gamma_fig)
            with cols[2]:
                st.subheader('Theta')
                st.pyplot(theta_fig)

            st.subheader('Vega')
            st.pyplot(vega_fig)

            # Offer downloads for charts
            buf = io.BytesIO()
            pnl_fig.savefig(buf, format='png', bbox_inches='tight')
            buf.seek(0)
            st.download_button('Download P&L PNG', data=buf, file_name='profit_loss.png', mime='image/png')

            st.success('Calculation complete')

    else:
        st.info('Click "Calculate Strategy" to generate charts')

st.markdown("---")
st.caption("Built from the original IRAN_OPTIONS_ANALYZER — web prototype using Streamlit.")

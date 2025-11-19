"""
HSBC Fraud Detection Dashboard - Streamlit
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time

# Config
API_URL = "http://api:8000"

st.set_page_config(
    page_title="HSBC Fraud Detection",
    page_icon="🚨",
    layout="wide"
)

# Title
st.title("🚨 HSBC Fraud Detection Dashboard")
st.markdown("Real-time fraud alerts monitoring")

# Auto-refresh
if st.sidebar.checkbox("Auto-refresh (5s)", value=True):
    time.sleep(5)
    st.rerun()

# ============================================
# METRICS
# ============================================
st.header("📊 Overview")

col1, col2, col3 = st.columns(3)

try:
    # Get stats
    response = requests.get(f"{API_URL}/fraud/stats", timeout=5)
    
    if response.status_code == 200:
        stats = response.json()
        
        with col1:
            st.metric(
                "Total Fraud Alerts",
                f"{stats['total_alerts']:,}",
                delta=None
            )
        
        with col2:
            st.metric(
                "Total Amount",
                f"${stats['total_amount']:,.2f}",
                delta=None
            )
        
        with col3:
            st.metric(
                "Avg Amount",
                f"${stats['avg_amount']:,.2f}",
                delta=None
            )
    else:
        st.error(f"API Error: {response.status_code}")

except Exception as e:
    st.error(f"⚠️ Cannot connect to API: {str(e)}")
    st.stop()

# ============================================
# FRAUD ALERTS TABLE
# ============================================
st.header("🔍 Recent Fraud Alerts")

# Filters
col_filter1, col_filter2 = st.columns(2)

with col_filter1:
    limit_options = ["All", 100, 500, 1000, 5000, 10000, 50000]
    limit_selection = st.selectbox("Show Records", limit_options, index=3)
    limit = None if limit_selection == "All" else limit_selection

with col_filter2:
    category_filter = st.selectbox(
        "Category",
        ["All"] + list(stats.get('by_category', {}).keys())
    )

# Get alerts
try:
    params = {}
    if limit is not None:
        params["limit"] = limit
    if category_filter != "All":
        params["category"] = category_filter
    
    response = requests.get(f"{API_URL}/fraud/alerts", params=params, timeout=30)
    
    if response.status_code == 200:
        alerts = response.json()
        
        if alerts:
            # Convert to DataFrame
            df = pd.DataFrame(alerts)
            
            # Format columns
            df['transaction_time'] = pd.to_datetime(df['transaction_time'])
            df['detected_at'] = pd.to_datetime(df['detected_at'])
            df['amount'] = df['amount'].apply(lambda x: f"${x:,.2f}")
            
            # Display table
            st.dataframe(
                df[[
                    'transaction_id', 'transaction_time', 'amount',
                    'merchant', 'category', 'first', 'last',
                    'state', 'city'
                ]].rename(columns={
                    'transaction_id': 'ID',
                    'transaction_time': 'Time',
                    'amount': 'Amount',
                    'merchant': 'Merchant',
                    'category': 'Category',
                    'first': 'First Name',
                    'last': 'Last Name',
                    'state': 'State',
                    'city': 'City'
                }),
                use_container_width=True,
                hide_index=True
            )
            
            st.success(f"✅ Showing {len(df)} fraud alerts")
        else:
            st.info("No fraud alerts found")
    else:
        st.error(f"API Error: {response.status_code}")

except Exception as e:
    st.error(f"Error: {str(e)}")

# ============================================
# CHARTS
# ============================================
if alerts:
    st.header("📈 Analytics")
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("Fraud by Category")
        
        # Category chart
        category_counts = pd.Series(stats.get('by_category', {})).sort_values(ascending=False)
        
        fig = px.bar(
            x=category_counts.index,
            y=category_counts.values,
            labels={'x': 'Category', 'y': 'Count'},
            title="Fraud Alerts by Category"
        )
        fig.update_traces(marker_color='#FF4B4B')
        st.plotly_chart(fig, use_container_width=True)
    
    with col_chart2:
        st.subheader("Fraud by State")
        
        # State chart
        state_counts = pd.Series(stats.get('by_state', {})).sort_values(ascending=False).head(10)
        
        fig = px.bar(
            x=state_counts.index,
            y=state_counts.values,
            labels={'x': 'State', 'y': 'Count'},
            title="Top 10 States with Fraud"
        )
        fig.update_traces(marker_color='#FFA500')
        st.plotly_chart(fig, use_container_width=True)
    
    # Amount distribution
    st.subheader("Amount Distribution")
    
    df_amounts = pd.DataFrame(alerts)
    
    fig = px.histogram(
        df_amounts,
        x='amount',
        nbins=30,
        title="Distribution of Fraud Transaction Amounts",
        labels={'amount': 'Amount ($)', 'count': 'Frequency'}
    )
    st.plotly_chart(fig, use_container_width=True)

# ============================================
# FOOTER
# ============================================
st.markdown("---")
st.markdown(
    f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
    f"API: {API_URL}"
)

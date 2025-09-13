import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import base64
from io import BytesIO

# Set page configuration
st.set_page_config(
    page_title="Advanced Sales Monitoring Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for data persistence
if 'weekly_data' not in st.session_state:
    st.session_state.weekly_data = {}

if 'current_week' not in st.session_state:
    current_week_id = datetime.now().strftime('%Y-%U')
    st.session_state.current_week = current_week_id
    
    # Initialize current week with empty data
    if current_week_id not in st.session_state.weekly_data:
        st.session_state.weekly_data[current_week_id] = {
            'weekly_target': 50000.0,
            'channel_data': pd.DataFrame({
                'Channel': [
                    'Whatsapp Broadcasting', 'Meta Ads', 'Google Ads', 
                    'Tele Calling', 'Relationship Sales', 
                    'Community Conversion', 'Organic Sales', 'Academic Schools'
                ],
                'Target Percentage': [12.5, 12.5, 12.5, 12.5, 12.5, 12.5, 12.5, 12.5],
                'Weekly Target': [6250.0] * 8,
                'Amount Spent': [0.0] * 8,
                'Actual Sales': [0.0] * 8,
                'Site Visits/Reach': [0] * 8,
                'Calls Made': [0] * 8
            })
        }

# Helper functions
def calculate_metrics(channel_data, weekly_target):
    df = channel_data.copy()
    
    # Calculate ROI safely
    df['ROI'] = 0.0
    for i, row in df.iterrows():
        if row['Amount Spent'] > 0:
            df.at[i, 'ROI'] = (row['Actual Sales'] - row['Amount Spent']) / row['Amount Spent']
    
    # Calculate channel-specific metrics
    df['Conversion Rate'] = 0.0
    for i, row in df.iterrows():
        channel = row['Channel']
        if channel in ['Meta Ads', 'Google Ads']:
            if row['Site Visits/Reach'] > 0:
                df.at[i, 'Conversion Rate'] = (row['Actual Sales'] / row['Site Visits/Reach']) * 100
        elif channel == 'Tele Calling':
            if row['Calls Made'] > 0:
                df.at[i, 'Conversion Rate'] = (row['Actual Sales'] / row['Calls Made']) * 100
        elif channel in ['Relationship Sales', 'Community Conversion', 'Academic Schools']:
            if row['Site Visits/Reach'] > 0:
                df.at[i, 'Conversion Rate'] = (row['Actual Sales'] / row['Site Visits/Reach']) * 100
        elif channel in ['Whatsapp Broadcasting', 'Organic Sales']:
            if weekly_target > 0:
                df.at[i, 'Conversion Rate'] = (row['Actual Sales'] / weekly_target) * 100
    
    return df

def update_weekly_targets(weekly_target, channel_data):
    percentages = channel_data['Target Percentage']
    channel_data['Weekly Target'] = [weekly_target * p / 100 for p in percentages]
    return channel_data

def get_table_download_link(df, filename):
    """Generates a link allowing the data to be downloaded as CSV"""
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}.csv">📥 Download CSV Report</a>'
    return href

# Dashboard layout
st.title("📊 Advanced Sales Channel Monitoring Dashboard")

# Sidebar for navigation
with st.sidebar:
    st.header("Navigation")
    
    # Week selection
    available_weeks = sorted(st.session_state.weekly_data.keys(), reverse=True)
    selected_week = st.selectbox(
        "Select Week",
        options=available_weeks,
        index=0
    )
    
    if selected_week != st.session_state.current_week:
        st.session_state.current_week = selected_week
        st.rerun()
    
    # Add new week
    if st.button("➕ Add New Week"):
        new_week = datetime.now().strftime('%Y-%U')
        if new_week not in st.session_state.weekly_data:
            # Copy the structure from the current week
            current_data = st.session_state.weekly_data[st.session_state.current_week]
            st.session_state.weekly_data[new_week] = {
                'weekly_target': current_data['weekly_target'],
                'channel_data': current_data['channel_data'].copy()
            }
            st.session_state.current_week = new_week
            st.rerun()
    
    st.divider()
    st.header("Configuration")
    
    # Weekly target input
    current_data = st.session_state.weekly_data[st.session_state.current_week]
    new_weekly_target = st.number_input(
        "Total Weekly Sales Target (₹)",
        min_value=0.0,
        value=float(current_data['weekly_target']),
        step=1000.0
    )
    
    if new_weekly_target != current_data['weekly_target']:
        current_data['weekly_target'] = new_weekly_target
        current_data['channel_data'] = update_weekly_targets(new_weekly_target, current_data['channel_data'])
    
    st.subheader("Channel Target Distribution (%)")
    
    # Create input fields for each channel's percentage
    total_percentage = 0
    for i, channel in enumerate(current_data['channel_data']['Channel']):
        current_val = current_data['channel_data'].at[i, 'Target Percentage']
        new_val = st.number_input(
            f"{channel}",
            min_value=0.0,
            max_value=100.0,
            value=float(current_val),
            step=1.0,
            key=f"target_perc_{i}_{st.session_state.current_week}"
        )
        
        if new_val != current_val:
            current_data['channel_data'].at[i, 'Target Percentage'] = new_val
            current_data['channel_data'] = update_weekly_targets(
                current_data['weekly_target'], 
                current_data['channel_data']
            )
        
        total_percentage += new_val
    
    # Check if percentages sum to 100
    if total_percentage != 100:
        st.error(f"Total distribution must equal 100%. Current total: {total_percentage}%")
    
    st.divider()
    st.subheader("Data Management")
    
    if st.button("🔄 Reset Current Week Data"):
        current_data['channel_data']['Amount Spent'] = [0.0] * 8
        current_data['channel_data']['Actual Sales'] = [0.0] * 8
        current_data['channel_data']['Site Visits/Reach'] = [0] * 8
        current_data['channel_data']['Calls Made'] = [0] * 8
        st.success("Current week data has been reset!")
        st.rerun()

# Main dashboard
tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Channel Details", "ROI Analysis", "Weekly Reports"])

with tab1:
    st.header("Sales Performance Overview")
    
    current_data = st.session_state.weekly_data[st.session_state.current_week]
    df = calculate_metrics(current_data['channel_data'], current_data['weekly_target'])
    
    # KPI cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        total_sales = df['Actual Sales'].sum()
        st.metric("Total Actual Sales", f"₹{total_sales:,.2f}")
    with col2:
        total_spent = df['Amount Spent'].sum()
        st.metric("Total Amount Spent", f"₹{total_spent:,.2f}")
    with col3:
        overall_roi = (total_sales - total_spent) / total_spent if total_spent > 0 else 0
        st.metric("Overall ROI", f"{overall_roi:.2%}")
    with col4:
        target_achievement = (total_sales / current_data['weekly_target']) * 100 if current_data['weekly_target'] > 0 else 0
        st.metric("Target Achievement", f"{target_achievement:.1f}%")
    
    # Sales comparison chart
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df['Channel'],
        y=df['Weekly Target'],
        name='Target Sales',
        marker_color='lightblue'
    ))
    fig.add_trace(go.Bar(
        x=df['Channel'],
        y=df['Actual Sales'],
        name='Actual Sales',
        marker_color='lightgreen'
    ))
    fig.update_layout(
        title='Target vs Actual Sales by Channel',
        barmode='group',
        xaxis_tickangle=-45
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # ROI by channel
    fig2 = px.bar(
        df, 
        x='Channel', 
        y='ROI',
        title='ROI by Channel',
        color='ROI',
        color_continuous_scale='RdYlGn'
    )
    fig2.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig2, use_container_width=True)

with tab2:
    st.header("Channel Details and Metrics")
    
    current_data = st.session_state.weekly_data[st.session_state.current_week]
    df = calculate_metrics(current_data['channel_data'], current_data['weekly_target'])
    
    for i, channel in enumerate(df['Channel']):
        with st.expander(f"{channel} Details"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Targets")
                st.metric("Weekly Target", f"₹{df.at[i, 'Weekly Target']:,.2f}")
                st.metric("Target Percentage", f"{df.at[i, 'Target Percentage']}%")
                
                # Channel-specific input fields
                if channel == 'Tele Calling':
                    calls_made = st.number_input(
                        "Calls Made",
                        min_value=0,
                        value=int(df.at[i, 'Calls Made']),
                        step=1,
                        key=f"calls_made_{i}_{st.session_state.current_week}"
                    )
                    if calls_made != df.at[i, 'Calls Made']:
                        current_data['channel_data'].at[i, 'Calls Made'] = calls_made
                else:
                    site_visits = st.number_input(
                        "Site Visits/Reach",
                        min_value=0,
                        value=int(df.at[i, 'Site Visits/Reach']),
                        step=1,
                        key=f"site_visits_{i}_{st.session_state.current_week}"
                    )
                    if site_visits != df.at[i, 'Site Visits/Reach']:
                        current_data['channel_data'].at[i, 'Site Visits/Reach'] = site_visits
            
            with col2:
                st.subheader("Performance")
                amount_spent = st.number_input(
                    "Amount Spent (₹)",
                    min_value=0.0,
                    value=float(df.at[i, 'Amount Spent']),
                    step=100.0,
                    key=f"amount_spent_{i}_{st.session_state.current_week}"
                )
                if amount_spent != df.at[i, 'Amount Spent']:
                    current_data['channel_data'].at[i, 'Amount Spent'] = amount_spent
                
                actual_sales = st.number_input(
                    "Actual Sales (₹)",
                    min_value=0.0,
                    value=float(df.at[i, 'Actual Sales']),
                    step=100.0,
                    key=f"actual_sales_{i}_{st.session_state.current_week}"
                )
                if actual_sales != df.at[i, 'Actual Sales']:
                    current_data['channel_data'].at[i, 'Actual Sales'] = actual_sales
                
                # Display calculated metrics
                st.metric("ROI", f"{df.at[i, 'ROI']:.2%}")
                st.metric("Conversion Rate", f"{df.at[i, 'Conversion Rate']:.2f}%")

with tab3:
    st.header("ROI and Efficiency Analysis")
    
    current_data = st.session_state.weekly_data[st.session_state.current_week]
    df = calculate_metrics(current_data['channel_data'], current_data['weekly_target'])
    
    col1, col2 = st.columns(2)
    
    with col1:
        # ROI comparison
        fig = px.scatter(
            df,
            x='Amount Spent',
            y='Actual Sales',
            size='ROI',
            color='Channel',
            hover_name='Channel',
            title='Spending vs Sales Efficiency'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Conversion rate comparison
        fig = px.bar(
            df,
            x='Channel',
            y='Conversion Rate',
            title='Conversion Rates by Channel',
            color='Conversion Rate',
            color_continuous_scale='Viridis'
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    
    # Detailed ROI table
    st.subheader("Detailed Performance Metrics")
    display_df = df[['Channel', 'Target Percentage', 'Weekly Target', 'Amount Spent', 
                    'Actual Sales', 'ROI', 'Conversion Rate']].copy()
    display_df['ROI'] = display_df['ROI'].apply(lambda x: f"{x:.2%}")
    display_df['Conversion Rate'] = display_df['Conversion Rate'].apply(lambda x: f"{x:.2f}%")
    
    for col in ['Weekly Target', 'Amount Spent', 'Actual Sales']:
        display_df[col] = display_df[col].apply(lambda x: f"₹{x:,.2f}")
    
    st.dataframe(display_df, use_container_width=True)

with tab4:
    st.header("Weekly Reports")
    
    current_data = st.session_state.weekly_data[st.session_state.current_week]
    df = calculate_metrics(current_data['channel_data'], current_data['weekly_target'])
    
    st.subheader(f"Report for Week {st.session_state.current_week}")
    
    total_sales = df['Actual Sales'].sum()
    total_spent = df['Amount Spent'].sum()
    overall_roi = (total_sales - total_spent) / total_spent if total_spent > 0 else 0
    target_achievement = (total_sales / current_data['weekly_target']) * 100 if current_data['weekly_target'] > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Target", f"₹{current_data['weekly_target']:,.2f}")
    with col2:
        st.metric("Total Actual Sales", f"₹{total_sales:,.2f}")
    with col3:
        st.metric("Overall ROI", f"{overall_roi:.2%}")
    with col4:
        st.metric("Target Achievement", f"{target_achievement:.1f}%")
    
    # Historical performance chart (if multiple weeks exist)
    if len(st.session_state.weekly_data) > 1:
        weeks = sorted(st.session_state.weekly_data.keys())
        historical_sales = []
        historical_targets = []
        
        for week in weeks:
            data = st.session_state.weekly_data[week]
            historical_targets.append(data['weekly_target'])
            historical_sales.append(data['channel_data']['Actual Sales'].sum())
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=weeks, 
            y=historical_targets, 
            name='Target',
            line=dict(dash='dash')
        ))
        fig.add_trace(go.Scatter(
            x=weeks, 
            y=historical_sales, 
            name='Actual Sales',
            mode='lines+markers'
        ))
        fig.update_layout(
            title='Historical Performance',
            xaxis_title='Week',
            yaxis_title='Sales (₹)'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Add more weeks to see historical performance trends.")
    
    # Download report
    st.subheader("Download Report")
    
    report_df = pd.DataFrame({
        'Metric': ['Total Target', 'Total Actual Sales', 'Total Amount Spent', 'Overall ROI', 'Target Achievement'],
        'Value': [
            f"₹{current_data['weekly_target']:,.2f}", 
            f"₹{total_sales:,.2f}", 
            f"₹{total_spent:,.2f}", 
            f"{overall_roi:.2%}", 
            f"{target_achievement:.1f}%"
        ]
    })
    
    st.markdown(get_table_download_link(report_df, f"sales_report_{st.session_state.current_week}"), unsafe_allow_html=True)
    
    # Channel performance download
    channel_report_df = df.copy()
    st.markdown(get_table_download_link(channel_report_df, f"channel_performance_{st.session_state.current_week}"), unsafe_allow_html=True)

# Footer
st.divider()
st.caption("Advanced Sales Channel Monitoring Dashboard | Created with Streamlit")
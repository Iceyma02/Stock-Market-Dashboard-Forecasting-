"""
Mining Production Efficiency Dashboard
Copyright 2026 Icey M A
Licensed under Apache License 2.0
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import io
import base64
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
from fpdf import FPDF
import tempfile
import os

# ============================================================================
# CONFIGURATION
# ============================================================================
APP_VERSION = "2.0.0"
APP_NAME = "Mining Production Excellence Dashboard"
COMPANY_NAME = "Global Mining Corporation"

# ============================================================================
# SMART DOWNTIME FORMATTING FUNCTIONS
# ============================================================================
def format_downtime_context(hours):
    """
    Format downtime in the most readable way for mining operations
    Returns a string with appropriate units and context
    """
    if pd.isna(hours) or hours == 0:
        return "0 minutes"
    elif hours < 1:
        minutes = hours * 60
        return f"{minutes:.0f} minutes"
    elif hours < 8:
        return f"{hours:.1f} hours (less than 1 shift)"
    elif hours < 24:
        shifts = hours / 8
        return f"{hours:.0f} hours ({shifts:.1f} shifts)"
    elif hours < 48:
        days = hours / 24
        shifts = hours / 8
        return f"{days:.1f} days ({hours:.0f} hours, {shifts:.0f} shifts)"
    elif hours < 168:  # Less than 1 week
        days = hours / 24
        shifts = hours / 8
        return f"{days:.0f} days ({shifts:.0f} shifts)"
    else:
        weeks = hours / 168
        days = (hours % 168) / 24
        if days > 0:
            return f"{weeks:.0f} weeks, {days:.0f} days ({hours:.0f} hours)"
        else:
            return f"{weeks:.0f} weeks ({hours:.0f} hours)"

def minutes_to_hours(minutes):
    """Convert minutes to hours"""
    return minutes / 60

# ============================================================================
# PDF REPORT GENERATION
# ============================================================================
def generate_pdf_report(prod_df, equip_df, downtime_df, oee, utilization, total_production, cost_per_ton):
    """Generate a professional PDF report"""
    
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 16)
            self.cell(0, 10, f'{COMPANY_NAME} - Production Report', 0, 1, 'C')
            self.set_font('Arial', 'I', 10)
            self.cell(0, 10, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 1, 'C')
            self.ln(10)
        
        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
        
        def chapter_title(self, title):
            self.set_font('Arial', 'B', 12)
            self.set_fill_color(200, 220, 255)
            self.cell(0, 6, title, 0, 1, 'L', 1)
            self.ln(4)
        
        def chapter_body(self, body):
            self.set_font('Arial', '', 11)
            self.multi_cell(0, 5, body)
            self.ln()
        
        def add_metric_row(self, label, value):
            self.set_font('Arial', 'B', 11)
            self.cell(60, 8, label, 0, 0)
            self.set_font('Arial', '', 11)
            self.cell(0, 8, value, 0, 1)
    
    pdf = PDF()
    pdf.add_page()
    
    # Executive Summary
    pdf.chapter_title("EXECUTIVE SUMMARY")
    summary = f"""
    This report provides a comprehensive analysis of mining operations performance.
    Data period covers {prod_df['date'].nunique()} days of production activity.
    """
    pdf.chapter_body(summary)
    
    # Key Metrics
    pdf.chapter_title("KEY PERFORMANCE INDICATORS")
    pdf.add_metric_row("Overall Equipment Effectiveness (OEE):", f"{oee}%")
    pdf.add_metric_row("Equipment Utilization:", f"{utilization}%")
    pdf.add_metric_row("Total Production:", f"{total_production:,.0f} Tons")
    pdf.add_metric_row("Cost per Ton:", f"${cost_per_ton}")
    
    # Production Summary
    pdf.chapter_title("PRODUCTION SUMMARY")
    
    # Material breakdown
    material_data = prod_df.groupby('material_type')['quantity'].sum().reset_index()
    pdf.add_metric_row("Iron Ore:", f"{material_data[material_data['material_type']=='Iron Ore']['quantity'].sum():,.0f} T" if 'Iron Ore' in material_data['material_type'].values else "0 T")
    pdf.add_metric_row("Copper Ore:", f"{material_data[material_data['material_type']=='Copper Ore']['quantity'].sum():,.0f} T" if 'Copper Ore' in material_data['material_type'].values else "0 T")
    pdf.add_metric_row("Coal:", f"{material_data[material_data['material_type']=='Coal']['quantity'].sum():,.0f} T" if 'Coal' in material_data['material_type'].values else "0 T")
    pdf.add_metric_row("Gold Ore:", f"{material_data[material_data['material_type']=='Gold Ore']['quantity'].sum():,.0f} T" if 'Gold Ore' in material_data['material_type'].values else "0 T")
    pdf.add_metric_row("Waste Rock:", f"{material_data[material_data['material_type']=='Waste Rock']['quantity'].sum():,.0f} T" if 'Waste Rock' in material_data['material_type'].values else "0 T")
    
    # Downtime Analysis
    pdf.chapter_title("DOWNTIME ANALYSIS")
    
    if not downtime_df.empty:
        # Convert minutes to hours for the report
        downtime_df['duration_hours'] = downtime_df['duration_minutes'] / 60
        downtime_by_type = downtime_df.groupby('downtime_type')['duration_hours'].sum().reset_index()
        
        total_hours = downtime_by_type['duration_hours'].sum()
        pdf.add_metric_row("Total Downtime:", format_downtime_context(total_hours))
        
        for _, row in downtime_by_type.iterrows():
            pdf.add_metric_row(f"  {row['downtime_type']}:", format_downtime_context(row['duration_hours']))
        
        if 'cost_usd' in downtime_df.columns:
            total_cost = downtime_df['cost_usd'].sum()
            pdf.add_metric_row("Total Downtime Cost:", f"${total_cost:,.0f}")
            if total_hours > 0:
                pdf.add_metric_row("Average Cost/Hour:", f"${total_cost/total_hours:,.0f}")
    else:
        pdf.chapter_body("No downtime data available for the selected period.")
    
    # Equipment Status
    pdf.chapter_title("EQUIPMENT STATUS")
    if not equip_df.empty:
        status_counts = equip_df['status'].value_counts()
        pdf.add_metric_row("Operational:", f"{status_counts.get('Operational', 0)} units")
        pdf.add_metric_row("Maintenance:", f"{status_counts.get('Maintenance', 0)} units")
        pdf.add_metric_row("Idle:", f"{status_counts.get('Idle', 0)} units")
    
    # Footer with disclaimer
    pdf.add_page()
    pdf.chapter_title("DISCLAIMER")
    disclaimer = """
    This report is generated automatically from the Mining Production Efficiency Dashboard.
    Data is based on operational records and may be subject to revisions.
    
    For any questions regarding this report, please contact:
    operations@globalmining.com
    
    CONFIDENTIAL - For internal use only
    """
    pdf.chapter_body(disclaimer)
    
    return pdf

# ============================================================================
# DATA GENERATION - REALISTIC MINING DATA
# ============================================================================
@st.cache_data
def generate_mining_dataset():
    """
    Generate comprehensive mining dataset for 2025
    Returns: production_df, equipment_df, downtime_df
    """
    random.seed(42)
    np.random.seed(42)
    
    # Mining equipment specifications
    EQUIPMENT_SPECS = {
        "Excavator": {"capacity_range": (200, 800), "utilization": 0.75, "fuel_rate": 80},
        "Haul Truck": {"capacity_range": (100, 400), "utilization": 0.80, "fuel_rate": 120},
        "Crusher": {"capacity_range": (300, 1000), "utilization": 0.85, "fuel_rate": 60},
        "Loader": {"capacity_range": (150, 500), "utilization": 0.78, "fuel_rate": 70},
        "Drill Rig": {"capacity_range": (50, 200), "utilization": 0.70, "fuel_rate": 50},
        "Dozer": {"capacity_range": (100, 300), "utilization": 0.65, "fuel_rate": 90},
    }
    
    MATERIALS = ["Iron Ore", "Copper Ore", "Coal", "Gold Ore", "Waste Rock"]
    SITES = ["North Pit", "South Pit", "East Pit", "West Pit", "Processing Plant"]
    OPERATORS = [f"OP-{i:04d}" for i in range(1000, 1100)]
    
    # Generate equipment
    equipment_data = []
    for i in range(1, 31):
        eq_type = random.choice(list(EQUIPMENT_SPECS.keys()))
        specs = EQUIPMENT_SPECS[eq_type]
        
        equipment_data.append({
            'equipment_id': f'EQ-{i:03d}',
            'equipment_name': f'{eq_type} {i}',
            'equipment_type': eq_type,
            'model': random.choice(['CAT 797F', 'Komatsu 830E', 'Hitachi EX3600']),
            'capacity_tph': random.randint(*specs["capacity_range"]),
            'purchase_date': datetime(2020 + random.randint(0, 5), 
                                     random.randint(1, 12), random.randint(1, 28)),
            'last_maintenance': datetime(2025, random.randint(1, 12), random.randint(1, 28)),
            'status': random.choices(['Operational', 'Maintenance', 'Idle'], 
                                    weights=[0.75, 0.15, 0.10])[0],
            'location': random.choice(SITES),
            'fuel_consumption_lph': specs["fuel_rate"],
            'operator_skill': random.choices(['High', 'Medium', 'Low'], 
                                           weights=[0.4, 0.4, 0.2])[0]
        })
    
    df_equipment = pd.DataFrame(equipment_data)
    
    # Generate production data
    production_logs = []
    start_date = datetime(2025, 1, 1)
    end_date = datetime(2025, 12, 31)
    all_dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    for current_date in all_dates:
        for _, eq in df_equipment.iterrows():
            if eq['status'] == 'Maintenance' and random.random() < 0.8:
                continue
                
            utilization = EQUIPMENT_SPECS.get(eq['equipment_type'], {}).get('utilization', 0.7)
            if random.random() > utilization:
                continue
            
            for shift in ['Day', 'Night']:
                num_events = random.randint(3, 8)
                for _ in range(num_events):
                    base_production = eq['capacity_tph'] * random.uniform(0.8, 1.2)
                    
                    # Quality based on operator skill
                    if eq['operator_skill'] == 'High':
                        quality_weights = [0.8, 0.15, 0.05]
                    elif eq['operator_skill'] == 'Medium':
                        quality_weights = [0.5, 0.4, 0.1]
                    else:
                        quality_weights = [0.3, 0.5, 0.2]
                    
                    production_logs.append({
                        'equipment_id': eq['equipment_id'],
                        'timestamp': current_date.replace(hour=random.randint(0, 23)),
                        'date': current_date.date(),
                        'shift': shift,
                        'operator_id': random.choice(OPERATORS),
                        'material_type': random.choice(MATERIALS),
                        'quantity': max(0, np.random.normal(base_production, base_production * 0.1)),
                        'quality_grade': random.choices(['High', 'Medium', 'Low'], 
                                                       weights=quality_weights)[0],
                        'location': eq['location'],
                        'equipment_type': eq['equipment_type']
                    })
    
    df_production = pd.DataFrame(production_logs)
    
    # Generate downtime data with realistic durations
    downtime_events = []
    for _, eq in df_equipment.iterrows():
        # Major downtimes (longer events)
        for _ in range(random.randint(3, 6)):
            downtime_date = start_date + timedelta(days=random.randint(0, 364))
            # Generate realistic durations: some short, some long
            if random.random() < 0.3:  # 30% chance of major event
                duration_minutes = random.randint(1440, 4320)  # 1-3 days
            else:
                duration_minutes = random.randint(120, 720)  # 2-12 hours
                
            downtime_events.append({
                'equipment_id': eq['equipment_id'],
                'start_time': downtime_date.replace(hour=random.randint(0, 23)),
                'duration_minutes': duration_minutes,
                'downtime_type': random.choice(['Mechanical', 'Electrical', 'Hydraulic']),
                'reason': random.choice(['Component Failure', 'System Overload', 'Wear & Tear']),
                'cost_usd': random.randint(5000, 25000)
            })
        
        # Minor downtimes (short events)
        for _ in range(random.randint(10, 20)):
            downtime_date = start_date + timedelta(days=random.randint(0, 364))
            downtime_events.append({
                'equipment_id': eq['equipment_id'],
                'start_time': downtime_date.replace(hour=random.randint(0, 23)),
                'duration_minutes': random.randint(30, 180),
                'downtime_type': random.choice(['Operational', 'Weather', 'Supply Delay']),
                'reason': random.choice(['Operator Error', 'Weather Conditions', 'Waiting for Parts']),
                'cost_usd': random.randint(100, 1000)
            })
    
    df_downtime = pd.DataFrame(downtime_events)
    df_downtime['date'] = pd.to_datetime(df_downtime['start_time']).dt.date
    
    return df_production, df_equipment, df_downtime

# ============================================================================
# KPI CALCULATIONS
# ============================================================================
def calculate_oee(production_df, downtime_df, equipment_df):
    """Calculate Overall Equipment Effectiveness"""
    if production_df.empty:
        return 0.0
    
    days = production_df['date'].nunique()
    planned_minutes = days * 24 * 60
    downtime = downtime_df['duration_minutes'].sum()
    availability = max(0, (planned_minutes - downtime) / planned_minutes)
    
    equipment_capacity = equipment_df.set_index('equipment_id')['capacity_tph'].to_dict()
    production_df['expected_hourly'] = production_df['equipment_id'].map(equipment_capacity)
    total_expected = production_df['expected_hourly'].sum() * 8
    total_actual = production_df['quantity'].sum()
    performance = total_actual / total_expected if total_expected > 0 else 0
    
    quality_map = {'High': 1.0, 'Medium': 0.85, 'Low': 0.6}
    production_df['quality_score'] = production_df['quality_grade'].map(quality_map)
    quality = production_df['quality_score'].mean()
    
    return round(min(availability * performance * quality * 100, 100), 1)

def calculate_utilization(equipment_df, production_df):
    """Calculate equipment utilization rate"""
    if equipment_df.empty:
        return 0.0
    active_equipment = production_df['equipment_id'].nunique()
    return round((active_equipment / len(equipment_df)) * 100, 1)

def calculate_cost_metrics(production_df, downtime_df):
    """Calculate cost per ton and other financial metrics"""
    if production_df.empty:
        return 0.0, 0.0
    
    total_production = production_df['quantity'].sum()
    downtime_cost = downtime_df['cost_usd'].sum() if 'cost_usd' in downtime_df.columns else 0
    operational_cost = total_production * 15  # $15 per ton operational cost
    
    total_cost = downtime_cost + operational_cost
    cost_per_ton = total_cost / total_production if total_production > 0 else 0
    
    return round(cost_per_ton, 2), round(total_cost / 1000, 1)

# ============================================================================
# MAIN APPLICATION
# ============================================================================
def main():
    # Page Configuration
    st.set_page_config(
        page_title=APP_NAME,
        page_icon="⛏️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
    .main-title {
        font-size: 2.8rem;
        background: linear-gradient(90deg, #FF6B00, #FF8C42);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: 800;
    }
    .metric-card {
        background: linear-gradient(135deg, #1a202c 0%, #2d3748 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 6px solid #FF6B00;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: 800;
        margin: 0.5rem 0;
    }
    .metric-label {
        color: #cbd5e0;
        font-size: 1rem;
        margin-bottom: 0.5rem;
    }
    .section-header {
        font-size: 1.8rem;
        color: #4a90e2;
        border-bottom: 3px solid #FF6B00;
        padding-bottom: 0.5rem;
        margin: 2rem 0 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown(f"## 🏭 {COMPANY_NAME}")
        st.markdown(f"**Version:** {APP_VERSION}")
        st.markdown("---")
        
        # Filters
        st.subheader("🔍 Filters")
        
        date_range = st.date_input(
            "Date Range",
            value=(datetime(2025, 1, 1), datetime(2025, 12, 31))
        )
        
        sites = st.multiselect(
            "Sites",
            ["North Pit", "South Pit", "East Pit", "West Pit", "Processing Plant"],
            default=["North Pit", "South Pit"]
        )
        
        equipment_types = st.multiselect(
            "Equipment Types",
            ["Excavator", "Haul Truck", "Crusher", "Loader", "Drill Rig", "Dozer"],
            default=["Excavator", "Haul Truck", "Crusher"]
        )
        
        materials = st.multiselect(
            "Materials",
            ["Iron Ore", "Copper Ore", "Coal", "Gold Ore", "Waste Rock"],
            default=["Iron Ore", "Copper Ore", "Coal"]
        )
        
        st.markdown("---")
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    # Main Content
    st.markdown(f'<h1 class="main-title">{APP_NAME}</h1>', unsafe_allow_html=True)
    
    # Load Data
    df_production, df_equipment, df_downtime = generate_mining_dataset()
    
    # Apply Filters
    start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    
    prod_filtered = df_production[
        (df_production['timestamp'].dt.date >= start_date.date()) &
        (df_production['timestamp'].dt.date <= end_date.date()) &
        (df_production['location'].isin(sites)) &
        (df_production['equipment_type'].isin(equipment_types)) &
        (df_production['material_type'].isin(materials))
    ].copy()
    
    eq_ids = prod_filtered['equipment_id'].unique()
    equip_filtered = df_equipment[df_equipment['equipment_id'].isin(eq_ids)].copy()
    
    # Filter downtime data
    downtime_filtered = df_downtime[
        (pd.to_datetime(df_downtime['start_time']).dt.date >= start_date.date()) &
        (pd.to_datetime(df_downtime['start_time']).dt.date <= end_date.date()) &
        (df_downtime['equipment_id'].isin(eq_ids))
    ].copy()
    
    # Calculate KPIs
    oee = calculate_oee(prod_filtered, downtime_filtered, equip_filtered)
    utilization = calculate_utilization(equip_filtered, prod_filtered)
    total_production = prod_filtered['quantity'].sum()
    avg_daily = total_production / max(1, prod_filtered['date'].nunique())
    cost_per_ton, total_cost_k = calculate_cost_metrics(prod_filtered, downtime_filtered)
    
    # Key Metrics Display
    st.markdown('<div class="section-header">📊 Executive Dashboard</div>', unsafe_allow_html=True)
    
    cols = st.columns(4)
    metrics = [
        ("🏆 OEE", f"{oee}%", "Overall Equipment Effectiveness"),
        ("⛰️ Total Production", f"{total_production:,.0f} T", f"Avg: {avg_daily:,.0f} T/day"),
        ("⚙️ Utilization", f"{utilization}%", "Equipment Active Rate"),
        ("💰 Cost Efficiency", f"${cost_per_ton}/T", f"Total: ${total_cost_k}k")
    ]
    
    for col, (icon, value, label) in zip(cols, metrics):
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{icon} {label.split(':')[0]}</div>
                <div class="metric-value">{value}</div>
                <div style="color: #a0aec0; font-size: 0.9rem;">{label.split(':')[-1] if ':' in label else label}</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Production Analysis
    st.markdown('<div class="section-header">📈 Production Analysis</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # Daily trend
        daily_data = prod_filtered.groupby('date')['quantity'].sum().reset_index()
        fig = px.line(daily_data, x='date', y='quantity',
                      title='Daily Production Trend',
                      labels={'date': 'Date', 'quantity': 'Tons'})
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Material distribution
        material_data = prod_filtered.groupby('material_type')['quantity'].sum().reset_index()
        fig = px.pie(material_data, values='quantity', names='material_type',
                     title='Material Distribution', hole=0.4)
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # Equipment Monitoring
    st.markdown('<div class="section-header">⚙️ Equipment Monitoring</div>', unsafe_allow_html=True)
    
    # Equipment status
    if not equip_filtered.empty:
        status_counts = equip_filtered['status'].value_counts()
        cols = st.columns(len(status_counts))
        
        for col, (status, count) in zip(cols, status_counts.items()):
            with col:
                color = "#38A169" if status == "Operational" else "#D69E2E" if status == "Idle" else "#E53E3E"
                icon = "🟢" if status == "Operational" else "🟡" if status == "Idle" else "🔴"
                st.markdown(f"""
                <div class="metric-card" style="border-left-color: {color}">
                    <div class="metric-label">{icon} {status}</div>
                    <div class="metric-value">{count}</div>
                    <div style="color: #a0aec0;">Equipment Units</div>
                </div>
                """, unsafe_allow_html=True)
    
    # OEE by Equipment Type
    if not prod_filtered.empty:
        oee_by_type = []
        for eq_type in equip_filtered['equipment_type'].unique():
            eq_ids = equip_filtered[equip_filtered['equipment_type'] == eq_type]['equipment_id']
            prod_sub = prod_filtered[prod_filtered['equipment_id'].isin(eq_ids)]
            down_sub = downtime_filtered[downtime_filtered['equipment_id'].isin(eq_ids)]
            oee_val = calculate_oee(prod_sub, down_sub, 
                                  equip_filtered[equip_filtered['equipment_type'] == eq_type])
            oee_by_type.append({'Type': eq_type, 'OEE': oee_val})
        
        oee_df = pd.DataFrame(oee_by_type)
        fig = px.bar(oee_df, x='Type', y='OEE', 
                     title='OEE by Equipment Type',
                     color='OEE', color_continuous_scale='RdYlGn')
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # ============================================================================
    # FIXED DOWNTIME ANALYSIS - WITH HOURS INSTEAD OF MINUTES
    # ============================================================================
    st.markdown('<div class="section-header">🔧 Downtime Analysis</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        if not downtime_filtered.empty:
            # CRITICAL FIX: Convert minutes to hours for display
            downtime_filtered['duration_hours'] = downtime_filtered['duration_minutes'] / 60
            
            # Aggregate by downtime type
            downtime_by_type = downtime_filtered.groupby('downtime_type').agg({
                'duration_hours': 'sum',
                'duration_minutes': 'count',  # Count of events
                'cost_usd': 'sum'
            }).reset_index()
            downtime_by_type.rename(columns={'duration_minutes': 'event_count'}, inplace=True)
            
            # Sort by duration
            downtime_by_type = downtime_by_type.sort_values('duration_hours', ascending=False)
            
            # Calculate additional metrics for tooltips
            downtime_by_type['duration_days'] = downtime_by_type['duration_hours'] / 24
            downtime_by_type['duration_shifts'] = downtime_by_type['duration_hours'] / 8
            downtime_by_type['cost_per_hour'] = downtime_by_type['cost_usd'] / downtime_by_type['duration_hours']
            
            # Create custom hover text with ALL context
            hover_texts = []
            for _, row in downtime_by_type.iterrows():
                hover_text = (
                    f"<b>{row['downtime_type']}</b><br>"
                    f"• Duration: {format_downtime_context(row['duration_hours'])}<br>"
                    f"• Hours: {row['duration_hours']:,.0f}<br>"
                    f"• Days: {row['duration_days']:.1f}<br>"
                    f"• Shifts: {row['duration_shifts']:.0f}<br>"
                    f"• Events: {row['event_count']}<br>"
                    f"• Cost: ${row['cost_usd']:,.0f}<br>"
                    f"• Cost/Hour: ${row['cost_per_hour']:,.0f}"
                )
                hover_texts.append(hover_text)
            
            # Create bar chart with HOURS on y-axis (NOT MINUTES)
            fig_downtime = go.Figure()
            
            fig_downtime.add_trace(go.Bar(
                x=downtime_by_type['downtime_type'],
                y=downtime_by_type['duration_hours'],  # This is in HOURS now
                text=[format_downtime_context(h) for h in downtime_by_type['duration_hours']],
                textposition='outside',
                marker=dict(
                    color=downtime_by_type['duration_hours'],
                    colorscale='Reds',
                    showscale=True,
                    colorbar=dict(title="Hours")
                ),
                hovertext=hover_texts,
                hoverinfo='text',
                name='Downtime'
            ))
            
            total_hours = downtime_by_type['duration_hours'].sum()
            
            fig_downtime.update_layout(
                title=f"⏱️ Downtime by Category - Total: {format_downtime_context(total_hours)}",
                xaxis_title="Downtime Type",
                yaxis_title="Duration (Hours)",  # Explicitly say HOURS
                height=450,
                template="plotly_dark",
                showlegend=False
            )
            
            st.plotly_chart(fig_downtime, use_container_width=True)
            
            # Summary metrics in mining-friendly format
            col_a, col_b, col_c, col_d = st.columns(4)
            with col_a:
                st.metric("Total Downtime", format_downtime_context(total_hours))
            with col_b:
                st.metric("Total Events", f"{downtime_filtered.shape[0]:,}")
            with col_c:
                avg_hours = downtime_filtered['duration_hours'].mean()
                st.metric("Avg Duration", format_downtime_context(avg_hours))
            with col_d:
                max_hours = downtime_filtered['duration_hours'].max()
                st.metric("Longest Event", format_downtime_context(max_hours))
                
        else:
            st.info("No downtime data available")

    with col2:
        if not downtime_filtered.empty and 'cost_usd' in downtime_filtered.columns:
            # Cost analysis
            cost_by_type = downtime_filtered.groupby('downtime_type')['cost_usd'].sum().reset_index()
            cost_by_type = cost_by_type.sort_values('cost_usd', ascending=False)
            
            # Convert to thousands for cleaner display
            cost_by_type['cost_thousands'] = cost_by_type['cost_usd'] / 1000
            total_cost = cost_by_type['cost_usd'].sum()
            
            # Calculate percentage of total
            cost_by_type['cost_percent'] = (cost_by_type['cost_usd'] / total_cost * 100).round(1)
            
            # Create custom hover text for cost chart
            cost_hover_texts = []
            for _, row in cost_by_type.iterrows():
                hover_text = (
                    f"<b>{row['downtime_type']}</b><br>"
                    f"• Total Cost: ${row['cost_usd']:,.0f}<br>"
                    f"• % of Total: {row['cost_percent']}%<br>"
                    f"• Thousands: ${row['cost_thousands']:,.0f}K"
                )
                cost_hover_texts.append(hover_text)
            
            fig_cost = go.Figure()
            
            fig_cost.add_trace(go.Bar(
                x=cost_by_type['downtime_type'],
                y=cost_by_type['cost_thousands'],
                text=['$' + str(int(x)) + 'K' for x in cost_by_type['cost_thousands']],
                textposition='outside',
                marker=dict(
                    color=cost_by_type['cost_thousands'],
                    colorscale='RdYlGn_r',
                    showscale=True,
                    colorbar=dict(title="Thousands $")
                ),
                hovertext=cost_hover_texts,
                hoverinfo='text',
                name='Cost'
            ))
            
            fig_cost.update_layout(
                title=f"💰 Downtime Cost Analysis - Total: ${total_cost/1e6:.1f}M",
                xaxis_title="Downtime Type",
                yaxis_title="Cost (Thousands USD)",
                height=450,
                template="plotly_dark",
                showlegend=False
            )
            
            st.plotly_chart(fig_cost, use_container_width=True)
            
            # Cost efficiency metrics
            col_e, col_f, col_g = st.columns(3)
            with col_e:
                st.metric("Total Cost", f"${total_cost/1e6:.1f}M")
            with col_f:
                if total_hours > 0:
                    avg_cost_per_hour = total_cost / total_hours
                    st.metric("Avg Cost/Hour", f"${avg_cost_per_hour:,.0f}")
                else:
                    st.metric("Avg Cost/Hour", "N/A")
            with col_g:
                most_costly = cost_by_type.iloc[0]['downtime_type']
                st.metric("Most Costly", most_costly)
        else:
            st.info("No cost data available")
    
    # Shift-based downtime analysis
    if not downtime_filtered.empty:
        st.markdown('<div class="section-header">🕒 Shift Impact Analysis</div>', unsafe_allow_html=True)
        
        # Add shift information
        downtime_filtered['hour'] = pd.to_datetime(downtime_filtered['start_time']).dt.hour
        downtime_filtered['shift'] = downtime_filtered['hour'].apply(
            lambda x: 'Night' if (x >= 18 or x < 6) else 'Day'
        )
        
        shift_summary = downtime_filtered.groupby('shift').agg({
            'duration_hours': 'sum',
            'cost_usd': 'sum',
            'duration_minutes': 'count'
        }).reset_index()
        shift_summary.rename(columns={'duration_minutes': 'event_count'}, inplace=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_shift_hours = px.pie(
                shift_summary, 
                values='duration_hours', 
                names='shift',
                title="Downtime Hours by Shift",
                hole=0.4
            )
            fig_shift_hours.update_traces(
                textinfo='label+percent',
                hovertemplate='<b>%{label}</b><br>Hours: %{value:.0f}<br>Percent: %{percent}<extra></extra>'
            )
            st.plotly_chart(fig_shift_hours, use_container_width=True)
        
        with col2:
            fig_shift_cost = px.pie(
                shift_summary, 
                values='cost_usd', 
                names='shift',
                title="Downtime Cost by Shift",
                hole=0.4
            )
            fig_shift_cost.update_traces(
                textinfo='label+percent',
                hovertemplate='<b>%{label}</b><br>Cost: $%{value:,.0f}<br>Percent: %{percent}<extra></extra>'
            )
            st.plotly_chart(fig_shift_cost, use_container_width=True)
    
    # Predictive Maintenance Alerts
    st.markdown('<div class="section-header">🔔 Predictive Alerts</div>', unsafe_allow_html=True)
    
    # Generate alerts based on downtime patterns
    if not downtime_filtered.empty:
        # Find equipment with highest downtime
        top_downtime_equipment = downtime_filtered.groupby('equipment_id').agg({
            'duration_hours': 'sum',
            'duration_minutes': 'count'
        }).reset_index()
        top_downtime_equipment.rename(columns={'duration_minutes': 'event_count'}, inplace=True)
        top_downtime_equipment = top_downtime_equipment.sort_values('duration_hours', ascending=False).head(3)
        
        alerts = []
        for _, eq in top_downtime_equipment.iterrows():
            eq_id = eq['equipment_id']
            eq_info = df_equipment[df_equipment['equipment_id'] == eq_id].iloc[0]
            
            if eq['duration_hours'] > 100:
                severity = "High"
                icon = "🔴"
            elif eq['duration_hours'] > 50:
                severity = "Medium"
                icon = "🟡"
            else:
                severity = "Low"
                icon = "🟢"
            
            alerts.append({
                "equipment": f"{eq_info['equipment_type']} {eq_id}",
                "issue": f"Total downtime: {format_downtime_context(eq['duration_hours'])}",
                "severity": severity,
                "icon": icon
            })
        
        # Add some standard alerts
        standard_alerts = [
            {"equipment": "Excavator EQ-007", "issue": "Engine hours exceed threshold", "severity": "High", "icon": "🔴"},
            {"equipment": "Haul Truck HT-012", "issue": "Brake system degradation", "severity": "High", "icon": "🔴"},
            {"equipment": "Crusher CR-003", "issue": "Bearing vibration increasing", "severity": "Medium", "icon": "🟡"},
        ]
        
        alerts = standard_alerts + alerts
        
        for alert in alerts[:5]:  # Show top 5 alerts
            with st.expander(f"{alert['icon']} {alert['equipment']} - {alert['issue']}"):
                st.write(f"**Severity:** {alert['severity']}")
                st.write("**Action Required:** Schedule maintenance within 48 hours")
                if st.button(f"Create Work Order", key=f"btn_{alert['equipment']}"):
                    st.success(f"Work order created for {alert['equipment']}")
    
    # Data Export
    st.markdown('<div class="section-header">📥 Data Export</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # FIXED PDF REPORT GENERATION
        if st.button("📄 Generate PDF Report", use_container_width=True):
            with st.spinner("Generating PDF report..."):
                try:
                    # Calculate total downtime hours for the report
                    total_downtime_hours = downtime_filtered['duration_hours'].sum() if not downtime_filtered.empty else 0
                    
                    # Generate PDF
                    pdf = generate_pdf_report(
                        prod_filtered, 
                        equip_filtered, 
                        downtime_filtered,
                        oee, 
                        utilization, 
                        total_production, 
                        cost_per_ton
                    )
                    
                    # Save to temporary file
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                        pdf.output(tmp_file.name)
                        tmp_file_path = tmp_file.name
                    
                    # Read the file for download
                    with open(tmp_file_path, 'rb') as f:
                        pdf_data = f.read()
                    
                    # Clean up temp file
                    os.unlink(tmp_file_path)
                    
                    # Create download button
                    st.download_button(
                        label="📥 Download PDF Report",
                        data=pdf_data,
                        file_name=f"mining_report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                    st.success("✅ PDF Report generated successfully!")
                    
                except Exception as e:
                    st.error(f"Error generating PDF: {str(e)}")
                    st.info("Please install fpdf: pip install fpdf")
    
    with col2:
        # Excel Export
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            prod_filtered.to_excel(writer, sheet_name='Production', index=False)
            equip_filtered.to_excel(writer, sheet_name='Equipment', index=False)
            
            # For downtime, convert minutes to hours in Excel as well
            downtime_excel = downtime_filtered.copy()
            if not downtime_excel.empty:
                downtime_excel['duration_hours'] = downtime_excel['duration_minutes'] / 60
                downtime_excel['duration_formatted'] = downtime_excel['duration_hours'].apply(format_downtime_context)
            downtime_excel.to_excel(writer, sheet_name='Downtime', index=False)
            
            # Add summary sheet
            total_downtime_hours = downtime_filtered['duration_hours'].sum() if not downtime_filtered.empty else 0
            summary_data = {
                'Metric': ['OEE', 'Total Production', 'Equipment Utilization', 
                          'Cost per Ton', 'Avg Daily Production', 'Total Downtime'],
                'Value': [f"{oee}%", f"{total_production:,.0f} T", 
                         f"{utilization}%", f"${cost_per_ton}/T",
                         f"{avg_daily:,.0f} T", format_downtime_context(total_downtime_hours)]
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
        
        st.download_button(
            label="📊 Download Excel",
            data=output.getvalue(),
            file_name=f"mining_dashboard_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    
    with col3:
        if st.button("🔄 Refresh Dashboard", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    # Footer
    st.markdown("---")
    total_downtime_hours = downtime_filtered['duration_hours'].sum() if not downtime_filtered.empty else 0
    
    st.markdown(f"""
    <div style="text-align: center; color: #718096; font-size: 0.9rem;">
        <p><strong>{COMPANY_NAME} - Production Excellence System</strong></p>
        <p>Version {APP_VERSION} | Data Period: {date_range[0].strftime('%Y-%m-%d')} to {date_range[1].strftime('%Y-%m-%d')}</p>
        <p>Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Total Downtime: {format_downtime_context(total_downtime_hours)}</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

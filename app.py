# app.py - Main Streamlit Dashboard for Agri-Mind
import streamlit as st
import folium
from streamlit_folium import st_folium
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from config import (
    DEFAULT_LAT, DEFAULT_LON, DEFAULT_ZOOM, CROPS_CONFIG,
    IRRIGATION_TYPES, EGYPT_BOUNDS, THEME_CONFIG, DEMO_MODE
)
from utils.satellite import get_sentinel_client
from utils.indices import SpectralIndices, TimeSeriesAnalysis
from utils.arabic_nlg import ArabicReportGenerator
import requests
import json

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="🌾 Agri-Mind - الزراعة الذكية",
    page_icon="🚜",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "Agri-Mind v1.0 - Precision Agriculture for Egyptian Farmers"}
)

# Custom theme CSS
st.markdown(f"""
<style>
    :root {{
        --primary-color: {THEME_CONFIG['primaryColor']};
        --background-color: {THEME_CONFIG['backgroundColor']};
        --secondary-bg: {THEME_CONFIG['secondaryBackgroundColor']};
        --text-color: {THEME_CONFIG['textColor']};
    }}
    
    .main {{
        background-color: var(--background-color);
        color: var(--text-color);
    }}
    
    .sidebar .sidebar-content {{
        background-color: var(--secondary-bg);
    }}
    
    .metric-card {{
        background: linear-gradient(135deg, #2E7D32 0%, #558B2F 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }}
    
    .status-healthy {{
        background-color: #C8E6C9;
        border-left: 5px solid #00AA00;
    }}
    
    .status-warning {{
        background-color: #FFE0B2;
        border-left: 5px solid #FFAA00;
    }}
    
    .status-critical {{
        background-color: #FFCDD2;
        border-left: 5px solid #FF0000;
    }}
</style>
""", unsafe_allow_html=True)

# ==================== INITIALIZE SESSION STATE ====================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = DEMO_MODE
if "farm_data" not in st.session_state:
    st.session_state.farm_data = {}
if "map_data" not in st.session_state:
    st.session_state.map_data = None

# ==================== SIDEBAR CONFIGURATION ====================
with st.sidebar:
    st.markdown("# ⚙️ التكوين والإعدادات")
    st.markdown("---")
    
    # Mode selection
    mode = st.radio(
        "اختر الوضع:",
        ["🇬🇧 English Mode", "🇪🇬 مزارع (Farmer Mode)"],
        index=1
    )
    
    st.markdown("---")
    
    # Farm Location
    st.subheader("📍 موقع المزرعة")
    
    col1, col2 = st.columns(2)
    with col1:
        latitude = st.number_input(
            "Latitude",
            value=DEFAULT_LAT,
            min_value=EGYPT_BOUNDS["south"],
            max_value=EGYPT_BOUNDS["north"],
            step=0.0001,
            key="lat_input"
        )
    with col2:
        longitude = st.number_input(
            "Longitude",
            value=DEFAULT_LON,
            min_value=EGYPT_BOUNDS["west"],
            max_value=EGYPT_BOUNDS["east"],
            step=0.0001,
            key="lon_input"
        )
    
    # Farm details
    st.markdown("---")
    st.subheader("🌾 معلومات المزرعة")
    
    crop_type = st.selectbox(
        "نوع المحصول:",
        list(CROPS_CONFIG.keys()),
        format_func=lambda x: f"{x} ({CROPS_CONFIG[x]['en_name']})"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        farm_size_feddan = st.number_input(
            "حجم المزرعة (فدان):",
            min_value=0.1,
            value=5.0,
            step=0.5
        )
    with col2:
        farm_size_hectare = st.number_input(
            "أو (هكتار):",
            min_value=0.04,
            value=2.1,
            step=0.1
        )
    
    irrigation_type = st.selectbox(
        "نوع الري:",
        list(IRRIGATION_TYPES.keys()),
        format_func=lambda x: f"{x} ({IRRIGATION_TYPES[x]})"
    )
    
    st.markdown("---")
    st.subheader("🛰️ الأقمار الصناعية")
    
    date_range = st.date_input(
        "اختر نطاق التاريخ:",
        value=(datetime.now() - timedelta(days=30), datetime.now()),
        max_value=datetime.now()
    )
    
    # API Status
    st.markdown("---")
    st.subheader("🔧 حالة الخدمات")
    
    api_status = "✅ Active" if DEMO_MODE else "⚠️ Demo Mode"
    st.metric("Satellite API", api_status)
    
    # Demo mode toggle
    demo_enabled = st.checkbox("استخدم Demo Mode", value=DEMO_MODE)
    
    st.markdown("---")
    st.info("💡 اختر منطقة على الخريطة لتحديث البيانات")

# ==================== MAIN CONTENT ====================
st.markdown("# 🌾 Agri-Mind - المراقبة الذكية للزراعة")
st.markdown("**Precision Agriculture Dashboard for Egyptian Farmers**")

# Top metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "🌱 NDVI",
        "0.68",
        "↑ +0.05",
        delta_color="off"
    )

with col2:
    st.metric(
        "💧 NDWI",
        "-0.12",
        "↑ +0.08",
        delta_color="off"
    )

with col3:
    st.metric(
        "🌡️ Temp",
        "28°C",
        "↑ +2°C",
        delta_color="off"
    )

with col4:
    st.metric(
        "☔ Rainfall",
        "2.3 mm",
        "Next 7d",
        delta_color="off"
    )

st.markdown("---")

# Two-column layout: Map + Analysis
col_map, col_analysis = st.columns([1.5, 1], gap="large")

with col_map:
    st.subheader("📍 خريطة المزرعة التفاعلية")
    
    # Create folium map
    m = folium.Map(
        location=[latitude, longitude],
        zoom_start=DEFAULT_ZOOM,
        tiles="OpenStreetMap"
    )
    
    # Add farm marker
    folium.Marker(
        location=[latitude, longitude],
        popup=f"🚜 {crop_type}<br>مساحة: {farm_size_feddan} فدان",
        tooltip="مزرعتك",
        icon=folium.Icon(color="green", icon="leaf")
    ).add_to(m)
    
    # Add drawing tools
    from folium.plugins import Draw
    Draw(export=True).add_to(m)
    
    # Display map
    map_data = st_folium(m, width=500, height=500)
    
    st.caption("💡 ارسم حدود المزرعة على الخريطة أو اختر نقطة")

with col_analysis:
    st.subheader("📊 تحليل سريع")
    
    # Health status
    st.markdown("#### صحة المحصول")
    health_status = {
        "status": "Healthy",
        "emoji": "✅",
        "ndvi": "0.68",
        "ndwi": "-0.12"
    }
    
    status_class = "status-healthy" if health_status["status"] == "Healthy" else \
                   "status-warning" if health_status["status"] == "Needs Attention" else \
                   "status-critical"
    
    st.markdown(f"""
    <div class="{status_class}" style="padding: 15px; border-radius: 5px;">
        <h3>{health_status['emoji']} {health_status['status']}</h3>
        <p>NDVI: {health_status['ndvi']}</p>
        <p>NDWI: {health_status['ndwi']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Key recommendations
    st.markdown("#### التوصيات الرئيسية")
    st.success("✅ الري: منتظم")
    st.info("ℹ️ السماد: جرعة طبيعية")
    st.warning("⚠️ مراقبة: لا توجد تهديدات حالياً")

st.markdown("---")

# Detailed Analysis Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 التحليل الطيفي",
    "💧 الري والمياه",
    "🥗 السماد والتغذية",
    "🐛 الآفات والأمراض",
    "📊 التقرير الشامل"
])

# ==================== TAB 1: SPECTRAL ANALYSIS ====================
with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 مؤشرات النبات")
        
        indices_data = {
            "Index": ["NDVI", "NDWI", "SAVI", "EVI"],
            "Value": [0.68, -0.12, 0.65, 0.52],
            "Status": ["✅ Healthy", "⚠️ Normal", "✅ Good", "✅ Excellent"]
        }
        
        df_indices = pd.DataFrame(indices_data)
        st.dataframe(df_indices, use_container_width=True, hide_index=True)
    
    with col2:
        st.subheader("📉 رسم بياني للمؤشرات")
        
        fig = go.Figure()
        fig.add_trace(go.Indicator(
            mode="gauge+number+delta",
            value=0.68,
            title={"text": "NDVI"},
            delta={"reference": 0.63},
            gauge={
                "axis": {"range": [-1, 1]},
                "bar": {"color": "#2E7D32"},
                "steps": [
                    {"range": [-1, 0.3], "color": "#FFCDD2"},
                    {"range": [0.3, 0.6], "color": "#FFE0B2"},
                    {"range": [0.6, 1], "color": "#C8E6C9"}
                ]
            }
        ))
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    # Time series comparison
    st.subheader("📈 مقارنة زمنية (30 يوم)")
    
    dates = pd.date_range(end=datetime.now(), periods=30)
    ndvi_values = 0.6 + np.random.normal(0, 0.05, 30).cumsum() * 0.01
    
    fig = px.line(
        x=dates,
        y=ndvi_values,
        labels={"x": "التاريخ", "y": "قيمة NDVI"},
        title="تطور NDVI خلال آخر 30 يوم"
    )
    fig.add_hline(y=0.6, line_dash="dash", line_color="green", annotation_text="Healthy Threshold")
    st.plotly_chart(fig, use_container_width=True)

# ==================== TAB 2: IRRIGATION ====================
with tab2:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💧 احتياجات الري")
        
        water_need_score = 35  # 0-100 scale
        st.metric("درجة احتياج الري:", f"{water_need_score}%", "منخفضة")
        
        st.markdown("#### الملاحظات:")
        st.info(f"""
        • نوع الري: {IRRIGATION_TYPES[irrigation_type]}
        • كفاءة الري: 95%
        • آخر ري: قبل يومين
        • التوصية: ري في الأيام القادمة
        """)
    
    with col2:
        st.subheader("☔ توقعات الطقس")
        
        weather_forecast = {
            "day": ["غداً", "بعد غد", "+3 أيام", "+4 أيام", "+5 أيام"],
            "temp": [28, 30, 32, 29, 26],
            "rain": [0, 0, 5, 0, 10]
        }
        
        df_weather = pd.DataFrame(weather_forecast)
        st.dataframe(df_weather, use_container_width=True, hide_index=True)
    
    # Irrigation schedule
    st.subheader("📅 جدول الري الموصى به")
    
    schedule_data = {
        "التاريخ": ["اليوم", "اليوم + 3", "اليوم + 6", "اليوم + 9"],
        "الكمية (م³/فدان)": [15, 15, 12, 15],
        "الملاحظات": ["أولوية عالية", "عادي", "قد ينخفض حسب الأمطار", "عادي"]
    }
    
    df_schedule = pd.DataFrame(schedule_data)
    st.dataframe(df_schedule, use_container_width=True, hide_index=True)

# ==================== TAB 3: FERTILIZER ====================
with tab3:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🥗 مرحلة النمو الحالية")
        
        growth_stage = st.select_slider(
            "اختر مرحلة النمو:",
            options=["Germination", "Vegetative", "Flowering", "Fruiting", "Maturity"],
            value="Vegetative"
        )
        
        st.metric("صحة المحصول (NDVI):", "0.68", "ممتازة")
    
    with col2:
        st.subheader("📊 توصيات السماد")
        
        fertilizer_types = {
            "النيتروجين (N)": "أساسي ⭐⭐⭐",
            "الفسفور (P)": "جيد ⭐⭐",
            "البوتاسيوم (K)": "جيد ⭐⭐",
            "الكالسيوم (Ca)": "وقائي ⭐"
        }
        
        for nutrient, level in fertilizer_types.items():
            st.write(f"{nutrient}: {level}")
    
    # Detailed fertilizer plan
    st.subheader("📋 خطة التسميد التفصيلية")
    
    fertilizer_plan = {
        "المرحلة": ["البذر", "التفريغ", "الإزهار", "الإثمار"],
        "السماد الموصى": ["NPK 10-10-10", "Urea + معادن", "P + K", "K + Zn"],
        "الكمية/فدان": ["2 كيس", "1.5 كيس", "1 كيس", "0.5 كيس"],
        "المسافة (يوم)": [0, 21, 45, 65]
    }
    
    df_fert = pd.DataFrame(fertilizer_plan)
    st.dataframe(df_fert, use_container_width=True, hide_index=True)

# ==================== TAB 4: PEST MANAGEMENT ====================
with tab4:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🐛 تقييم مخاطر الآفات")
        
        pest_risk_score = 25  # 0-100
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=pest_risk_score,
            title={"text": "درجة المخاطرة"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "#FFB74D"},
                "steps": [
                    {"range": [0, 30], "color": "#C8E6C9"},
                    {"range": [30, 60], "color": "#FFE0B2"},
                    {"range": [60, 100], "color": "#FFCDD2"}
                ]
            }
        ))
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("⚠️ التحذيرات الحالية")
        
        warnings = [
            ("🟢", "Whiteflies", "Low risk", "Continue monitoring"),
            ("🟢", "Spider Mites", "Low risk", "Normal conditions"),
            ("🟡", "Aphids", "Moderate", "Monitor closely")
        ]
        
        for icon, pest, level, action in warnings:
            st.markdown(f"{icon} **{pest}**: {level} - {action}")
    
    # Pest management recommendations
    st.subheader("🛡️ توصيات المكافحة المتكاملة")
    
    recommendations = {
        "الآفة": ["التربس", "العناكب", "الذباب الأبيض"],
        "المكافحة الميكانيكية": ["الري الكثيف", "إزالة الأوراق المصابة", "الشباك الصفراء"],
        "المكافحة البيولوجية": ["الحشرات المفترسة", "العناكب المفترسة", "الطفيليات"],
        "المكافحة الكيميائية": ["عند الضرورة", "Acaricides", "Insecticides"]
    }
    
    df_pest = pd.DataFrame(recommendations)
    st.dataframe(df_pest, use_container_width=True, hide_index=True)

# ==================== TAB 5: COMPREHENSIVE REPORT ====================
with tab5:
    st.subheader("📋 التقرير الشامل للمزرعة")
    
    # Generate Arabic report
    report_gen = ArabicReportGenerator()
    
    health_status = {"status": "Healthy", "description": "الحمد لله المحصول بخير", "emoji": "✅"}
    
    report = report_gen.generate_health_report(health_status, crop_type, farm_size_feddan)
    st.markdown(f"```\n{report}\n```")
    
    # Sustainability metrics
    st.subheader("♻️ مؤشرات الاستدامة")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        water_savings = farm_size_feddan * 15  # m³
        st.metric("💧 توفير المياه", f"{water_savings} م³/موسم", "↓ 35%")
    
    with col2:
        carbon_saved = farm_size_feddan * 0.5  # tonnes CO2
        st.metric("🌍 تقليل الانبعاثات", f"{carbon_saved} طن CO₂", "↓ 40%")
    
    with col3:
        cost_savings = farm_size_feddan * 800  # EGP
        st.metric("💰 توفير التكاليف", f"₤ {cost_savings}", "↓ 30%")
    
    # Export report
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 تحميل التقرير (PDF)", use_container_width=True):
            st.success("✅ جاري تحضير التقرير...")
            st.info("سيتم تحميل التقرير قريباً")
    
    with col2:
        if st.button("📧 إرسال عبر البريد", use_container_width=True):
            st.success("✅ تم إرسال التقرير إلى بريدك")

st.markdown("---")

# Footer
st.markdown("""
---
<div style="text-align: center; color: #2E7D32; padding: 20px;">
    <p><strong>Agri-Mind v1.0</strong> | Built with ❤️ for Egyptian Farmers</p>
    <p>🌾 Precision Agriculture • 🛰️ Satellite Data • 🤖 AI Analysis</p>
    <p style="font-size: 0.9em; color: #666;">For support: support@agri-mind.eg | Demo Mode Enabled</p>
</div>
""", unsafe_allow_html=True)

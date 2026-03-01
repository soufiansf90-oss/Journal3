import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sqlite3

# --- 1. THEME & VISUAL IDENTITY ---
st.set_page_config(page_title="369 ELITE DYNAMIC", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Inter:wght@300;500&display=swap');
    .stApp { background: #05070a; color: #e6edf3; font-family: 'Inter', sans-serif; }
    .main-title { font-family: 'Orbitron'; color: #00ffcc; text-align: center; text-shadow: 0 0 15px #00ffcc; padding: 10px; }
    
    /* Glassmorphism Cards */
    div[data-testid="stMetric"] {
        background: rgba(22, 27, 34, 0.6) !important;
        border: 1px solid #30363d !important;
        border-radius: 12px !important;
        padding: 15px !important;
    }
    
    /* Notion-Style Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #161b22; border: 1px solid #30363d;
        border-radius: 8px 8px 0 0; color: #8b949e; padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] { background-color: #00ffcc !important; color: #000 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE ENGINE ---
conn = sqlite3.connect('dynamic_elite_v19.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS trades 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, pair TEXT, type TEXT, 
              outcome TEXT, pnl REAL, setup TEXT, mindset TEXT, rr REAL, balance REAL)''')
conn.commit()

# --- 3. DYNAMIC LOGIC ---
df = pd.read_sql_query("SELECT * FROM trades", conn)

def get_setups():
    return list(df['setup'].unique()) if not df.empty else []

# --- 4. HEADER ---
st.markdown('<h1 class="main-title">369 TRACKER PRO</h1>', unsafe_allow_html=True)

# --- 5. NAVIGATION ---
tabs = st.tabs(["🎮 TERMINAL", "📆 DAILY LOG", "📊 PERFORMANCE", "📜 JOURNAL", "🧠 NOTION"])

# --- TAB 1: TERMINAL (Dynamic Entry) ---
with tabs[0]:
    col1, col2 = st.columns([1.2, 2])
    with col1:
        st.subheader("🛠️ Log Trade")
        with st.form("entry_form", clear_on_submit=True):
            balance = st.number_input("Starting/Current Balance ($)", value=1000.0)
            date = st.date_input("Date", datetime.now())
            asset = st.text_input("Asset", "NAS100").upper()
            side = st.selectbox("Action", ["LONG", "SHORT"])
            res = st.selectbox("Outcome", ["WIN", "LOSS", "BE"])
            pnl_val = st.number_input("Net P&L ($)", value=0.0)
            rr_val = st.number_input("R:R Ratio", value=1.0)
            
            # Dynamic Setup Choice
            setups = get_setups()
            new_s = st.checkbox("Add New Strategy?")
            setup = st.text_input("Setup Name").upper() if new_s or not setups else st.selectbox("Select Strategy", setups)
            
            mind = st.select_slider("Mindset", ["Focused", "Bored", "Impulsive", "Revenge"])
            
            if st.form_submit_button("LOCK EXECUTION"):
                c.execute("INSERT INTO trades (date, pair, type, outcome, pnl, setup, mindset, rr, balance) VALUES (?,?,?,?,?,?,?,?,?)",
                          (str(date), asset, side, res, pnl_val, setup, mind, rr_val, balance))
                conn.commit()
                st.rerun()

    with col2:
        if not df.empty:
            total_net = df['pnl'].sum()
            current_bal = df['balance'].iloc[-1] + total_net
            st.metric("CURRENT EQUITY", f"${current_bal:,.2f}", f"{total_net:,.2f}$ Total P&L")
            
            # Mini Equity Curve (Always Dynamic)
            df['curve'] = df['balance'].iloc[0] + df['pnl'].cumsum()
            fig_mini = px.line(df, x=df.index, y='curve', template="plotly_dark", title="Live Growth Curve")
            fig_mini.update_traces(line_color='#00ffcc', fill='tozeroy', fillcolor='rgba(0,255,204,0.1)')
            fig_mini.update_layout(height=300, margin=dict(l=0,r=0,t=30,b=0))
            st.plotly_chart(fig_mini, use_container_width=True)

# --- TAB 2: DAILY LOG (TradeZella Dynamic Style) ---
with tabs[1]:
    st.subheader("📆 Daily P&L Breakdown")
    if not df.empty:
        daily = df.groupby('date').agg({'pnl': 'sum', 'id': 'count', 'pair': lambda x: ', '.join(x)}).reset_index()
        daily.columns = ['Date', 'Net P&L', 'Trades', 'Assets']
        
        def color_daily(val):
            if val > 0: return 'background-color: rgba(0, 255, 204, 0.15)'
            if val < 0: return 'background-color: rgba(255, 75, 75, 0.15)'
            return ''
        
        st.table(daily.sort_values('Date', ascending=False).style.applymap(color_daily, subset=['Net P&L']))

# --- TAB 3: PERFORMANCE (Advanced Charts) ---
with tabs[2]:
    if not df.empty:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("PROFIT FACTOR", f"{ (df[df['pnl']>0]['pnl'].sum() / abs(df[df['pnl']<0]['pnl'].sum())) if len(df[df['pnl']<0])>0 else 1:.2f}")
        m2.metric("WIN RATE", f"{(len(df[df['outcome']=='WIN'])/len(df))*100:.1f}%")
        m3.metric("AVG RR", f"{df['rr'].mean():.2f}")
        m4.metric("TOTAL TRADES", len(df))

        c1, c2 = st.columns(2)
        with c1:
            # Zoomable Bar Chart
            st.subheader("📊 Profit/Loss per Execution")
            fig_bar = px.bar(df, x=df.index, y='pnl', color='outcome',
                             color_discrete_map={'WIN':'#00ffcc', 'LOSS':'#ff4b4b', 'BE':'#ffa500'}, template="plotly_dark")
            st.plotly_chart(fig_bar, use_container_width=True)
        with c2:
            st.subheader("🎯 Outcome Split")
            fig_pie = px.pie(df, names='outcome', hole=0.6, color='outcome',
                             color_discrete_map={'WIN':'#00ffcc', 'LOSS':'#ff4b4b', 'BE':'#ffa500'})
            st.plotly_chart(fig_pie, use_container_width=True)

# --- TAB 4: JOURNAL (Custom Dynamic View) ---
with tabs[3]:
    st.subheader("📜 Professional Ledger")
    if not df.empty:
        def style_rows(row):
            color = ''
            if row.outcome == 'WIN': color = 'background-color: rgba(0, 255, 204, 0.05)'
            elif row.outcome == 'LOSS': color = 'background-color: rgba(255, 75, 75, 0.05)'
            elif row.outcome == 'BE': color = 'background-color: rgba(255, 165, 0, 0.05)'
            return [color]*len(row)

        st.dataframe(df.sort_index(ascending=False).style.apply(style_rows, axis=1), use_container_width=True)

# --- TAB 5: NOTION (Collapsible Context) ---
with tabs[4]:
    st.subheader("📓 Notion Workspaces")
    with st.expander("🛠️ Strategy & Confluences"):
        st.write("Edit your strategy rules here...")
        st.checkbox("Wait for sweep")
        st.checkbox("Wait for MSB")

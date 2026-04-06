import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import time
from datetime import datetime

st.set_page_config(page_title="DODO GOLD", layout="wide", initial_sidebar_state="collapsed")

# 1. CSS ULTRA-PREMIUM (Con voz del Dodo)
st.markdown("""
    <style>
    .stApp { background-color: #050505 !important; }
    .gold-header { color: #d4af37 !important; font-size: 42px !important; text-align: center !important; font-family: 'serif' !important; margin-bottom: 5px; }
    
    /* Box de Comandos del Dodo */
    .dodo-command-box {
        background: linear-gradient(90deg, #1a1a1a, #000);
        border: 2px solid #d4af37;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 30px;
        box-shadow: 0px 0px 20px rgba(212, 175, 55, 0.2);
    }
    .command-text { color: #ffffff; font-size: 18px; font-family: 'Inter', sans-serif; font-weight: 600; }
    .dodo-highlight { color: #d4af37; font-weight: 800; text-transform: uppercase; }
    
    .card-pro { background: #111; border: 1px solid #2a2a2a; border-left: 6px solid #d4af37; border-radius: 10px; padding: 15px; margin-bottom: 10px; }
    .sym-pro { color: #d4af37; font-size: 20px; font-weight: 700; }
    .tag-buy { color: #00ff88; border: 1px solid #00ff88; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
    .tag-sell { color: #ff4b4b; border: 1px solid #ff4b4b; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
    
    header, footer { visibility: hidden !important; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<h1 class="gold-header">⚜️ DODO OPERATIONS PRO ⚜️</h1>', unsafe_allow_html=True)

def load_data():
    if os.path.exists("trading_history.csv"):
        try: return pd.read_csv("trading_history.csv", on_bad_lines='skip')
        except: return None
    return None

df = load_data()

if df is not None:
    latest = df.sort_values('timestamp').groupby('symbol').tail(1).sort_values('symbol')
    
    # --- SECCIÓN: DODO COMMAND CENTER (IA SUGGESTIONS) ---
    st.markdown('<div class="dodo-command-box">', unsafe_allow_html=True)
    col_icon, col_txt = st.columns([1, 9])
    
    with col_icon:
        st.write("🦤") # El logo del Dodo
        
    with col_txt:
        # LÓGICA DE SUGERENCIAS
        buys = latest[latest['decision'] == 'BUY']
        sells = latest[latest['decision'] == 'SELL']
        
        if not buys.empty:
            top_buy = buys.iloc[0]['symbol']
            st.markdown(f'<p class="command-text">DODO: <span class="dodo-highlight">¡HAY QUE COMPRAR!</span> El activo <span class="dodo-highlight">{top_buy}</span> está en zona de alta probabilidad.</p>', unsafe_allow_html=True)
        elif not sells.empty:
            top_sell = sells.iloc[0]['symbol']
            st.markdown(f'<p class="command-text">DODO: <span class="dodo-highlight">¡HORA DE VENDER!</span> Liquida posición en <span class="dodo-highlight">{top_sell}</span>, el mercado está saturado.</p>', unsafe_allow_html=True)
        else:
            st.markdown('<p class="command-text">DODO: <span class="dodo-highlight">MERCADO EN CALMA.</span> Futuro incierto en las próximas horas, mantén posición (HOLD) y espera mi señal.</p>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

    # 4. KPIs
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("MONITOR", len(latest))
    c2.metric("ALERTS", len(df[df['decision'] != 'HOLD']))
    c3.metric("ENGINE", "STABLE")
    c4.metric("SHIELD", "ON")

    st.write("---")

    # 5. LAYOUT (CARDS + GRÁFICO)
    col_l, col_r = st.columns([4, 6])

    with col_l:
        st.markdown('<h3 style="color:#d4af37;">MARKET DYNAMICS</h3>', unsafe_allow_html=True)
        for _, row in latest.head(8).iterrows():
            tag = "tag-buy" if row['decision'] == 'BUY' else "tag-sell" if row['decision'] == 'SELL' else "tag-hold"
            st.markdown(f"""
                <div class="card-pro">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div><div class="sym-pro">{row['symbol']}</div><div style="color:white; font-size:18px;">${row['price']:.4f}</div></div>
                        <div style="text-align:right;"><span class="{tag}">{row['decision']}</span><div style="margin-top:8px; color:#d4af37; font-weight:bold;">RSI: {row['rsi']:.1f}</div></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

    with col_r:
        st.markdown('<h3 style="color:#d4af37;">MOMENTUM ENGINE</h3>', unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=latest['symbol'], y=latest['rsi'], mode='lines+markers', line=dict(color='#d4af37', width=3)))
        fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=600)
        st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})

else:
    st.info("Sincronizando flujo institucional...")

time.sleep(10)
st.rerun()
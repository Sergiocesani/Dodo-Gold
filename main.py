import streamlit as st
import pandas as pd
import ccxt
import os
import time
import requests
from datetime import datetime
import plotly.graph_objects as go

# --- CONFIGURACIÓN PERMANENTE ---
TOKEN_TELEGRAM = "8770830913:AAEd7BuVw4cPp0L0ALqf8Gmm3XV9aqVXdlc"
CHAT_ID = "5933435805" 
PORTFOLIO_FILE = "portfolio.csv"

# 1. ESTÉTICA Y PÁGINA
st.set_page_config(page_title="DODO OPS CRYPTO PELUD", layout="wide", initial_sidebar_state="collapsed")

def send_telegram_msg(message):
    try:
        url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
        params = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
        requests.get(url, params=params)
    except: pass

def save_purchase(symbol, price):
    new_entry = pd.DataFrame([{'symbol': symbol, 'buy_price': price, 'time': datetime.now()}])
    if not os.path.exists(PORTFOLIO_FILE):
        new_entry.to_csv(PORTFOLIO_FILE, index=False)
    else:
        pd.concat([pd.read_csv(PORTFOLIO_FILE), new_entry]).to_csv(PORTFOLIO_FILE, index=False)
    st.toast(f"⚜️ DODO OPS: {symbol} registrado", icon="✅")

# 2. MOTOR DE INTELIGENCIA (50 ACTIVOS)
@st.cache_data(ttl=40)
def get_market_data():
    exchange = ccxt.binance({'enableRateLimit': True})
    try:
        markets = exchange.load_markets()
        symbols = [s for s, m in markets.items() if '/USDT' in s and m['active']][:50]
        all_data = []
        
        for symbol in symbols:
            o_1h = exchange.fetch_ohlcv(symbol, timeframe='1h', limit=30)
            df_1h = pd.DataFrame(o_1h, columns=['ts','o','h','l','c','v'])
            o_4h = exchange.fetch_ohlcv(symbol, timeframe='4h', limit=30)
            df_4h = pd.DataFrame(o_4h, columns=['ts','o','h','l','c','v'])
            
            def rsi_calc(df):
                d = df['c'].diff()
                g, l = d.where(d>0,0).rolling(14).mean(), -d.where(d<0,0).rolling(14).mean()
                return 100 - (100 / (1 + (g/l))).iloc[-1]

            r1, r4 = rsi_calc(df_1h), rsi_calc(df_4h)
            price, open_p = df_1h['c'].iloc[-1], df_1h['o'].iloc[-1]
            vol_spike = df_1h['v'].iloc[-1] / df_1h['v'].mean()
            p_change = ((price - open_p) / open_p) * 100
            
            decision = 'HOLD'
            if vol_spike > 3.0 and p_change > 0.5: 
                decision = 'INFLOW 🐳'
                send_telegram_msg(f"⚜️ *DODO OPS:* BALLENA en {symbol} ({vol_spike:.1f}x)")
            elif r1 < 35 and r4 > 40: 
                decision = 'BUY 🚀'
                send_telegram_msg(f"🚀 *DODO BUY:* {symbol} (RSI: {r1:.1f})")
            elif r1 > 70:
                decision = 'SELL 💸'

            all_data.append({'symbol': symbol, 'price': price, 'rsi_1h': r1, 'rsi_4h': r4, 'vol': vol_spike, 'decision': decision})
        return pd.DataFrame(all_data)
    except: return None

# 3. CSS PREMIUM
st.markdown("""
    <style>
    .stApp { background-color: #000; }
    .gold-header { color: #d4af37; text-align: center; font-size: 35px; border-bottom: 2px solid #d4af37; padding-bottom: 10px; margin-bottom: 20px;}
    .trade-card { background: #111; border-left: 5px solid #d4af37; border-radius: 10px; padding: 15px; margin-bottom: 5px; border: 1px solid #222; }
    .stButton>button { background-color: #d4af37 !important; color: black !important; font-weight: bold; width: 100%; height: 30px; font-size: 12px; }
    header, footer { visibility: hidden !important; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<h1 class="gold-header">⚜️ DODO OPS CRYPTO PELUD ⚜️</h1>', unsafe_allow_html=True)

# 4. EJECUCIÓN
df = get_market_data()

if df is not None:
    col_l, col_r = st.columns([1, 1.5])
    
    with col_l:
        st.markdown("<h4 style='color:#d4af37; text-align:center;'>RADAR LIVE (50 ASSETS)</h4>", unsafe_allow_html=True)
        # Mostramos los 50, pero priorizamos alertas arriba
        sorted_df = df.sort_values(by=['decision', 'vol'], ascending=[False, False])
        
        for idx, row in sorted_df.iterrows():
            color = "#00ff88" if "BUY" in row['decision'] or "INFLOW" in row['decision'] else "#ff4b4b" if "SELL" in row['decision'] else "#666"
            with st.container():
                st.markdown(f"""
                    <div class="trade-card">
                        <div style="display:flex; justify-content:space-between;">
                            <b style="color:#d4af37; font-size:16px;">{row['symbol']}</b>
                            <b style="color:{color};">{row['decision']}</b>
                        </div>
                        <div style="color:white; font-size:18px;">${row['price']:.4f}</div>
                        <div style="color:#888; font-size:11px;">VOL: {row['vol']:.1f}x | RSI 1H: {row['rsi_1h']:.1f}</div>
                    </div>
                """, unsafe_allow_html=True)
                st.button(f"REGISTRAR {row['symbol']}", key=f"btn_{row['symbol']}_{idx}", on_click=save_purchase, args=(row['symbol'], row['price']))

    with col_r:
        st.markdown("<h4 style='color:#d4af37; text-align:center;'>MAPA DE MOMENTUM</h4>", unsafe_allow_html=True)
        fig = go.Figure(go.Scatter(
            x=df['symbol'], y=df['rsi_1h'], mode='markers', 
            marker=dict(size=df['vol']*12, color=df['vol'], colorscale='YlOrBr', showscale=True)
        ))
        fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=700)
        st.plotly_chart(fig, use_container_width=True)

# AUTO REFRESH
time.sleep(60); st.rerun()
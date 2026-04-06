import streamlit as st
import pandas as pd
import ccxt
import os
import time
import requests
from datetime import datetime
import plotly.graph_objects as go

# --- CONFIGURACIÓN TELEGRAM ---
TOKEN_TELEGRAM = "8770830913:AAEd7BuVw4cPp0L0ALqf8Gmm3XV9aqVXdlc"
CHAT_ID = "5933435805" 

def send_telegram_msg(message):
    try:
        url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
        params = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
        requests.get(url, params=params)
    except: pass

def save_purchase(symbol, price):
    new_entry = pd.DataFrame([{'symbol': symbol, 'buy_price': price, 'time': datetime.now()}])
    if not os.path.exists("portfolio.csv"):
        new_entry.to_csv("portfolio.csv", index=False)
    else:
        pd.concat([pd.read_csv("portfolio.csv"), new_entry]).to_csv("portfolio.csv", index=False)
    st.toast(f"⚜️ DODO OPS: {symbol} registrado", icon="✅")

# 1. CONFIGURACIÓN DE INTERFAZ
st.set_page_config(page_title="DODO OPS CRYPTO PELUD", layout="wide", initial_sidebar_state="collapsed")

# 2. MOTOR DE ANÁLISIS
@st.cache_data(ttl=60)
def get_advanced_whale_data():
    exchange = ccxt.binance({'enableRateLimit': True})
    try:
        markets = exchange.load_markets()
        symbols = [s for s, m in markets.items() if '/USDT' in s and m['active']]
        watchlist = symbols[:50] 
        all_data = []
        
        # Usamos un spinner para que no veas la pantalla negra
        with st.spinner("🕵️ DODO OPS rastreando ballenas..."):
            for symbol in watchlist:
                o_1h = exchange.fetch_ohlcv(symbol, timeframe='1h', limit=24)
                df_1h = pd.DataFrame(o_1h, columns=['ts','o','h','l','c','v'])
                o_4h = exchange.fetch_ohlcv(symbol, timeframe='4h', limit=24)
                df_4h = pd.DataFrame(o_4h, columns=['ts','o','h','l','c','v'])
                
                def calc_rsi(df):
                    diff = df['c'].diff()
                    g = (diff.where(diff > 0, 0)).rolling(14).mean()
                    l = (-diff.where(diff < 0, 0)).rolling(14).mean()
                    return 100 - (100 / (1 + (g/l))).iloc[-1]

                rsi_1h, rsi_4h = calc_rsi(df_1h), calc_rsi(df_4h)
                price, open_p = df_1h['c'].iloc[-1], df_1h['o'].iloc[-1]
                vol_spike = df_1h['v'].iloc[-1] / df_1h['v'].mean()
                price_change = ((price - open_p) / open_p) * 100
                
                decision = 'HOLD'
                firm = "*DODO OPS CRYPTO PELUD*"
                
                if vol_spike > 2.0 and price_change > 0.5:
                    decision = 'INFLOW'
                    send_telegram_msg(f"⚜️ {firm}\n\n🚨 *INFLOW:* `{symbol}`\n📈 *Vol:* `{vol_spike:.1f}x`\n💰 *Precio:* `${price:.4f}`")
                elif vol_spike > 2.0 and price_change < -0.5:
                    decision = 'OUTFLOW'
                    send_telegram_msg(f"⚜️ {firm}\n\n⚠️ *OUTFLOW:* `{symbol}`\n📉 *Vol:* `{vol_spike:.1f}x`\n💸 *Precio:* `${price:.4f}`")
                elif rsi_1h < 32 and rsi_4h > 40:
                    decision = 'BUY'
                    send_telegram_msg(f"⚜️ {firm}\n\n🚀 *COMPRA:* {symbol}\n📊 *RSI:* {rsi_1h:.1f}")
                
                all_data.append({'symbol': symbol, 'price': price, 'rsi_1h': rsi_1h, 'vol': vol_spike, 'decision': decision})
        return pd.DataFrame(all_data)
    except: return None

# 3. CSS PREMIUM
st.markdown("""
    <style>
    .stApp { background-color: #000; }
    .gold-header { color: #d4af37; text-align: center; font-family: serif; font-size: 38px; border-bottom: 2px solid #d4af37; padding-bottom: 10px; margin-bottom: 20px; }
    .dodo-box { background: linear-gradient(145deg, #0f0f0f, #1a1a1a); border: 1px solid #d4af37; border-radius: 15px; padding: 20px; text-align: center; margin-bottom: 20px; }
    .trade-card { background: #111; border-left: 5px solid #d4af37; border-radius: 10px; padding: 15px; margin-bottom: 10px; border: 1px solid #222; }
    header, footer { visibility: hidden !important; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<h1 class="gold-header">⚜️ DODO OPS CRYPTO PELUD ⚜️</h1>', unsafe_allow_html=True)

df = get_advanced_whale_data()

if df is not None:
    # BOX CENTRAL
    st.markdown('<div class="dodo-box">', unsafe_allow_html=True)
    best = df[df['decision'] != 'HOLD'].head(1)
    if not best.empty:
        st.subheader(f"🦤 ÚLTIMA ALERTA: {best.iloc[0]['symbol']} ({best.iloc[0]['decision']})")
    else:
        st.write("DODO OPS: Esperando movimientos de ballenas...")
    st.markdown('</div>', unsafe_allow_html=True)

    col_l, col_r = st.columns([1, 1.5])
    
    with col_l:
        st.markdown("<h4 style='color:#d4af37; text-align:center;'>RADAR LIVE</h4>", unsafe_allow_html=True)
        display_df = df.sort_values(by=['decision', 'vol'], ascending=[False, False]).head(15)
        
        for idx, row in display_df.iterrows():
            with st.container():
                color = "#00ff88" if row['decision'] in ['BUY', 'INFLOW'] else "#ff4b4b" if row['decision'] == 'OUTFLOW' else "#888"
                st.markdown(f"""
                    <div class="trade-card">
                        <div style="display:flex; justify-content:space-between;">
                            <b style="color:#d4af37; font-size:18px;">{row['symbol']}</b>
                            <b style="color:{color};">{row['decision']}</b>
                        </div>
                        <div style="color:white; font-size:20px;">${row['price']:.4f}</div>
                        <div style="color:#666; font-size:12px;">VOL: {row['vol']:.1f}x | RSI: {row['rsi_1h']:.1f}</div>
                    </div>
                """, unsafe_allow_html=True)
                st.button(f"REGISTRAR {row['symbol']}", key=f"btn_{row['symbol']}_{idx}", on_click=save_purchase, args=(row['symbol'], row['price']))

    with col_r:
        st.markdown("<h4 style='color:#d4af37; text-align:center;'>WHALE MOMENTUM</h4>", unsafe_allow_html=True)
        fig = go.Figure(go.Scatter(x=df['symbol'], y=df['rsi_1h'], mode='markers', 
                                   marker=dict(size=df['vol']*12, color=df['vol'], colorscale='YlOrBr', showscale=True)))
        fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=700)
        st.plotly_chart(fig, use_container_width=True)

time.sleep(60); st.rerun()
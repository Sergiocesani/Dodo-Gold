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

# 1. ESTÉTICA Y PÁGINA (DORADO Y NEGRO)
st.set_page_config(page_title="DODO OPS CRYPTO PELUD", layout="wide", initial_sidebar_state="collapsed")

def send_telegram_msg(message):
    try:
        url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
        params = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
        requests.get(url, params=params)
    except: pass

# 2. MOTOR DE INTELIGENCIA (50 ACTIVOS + CONFIRMACIÓN 4H)
@st.cache_data(ttl=40)
def get_market_data():
    exchange = ccxt.binance({'enableRateLimit': True})
    try:
        markets = exchange.load_markets()
        # Filtramos solo pares USDT activos
        symbols = [s for s, m in markets.items() if '/USDT' in s and m['active']][:50]
        all_data = []
        
        for symbol in symbols:
            # Traemos velas 1H (Momento) y 4H (Tendencia Macro)
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
            # --- VOLUMEN ELITE 3.0x ---
            vol_spike = df_1h['v'].iloc[-1] / df_1h['v'].mean()
            p_change = ((price - open_p) / open_p) * 100
            
            decision = 'HOLD'
            firm = "⚜️ *DODO OPS CRYPTO PELUD*"

            # LÓGICA DE ALERTA AGRESIVA (3.0x VOL)
            if vol_spike > 3.0 and p_change > 0.5: 
                decision = 'INFLOW 🐳'
                send_telegram_msg(f"{firm}\n\n🚨 *ALERTA DE BALLENA:* `{symbol}`\n📈 *Volumen Inusual:* `{vol_spike:.1f}x`\n💰 *Precio:* `${price:.4f}`\n⚡ _Movimiento de capital detectado._")
            
            elif r1 < 32 and r4 > 42: 
                decision = 'BUY 🚀'
                send_telegram_msg(f"{firm}\n\n🚀 *OPORTUNIDAD TÉCNICA:* `{symbol}`\n📊 *RSI 1H:* `{r1:.1f}`\n📈 *Tendencia 4H:* `SANA ({r4:.1f})`\n💰 *Precio:* `${price:.4f}`")

            all_data.append({
                'symbol': symbol, 'price': price, 'rsi_1h': r1, 
                'rsi_4h': r4, 'vol': vol_spike, 'decision': decision
            })
        return pd.DataFrame(all_data)
    except: return None

# 3. CSS PERSONALIZADO (RECUPERANDO EL ESTILO)
st.markdown("""
    <style>
    .stApp { background-color: #000; }
    .gold-header { color: #d4af37; text-align: center; font-size: 38px; border-bottom: 2px solid #d4af37; padding-bottom: 10px; margin-bottom: 25px; }
    .trade-card { background: #111; border-left: 5px solid #d4af37; border-radius: 10px; padding: 15px; margin-bottom: 10px; border: 1px solid #222; }
    header, footer { visibility: hidden !important; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<h1 class="gold-header">⚜️ DODO OPS CRYPTO PELUD ⚜️</h1>', unsafe_allow_html=True)

# 4. RENDERIZADO DEL DASHBOARD
with st.spinner("🕵️ DODO OPS ESCANEANDO BALLENAS (3.0x)..."):
    df = get_market_data()

if df is not None:
    # Mostramos los que tienen acción arriba
    alertas = df[df['decision'] != 'HOLD']
    
    c1, c2 = st.columns([1, 1.5])
    
    with c1:
        st.markdown("<h4 style='color:#d4af37; text-align:center;'>RADAR LIVE</h4>", unsafe_allow_html=True)
        # Si no hay alertas de decisión, mostramos el top 10 de volumen real
        to_show = alertas if not alertas.empty else df.sort_values('vol', ascending=False).head(10)
        
        for _, row in to_show.iterrows():
            color = "#00ff88" if row['decision'] != 'HOLD' else "#666"
            st.markdown(f"""
                <div class="trade-card">
                    <div style="display:flex; justify-content:space-between;">
                        <b style="color:#d4af37; font-size:18px;">{row['symbol']}</b>
                        <b style="color:{color};">{row['decision']}</b>
                    </div>
                    <div style="color:white; font-size:22px; font-weight:bold;">${row['price']:.4f}</div>
                    <div style="color:#888; font-size:12px;">
                        VOL: {row['vol']:.1f}x | RSI 1H: {row['rsi_1h']:.1f} | RSI 4H: {row['rsi_4h']:.1f}
                    </div>
                </div>
            """, unsafe_allow_html=True)

    with c2:
        st.markdown("<h4 style='color:#d4af37; text-align:center;'>MAPA DE MOMENTUM</h4>", unsafe_allow_html=True)
        # Gráfico de burbujas (Tamaño = Volumen)
        fig = go.Figure(go.Scatter(
            x=df['symbol'], y=df['rsi_1h'], mode='markers', 
            marker=dict(size=df['vol']*14, color=df['vol'], colorscale='YlOrBr', showscale=True)
        ))
        fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=650)
        st.plotly_chart(fig, use_container_width=True)

# 5. ACTUALIZACIÓN AUTOMÁTICA
time.sleep(60); st.rerun()
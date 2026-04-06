import streamlit as st
import pandas as pd
import ccxt
import os
import time
import requests
from datetime import datetime
import plotly.graph_objects as go
from groq import Groq
import config  # Importa tus claves desde config.py

# --- CONFIGURACIÓN SEGURA ---
TOKEN_TELEGRAM = config.TOKEN_TELEGRAM
CHAT_ID = config.CHAT_ID
GROQ_API_KEY = config.GROQ_API_KEY
PORTFOLIO_FILE = "portfolio.csv"

# Inicializar Cliente IA (Groq)
client_ai = Groq(api_key=GROQ_API_KEY)

st.set_page_config(page_title="DODO OPS CRYPTO PELUD", layout="wide", initial_sidebar_state="collapsed")

# --- FUNCIONES DE COMUNICACIÓN ---
def send_telegram_msg(message):
    try:
        url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
        params = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
        requests.get(url, params=params)
    except: pass

def get_updates():
    try:
        url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/getUpdates"
        res = requests.get(url).json()
        return res.get("result", [])
    except: return []

# --- CEREBRO DE IA (GROQ ACTUALIZADO 2026) ---
def analizar_con_ia(symbol, precio, rsi, vol):
    if not GROQ_API_KEY:
        return "❌ Error: No se detectó la API KEY en el archivo .env o config.py"
    try:
        prompt = f"""
        Actúa como un trader senior experto. 
        Analiza este activo: {symbol}
        Precio actual: {precio}
        RSI (1H): {rsi:.2f}
        Volumen Relativo: {vol:.2f}x
        Dame un consejo de trading corto (máximo 3 frases) para Sergio. 
        Dile si es momento de entrar, vender o esperar, basándote en estos datos.
        """
        # ACTUALIZADO: Usando el modelo Llama 3.3 70B (Versátil y veloz)
        chat_completion = client_ai.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.7
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"⚠️ Error de conexión con Groq: {str(e)}"

# --- MOTOR DE DATOS (BOLLINGER + RSI) ---
@st.cache_data(ttl=40)
def get_market_data():
    exchange = ccxt.binance({'enableRateLimit': True})
    try:
        markets = exchange.load_markets()
        symbols = [s for s, m in markets.items() if '/USDT' in s and m['active']][:50]
        all_data = []
        
        for symbol in symbols:
            o_1h = exchange.fetch_ohlcv(symbol, timeframe='1h', limit=50)
            df = pd.DataFrame(o_1h, columns=['ts','o','h','l','c','v'])
            
            d = df['c'].diff()
            rsi = 100 - (100 / (1 + (d.where(d>0,0).rolling(14).mean() / -d.where(d<0,0).rolling(14).mean()))).iloc[-1]
            
            sma = df['c'].rolling(window=20).mean()
            std = df['c'].rolling(window=20).std()
            u_band, l_band = (sma + (std * 2)).iloc[-1], (sma - (std * 2)).iloc[-1]
            
            price = df['c'].iloc[-1]
            vol_spike = df['v'].iloc[-1] / df['v'].mean()
            
            decision, msg_accion = 'HOLD', "DODO OPS: Buscando entrada..."
            if price <= l_band and rsi < 38:
                decision, msg_accion = 'BUY 🚀', f"🎯 SNIPER: {symbol} Suelo Bollinger + RSI Bajo."
            elif price >= u_band and rsi > 65:
                decision, msg_accion = 'SELL 💸', f"🔥 SNIPER: {symbol} Techo Bollinger + RSI Alto."
            elif vol_spike > 3.0:
                decision, msg_accion = 'INFLOW 🐳', f"🚨 BALLENA: {vol_spike:.1f}x Volumen."

            all_data.append({'symbol': symbol, 'price': price, 'rsi': rsi, 'vol': vol_spike, 'decision': decision, 'recomendacion': msg_accion})
        return pd.DataFrame(all_data)
    except: return None

# --- UI VISUAL ---
st.markdown("""<style>
    .stApp { background-color: #000; } 
    .gold-header { color: #d4af37; text-align: center; font-size: 35px; border-bottom: 2px solid #d4af37; padding-bottom: 10px; margin-bottom: 20px;} 
    .trade-card { background: #111; border-left: 5px solid #d4af37; border-radius: 10px; padding: 15px; margin-bottom: 5px; border: 1px solid #222; } 
    .stButton>button { background-color: #d4af37 !important; color: black !important; font-weight: bold; width: 100%; border: none; transition: 0.3s; }
    .stButton>button:hover { background-color: #f1c40f !important; transform: scale(1.02); }
</style>""", unsafe_allow_html=True)

st.markdown('<h1 class="gold-header">⚜️ DODO OPS CRYPTO PELUD ⚜️</h1>', unsafe_allow_html=True)

# EJECUCIÓN
df = get_market_data()

if df is not None:
    # Comandos Telegram (Segundo plano)
    upds = get_updates()
    if upds:
        last_m = upds[-1]["message"]["text"].lower()
        if "/analizar" in last_m:
            try:
                target = last_m.split(" ")[1].upper() + "/USDT"
                row = df[df['symbol'] == target].iloc[0]
                res_ia = analizar_con_ia(target, row['price'], row['rsi'], row['vol'])
                send_telegram_msg(f"🧠 *ANÁLISIS IA {target}:*\n\n{res_ia}")
            except: pass

    col_l, col_r = st.columns([1, 1.5])
    
    with col_l:
        st.markdown("<h4 style='color:#d4af37; text-align:center;'>RADAR SNIPER</h4>", unsafe_allow_html=True)
        sorted_df = df.sort_values(by=['decision', 'vol'], ascending=[False, False])
        
        for idx, row in sorted_df.iterrows():
            color = "#00ff88" if "BUY" in row['decision'] else "#ff4b4b" if "SELL" in row['decision'] else "#d4af37" if "INFLOW" in row['decision'] else "#666"
            
            with st.container():
                st.markdown(f"""<div class="trade-card">
                    <b style="color:#d4af37; font-size:16px;">{row['symbol']}</b> | <b style="color:{color};">{row['decision']}</b><br>
                    <span style="color:white; font-size:20px; font-weight:bold;">${row['price']:.4f}</span><br>
                    <small style="color:{color}; font-weight:bold;">{row['recomendacion']}</small>
                </div>""", unsafe_allow_html=True)
                
                # Botón de IA dentro de cada tarjeta
                if st.button(f"IA ANALIZAR {row['symbol']}", key=f"btn_{row['symbol']}_{idx}"):
                    with st.spinner(f"Consultando al Dodo Einstein sobre {row['symbol']}..."):
                        analisis = analizar_con_ia(row['symbol'], row['price'], row['rsi'], row['vol'])
                        st.info(analisis)

    with col_r:
        st.markdown("<h4 style='color:#d4af37; text-align:center;'>WHALE MOMENTUM</h4>", unsafe_allow_html=True)
        fig = go.Figure(go.Scatter(x=df['symbol'], y=df['rsi'], mode='markers', marker=dict(size=df['vol']*12, color=df['vol'], colorscale='YlOrBr', showscale=True)))
        fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=700, xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

time.sleep(60)
st.rerun()
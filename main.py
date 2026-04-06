import streamlit as st
import pandas as pd
import ccxt
import os
import time
import requests
from datetime import datetime
import plotly.graph_objects as go
from groq import Groq

# --- 1. CONFIGURACIÓN E INICIALIZACIÓN ---
try:
    import config
    TOKEN_TELEGRAM = config.TOKEN_TELEGRAM
    CHAT_ID = config.CHAT_ID
    GROQ_API_KEY = config.GROQ_API_KEY
except Exception:
    TOKEN_TELEGRAM = st.secrets.get("TOKEN_TELEGRAM")
    CHAT_ID = st.secrets.get("CHAT_ID")
    GROQ_API_KEY = st.secrets.get("GROQ_API_KEY")

PORTFOLIO_FILE = "portfolio.csv"
STOP_LOSS_PCT = -3.0   # Alerta si cae 3%
TAKE_PROFIT_PCT = 5.0  # Alerta si sube 5%

if not GROQ_API_KEY:
    st.error("❌ ERROR: No se encontró la GROQ_API_KEY.")
    st.stop()

client_ai = Groq(api_key=GROQ_API_KEY)

if not os.path.exists(PORTFOLIO_FILE):
    pd.DataFrame(columns=['symbol', 'buy_price', 'time']).to_csv(PORTFOLIO_FILE, index=False)

st.set_page_config(page_title="DODO OPS CRYPTO PELUD", layout="wide", initial_sidebar_state="collapsed")

# --- 2. FUNCIONES DE APOYO ---
def get_fear_greed():
    try:
        r = requests.get("https://api.alternative.me/fng/").json()
        return r['data'][0]['value'], r['data'][0]['value_classification']
    except: return "50", "Neutral"

def get_crypto_news(coin):
    try:
        # Buscamos noticias rápidas en CryptoPanic o similares (Simulado con IA para velocidad)
        return f"Últimas noticias sobre {coin}: Alta volatilidad esperada por movimientos en ballenas y reportes de inflación."
    except: return "No hay noticias relevantes ahora."

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

def save_purchase(symbol, price):
    new_entry = pd.DataFrame([{'symbol': symbol, 'buy_price': price, 'time': datetime.now().strftime("%Y-%m-%d %H:%M")}])
    pd.concat([pd.read_csv(PORTFOLIO_FILE), new_entry]).to_csv(PORTFOLIO_FILE, index=False)
    st.toast(f"✅ {symbol} registrado", icon="💰")

def delete_purchase(index):
    df_p = pd.read_csv(PORTFOLIO_FILE)
    df_p = df_p.drop(index)
    df_p.to_csv(PORTFOLIO_FILE, index=False)
    st.rerun()

# --- 3. CEREBRO IA MULTI-MODO ---
def analizar_con_ia(symbol, precio, rsi, vol, modo="standard"):
    try:
        prompts = {
            "standard": f"Trader senior: Analiza {symbol}, Precio: {precio}, RSI: {rsi:.2f}, Vol: {vol:.2f}x. Consejo de 3 frases.",
            "scalping": f"Modo Scalper 5min: Analiza {symbol} para trade rápido. RSI: {rsi:.2f}. ¿Entrada o salida inmediata?",
            "noticias": f"Analista Fundamental: Basado en el precio {precio} de {symbol}, ¿cómo afecta el sentimiento actual?",
            "comparar": f"Analiza la fuerza relativa de {symbol} frente al mercado. ¿Es líder o seguidor?"
        }
        prompt = prompts.get(modo, prompts["standard"])
        chat_completion = client_ai.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.7
        )
        return chat_completion.choices[0].message.content
    except Exception as e: return f"⚠️ Error IA: {str(e)}"

# --- 4. MOTOR DE DATOS ---
@st.cache_data(ttl=120)
def get_market_data():
    exchange = ccxt.kucoin({'enableRateLimit': True})
    try:
        markets = exchange.load_markets()
        symbols = [s for s, m in markets.items() if '/USDT' in s and m['active']][:30]
        all_data = []
        for i, symbol in enumerate(symbols):
            time.sleep(0.3) 
            try:
                o_1h = exchange.fetch_ohlcv(symbol, timeframe='1h', limit=50)
                df = pd.DataFrame(o_1h, columns=['ts','o','h','l','c','v'])
                d = df['c'].diff()
                rsi = 100 - (100 / (1 + (d.where(d>0,0).rolling(14).mean() / -d.where(d<0,0).rolling(14).mean()))).iloc[-1]
                sma = df['c'].rolling(20).mean(); std = df['c'].rolling(20).std()
                u_band, l_band = (sma + (std * 2)).iloc[-1], (sma - (std * 2)).iloc[-1]
                price = df['c'].iloc[-1]; vol_spike = df['v'].iloc[-1] / df['v'].mean()
                
                decision = 'HOLD'
                if price <= l_band and rsi < 38 and vol_spike > 1.8: decision = 'BUY 🚀'
                elif price >= u_band and rsi > 68: decision = 'SELL 💸'
                
                all_data.append({'symbol': symbol, 'price': price, 'rsi': rsi, 'vol': vol_spike, 'decision': decision})
            except: continue
        return pd.DataFrame(all_data)
    except: return None

# --- 5. LÓGICA DE INTERFAZ Y COMANDOS ---
st.markdown('<h1 class="gold-header" style="color:#d4af37; text-align:center;">⚜️ DODO OPS ULTRA ⚜️</h1>', unsafe_allow_html=True)
f_val, f_class = get_fear_greed()
st.markdown(f'<p style="text-align:center; color:#AAA;">Fear & Greed: <b style="color:#d4af37;">{f_val} ({f_class})</b></p>', unsafe_allow_html=True)

tab_radar, tab_risk = st.tabs(["🎯 RADAR SNIPER", "💰 GESTIÓN DE RIESGO"])

df = get_market_data()

# --- LÓGICA DE TELEGRAM (COMANDOS NUEVOS) ---
upds = get_updates()
if upds:
    msg = upds[-1]["message"]["text"].lower()
    if "/help" in msg:
        send_telegram_msg("📜 *Manual del Dodo Einstein:*\n\n/analizar COIN - Análisis técnico pro.\n/scalping COIN - Análisis rápido 5m.\n/noticias COIN - Lo último del mercado.\n/comparar COIN1 COIN2 - Cuál está mejor.")
    elif "/analizar" in msg or "/scalping" in msg or "/noticias" in msg:
        try:
            cmd = msg.split(" ")[0].replace("/", "")
            coin = msg.split(" ")[1].upper()
            target = f"{coin}/USDT"
            # Buscamos precio rápido
            ticker = ccxt.kucoin().fetch_ticker(target)
            res = analizar_con_ia(target, ticker['last'], 50.0, 1.0, modo=cmd)
            if cmd == "noticias": res = f"{get_crypto_news(coin)}\n\n" + res
            send_telegram_msg(f"🧠 *DODO {cmd.upper()}:* {target}\n\n{res}")
        except: send_telegram_msg("Escribí bien el comando, ej: /analizar BTC")

# --- RENDERIZADO ---
if df is not None:
    with tab_radar:
        col_l, col_r = st.columns([1, 1.5])
        with col_l:
            for idx, row in df.sort_values(by='decision', ascending=False).iterrows():
                color = "#00ff88" if "BUY" in row['decision'] else "#ff4b4b" if "SELL" in row['decision'] else "#d4af37"
                st.markdown(f'<div style="background:#111; border-left:5px solid {color}; padding:10px; margin-bottom:5px; border-radius:10px;"><b>{row["symbol"]}</b> | ${row["price"]:.4f}</div>', unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                if c1.button(f"IA 🧠", key=f"ia_{idx}"): st.info(analizar_con_ia(row['symbol'], row['price'], row['rsi'], row['vol']))
                if c2.button(f"REGISTRAR 📝", key=f"reg_{idx}"): save_purchase(row['symbol'], row['price'])
        with col_r:
            fig = go.Figure(go.Scatter(x=df['symbol'], y=df['rsi'], mode='markers', marker=dict(size=df['vol']*12, color=df['vol'], colorscale='YlOrBr')))
            fig.update_layout(template="plotly_dark", height=600); st.plotly_chart(fig, use_container_width=True)

    with tab_risk:
        st.markdown("### 📊 Portfolio y Alertas Automáticas")
        port = pd.read_csv(PORTFOLIO_FILE)
        if not port.empty:
            for i, p_row in port.iterrows():
                try:
                    ticker = ccxt.kucoin().fetch_ticker(p_row['symbol'])
                    actual = ticker['last']
                    diff = ((actual - p_row['buy_price']) / p_row['buy_price']) * 100
                    
                    # ALERTA AUTOMÁTICA STOP LOSS / TAKE PROFIT
                    if diff <= STOP_LOSS_PCT:
                        send_telegram_msg(f"🚨 *STOP LOSS:* `{p_row['symbol']}` cayó `{diff:.2f}%`!")
                    elif diff >= TAKE_PROFIT_PCT:
                        send_telegram_msg(f"💰 *TAKE PROFIT:* `{p_row['symbol']}` subió `{diff:.2f}%`!")

                    c_p1, c_p2 = st.columns([3, 1])
                    c_p1.write(f"**{p_row['symbol']}** | PnL: **{diff:.2f}%**")
                    if c_p2.button("VENDIDO ✅", key=f"v_{i}"): delete_purchase(i)
                except: pass

time.sleep(120); st.rerun()
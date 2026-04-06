import streamlit as st
import pandas as pd
import ccxt
import os
import time
import requests
from datetime import datetime
import plotly.graph_objects as go
from groq import Groq

# --- LÓGICA DE CONFIGURACIÓN HÍBRIDA (NUEVA SUMA) ---
# Intentamos importar config.py. Si falla (en la nube), usamos st.secrets.
try:
    import config
    TOKEN_TELEGRAM = config.TOKEN_TELEGRAM
    CHAT_ID = config.CHAT_ID
    GROQ_API_KEY = config.GROQ_API_KEY
except Exception:
    # Esto es lo que usará GitHub/Streamlit Cloud
    TOKEN_TELEGRAM = st.secrets.get("TELEGRAM_TOKEN")
    CHAT_ID = st.secrets.get("TELEGRAM_CHAT_ID")
    GROQ_API_KEY = st.secrets.get("GROQ_API_KEY")

PORTFOLIO_FILE = "portfolio.csv"

# Verificamos que las claves existan para no romper el programa
if not GROQ_API_KEY:
    st.error("❌ ERROR: No se encontró la GROQ_API_KEY. Verificá tus Secrets en Streamlit o tu .env")
    st.stop()

# Inicializar Cliente IA
client_ai = Groq(api_key=GROQ_API_KEY)

# Si el archivo de portfolio no existe, lo creamos (Suma para estabilidad)
if not os.path.exists(PORTFOLIO_FILE):
    pd.DataFrame(columns=['symbol', 'buy_price', 'time']).to_csv(PORTFOLIO_FILE, index=False)

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

# --- GESTIÓN DE ARCHIVOS ---
def save_purchase(symbol, price):
    new_entry = pd.DataFrame([{
        'symbol': symbol, 
        'buy_price': price, 
        'time': datetime.now().strftime("%Y-%m-%d %H:%M")
    }])
    pd.concat([pd.read_csv(PORTFOLIO_FILE), new_entry]).to_csv(PORTFOLIO_FILE, index=False)
    st.toast(f"⚜️ DODO OPS: {symbol} registrado", icon="✅")

# --- CEREBRO DE IA ---
def analizar_con_ia(symbol, precio, rsi, vol):
    try:
        prompt = f"Actúa como trader senior. Analiza {symbol}, Precio: {precio}, RSI: {rsi:.2f}, Vol: {vol:.2f}x. Dame consejo de 3 frases para Sergio."
        chat_completion = client_ai.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.7
        )
        return chat_completion.choices[0].message.content
    except Exception as e: return f"⚠️ Error IA: {str(e)}"

# --- MOTOR DE DATOS (REGLA DE 3) ---
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
            sma = df['c'].rolling(20).mean()
            std = df['c'].rolling(20).std()
            u_band, l_band = (sma + (std * 2)).iloc[-1], (sma - (std * 2)).iloc[-1]
            price = df['c'].iloc[-1]
            vol_spike = df['v'].iloc[-1] / df['v'].mean()
            
            decision, msg_accion = 'HOLD', "Buscando..."
            # REGLA DE 3: Bollinger + RSI + Volumen
            if price <= l_band and rsi < 38 and vol_spike > 1.8:
                decision, msg_accion = 'BUY 🚀', "🎯 SNIPER: CONFLUENCIA DETECTADA"
            elif price >= u_band and rsi > 68:
                decision, msg_accion = 'SELL 💸', "🔥 SNIPER: SOBRECOMPRA"
            elif vol_spike > 3.0:
                decision, msg_accion = 'INFLOW 🐳', f"🚨 BALLENA: {vol_spike:.1f}x"

            all_data.append({'symbol': symbol, 'price': price, 'rsi': rsi, 'vol': vol_spike, 'decision': decision, 'recomendacion': msg_accion})
        return pd.DataFrame(all_data)
    except Exception as e:
        st.error(f"Error Binance: {e}")
        return None

# --- UI VISUAL ---
st.markdown("""<style>
    .stApp { background-color: #000; } 
    .gold-header { color: #d4af37; text-align: center; font-size: 35px; border-bottom: 2px solid #d4af37; padding-bottom: 10px; margin-bottom: 20px;} 
    .trade-card { background: #111; border-left: 5px solid #d4af37; border-radius: 10px; padding: 15px; margin-bottom: 5px; border: 1px solid #222; } 
    .stButton>button { background-color: #d4af37 !important; color: black !important; font-weight: bold; width: 100%; border: none; }
</style>""", unsafe_allow_html=True)

st.markdown('<h1 class="gold-header">⚜️ DODO OPS CRYPTO PELUD ⚜️</h1>', unsafe_allow_html=True)

tab_radar, tab_risk = st.tabs(["🎯 RADAR SNIPER", "💰 GESTIÓN DE RIESGO"])

df = get_market_data()

if df is not None:
    # Alertas automáticas Sniper a Telegram
    for _, alert in df[df['decision'] == 'BUY 🚀'].iterrows():
        send_telegram_msg(f"🎯 *DODO SIGNAL:* `{alert['symbol']}`\n🚀 *COMPRA SNIPER*\n💰 Precio: `${alert['price']}`")

    with tab_radar:
        col_l, col_r = st.columns([1, 1.5])
        with col_l:
            sorted_df = df.sort_values(by=['decision', 'vol'], ascending=[False, False])
            for idx, row in sorted_df.iterrows():
                color = "#00ff88" if "BUY" in row['decision'] else "#ff4b4b" if "SELL" in row['decision'] else "#d4af37"
                st.markdown(f'<div class="trade-card"><b style="color:#d4af37;">{row["symbol"]}</b> | <b style="color:{color};">{row["decision"]}</b><br><span style="color:white; font-size:20px;">${row["price"]:.4f}</span></div>', unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                if c1.button(f"IA 🧠 {row['symbol']}", key=f"ia_{idx}"):
                    st.info(analizar_con_ia(row['symbol'], row['price'], row['rsi'], row['vol']))
                if c2.button(f"REGISTRAR 📝", key=f"reg_{idx}"):
                    save_purchase(row['symbol'], row['price'])
        with col_r:
            fig = go.Figure(go.Scatter(x=df['symbol'], y=df['rsi'], mode='markers', marker=dict(size=df['vol']*12, color=df['vol'], colorscale='YlOrBr')))
            fig.update_layout(template="plotly_dark", height=700)
            st.plotly_chart(fig, use_container_width=True)

    with tab_risk:
        st.markdown("### 📊 Tu Portfolio")
        if os.path.exists(PORTFOLIO_FILE):
            port = pd.read_csv(PORTFOLIO_FILE)
            if not port.empty:
                for i, p_row in port.iterrows():
                    actual = df[df['symbol'] == p_row['symbol']]['price'].values[0]
                    diff = ((actual - p_row['buy_price']) / p_row['buy_price']) * 100
                    st.write(f"**{p_row['symbol']}** | Compra: ${p_row['buy_price']} | Actual: ${actual} | **PnL: {diff:.2f}%**")
            else: st.info("Vacio")

time.sleep(60); st.rerun()
import streamlit as st
import pandas as pd
import ccxt
import os
import time
import requests
import sqlite3
from datetime import datetime
import plotly.graph_objects as go
from groq import Groq
import streamlit.components.v1 as components

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
DB_FILE = "dodo_futures.db"
STOP_LOSS_PCT = -3.0   
TAKE_PROFIT_PCT = 5.0  

if "last_update_id" not in st.session_state: st.session_state.last_update_id = 0
if "selected_coin" not in st.session_state: st.session_state.selected_coin = "BTC"

client_ai = Groq(api_key=GROQ_API_KEY)

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS trades 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, symbol TEXT, type TEXT, leverage INTEGER, 
                  amount REAL, entry_price REAL, status TEXT, timestamp TEXT, pnl REAL, feedback TEXT)''')
    conn.commit()
    conn.close()

init_db()

if not os.path.exists(PORTFOLIO_FILE):
    pd.DataFrame(columns=['symbol', 'buy_price', 'time']).to_csv(PORTFOLIO_FILE, index=False)

st.set_page_config(page_title="DODO TURBO CONTROL", layout="wide", initial_sidebar_state="collapsed")

# --- 2. FUNCIONES DE APOYO ---
def get_fear_greed():
    try:
        r = requests.get("https://api.alternative.me/fng/").json()
        return r['data'][0]['value'], r['data'][0]['value_classification']
    except: return "50", "Neutral"

def send_telegram_msg(message):
    try:
        url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
        params = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
        requests.get(url, params=params)
    except: pass

def get_updates():
    try:
        url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/getUpdates"
        params = {"offset": st.session_state.last_update_id + 1, "timeout": 1}
        res = requests.get(url, params=params).json()
        return res.get("result", [])
    except: return []

def analizar_con_ia(symbol, precio, rsi, vol, modo="standard"):
    try:
        prompts = {
            "standard": f"Trader senior: Analiza {symbol}, Precio: {precio}, RSI: {rsi:.2f}, Vol: {vol:.2f}x. Consejo corto.",
            "scalping": f"Scalper: Analiza {symbol} para trade rápido. RSI: {rsi:.2f}.",
            "noticias": f"Analista: Impacto de datos actuales en {symbol}.",
            "futuros": f"Coach: Operación en {symbol} CERRADA. PnL: {vol}%. Analiza técnica y psicología.",
            "liquidacion": f"URGENTE: Sergio fue LIQUIDADO en {symbol} con {vol}x. Sermón sobre gestión de riesgo."
        }
        prompt = prompts.get(modo, prompts["standard"])
        chat_completion = client_ai.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.7
        )
        return chat_completion.choices[0].message.content
    except: return "IA recalculando..."

# --- 3. COMPONENTE TRADINGVIEW (BINANCE STYLE) ---
def render_tradingview(symbol):
    tv_symbol = f"BINANCE:{symbol}USDT"
    components.html(
        f"""
        <div id="tradingview_chart" style="height:500px;"></div>
        <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
        <script type="text/javascript">
        new TradingView.widget({{
          "width": "100%", "height": 500, "symbol": "{tv_symbol}",
          "interval": "60", "timezone": "Etc/UTC", "theme": "dark",
          "style": "1", "locale": "es", "toolbar_bg": "#f1f3f6",
          "enable_publishing": false, "hide_side_toolbar": false,
          "allow_symbol_change": true, "container_id": "tradingview_chart"
        }});
        </script>
        """, height=510,
    )

# --- 4. MOTOR DE DATOS ---
@st.cache_data(ttl=120)
def get_market_data():
    exchange = ccxt.kucoin({'enableRateLimit': True})
    try:
        markets = exchange.load_markets()
        symbols = [s for s, m in markets.items() if '/USDT' in s and m['active']][:30]
        all_data = []
        for symbol in symbols:
            time.sleep(0.3) 
            try:
                o_1h = exchange.fetch_ohlcv(symbol, timeframe='1h', limit=50)
                df = pd.DataFrame(o_1h, columns=['ts','o','h','l','c','v'])
                d = df['c'].diff()
                rsi = 100 - (100 / (1 + (d.where(d>0,0).rolling(14).mean() / -d.where(d<0,0).rolling(14).mean()))).iloc[-1]
                sma = df['c'].rolling(20).mean(); std = df['c'].rolling(20).std()
                u_band, l_band = (sma + (std * 2)).iloc[-1], (sma - (std * 2)).iloc[-1]
                price = df['c'].iloc[-1]; vol_spike = df['v'].iloc[-1] / df['v'].mean()
                dec = 'HOLD'
                if vol_spike > 3.0 and rsi < 60: dec = '🐳 WHALE IN'
                elif price <= l_band and rsi < 38: dec = 'BUY 🚀'
                elif price >= u_band and rsi > 68: dec = 'SELL 💸'
                all_data.append({'symbol': symbol.replace('/USDT',''), 'price': price, 'rsi': rsi, 'vol': vol_spike, 'decision': dec})
            except: continue
        return pd.DataFrame(all_data)
    except: return None

# --- 5. CSS TURBO CONTROL ---
st.markdown("""
<style>
    .stApp { background-color: #0b0e11; }
    .gold-header { color: #f0b90b; text-align: center; font-size: 35px; border-bottom: 2px solid #f0b90b; padding-bottom: 10px; margin-bottom: 15px;} 
    .trade-card { background: #161b22; border-left: 5px solid #f0b90b; border-radius: 10px; padding: 15px; margin-bottom: 5px; border: 1px solid #30363d; } 
    .stButton>button { background-color: #f0b90b !important; color: black !important; font-weight: bold; width: 100%; border: none; }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="gold-header">⚜️ DODO TURBO TERMINAL ⚜️</h1>', unsafe_allow_html=True)

f_val, f_class = get_fear_greed()
st.markdown(f'<p style="text-align:center; color:#AAA;">Sentimiento: <b style="color:#f0b90b;">{f_val} ({f_class})</b></p>', unsafe_allow_html=True)

df_market = get_market_data()
tab_terminal, tab_futures, tab_risk = st.tabs(["📊 TERMINAL", "⚔️ FUTUROS SIM", "💰 RIESGO"])

with tab_terminal:
    col_nav, col_main = st.columns([1, 3])
    with col_nav:
        st.markdown("### 🔍 Buscador")
        search = st.text_input("Moneda", placeholder="BTC, ETH, RUNE...", key="main_search").upper()
        if search: st.session_state.selected_coin = search
        st.markdown("---")
        if df_market is not None:
            for i, r in df_market.sort_values(by='vol', ascending=False).iterrows():
                if st.button(f"{r['symbol']} | {r['decision']}", key=f"btn_{r['symbol']}", use_container_width=True):
                    st.session_state.selected_coin = r['symbol']
    with col_main:
        st.markdown(f"### 📈 {st.session_state.selected_coin}/USDT")
        render_tradingview(st.session_state.selected_coin)
        # Probabilidades IA
        if st.button("🧠 ANALIZAR PROBABILIDADES"):
            ticker = ccxt.kucoin().fetch_ticker(f"{st.session_state.selected_coin}/USDT")
            st.info(analizar_con_ia(st.session_state.selected_coin, ticker['last'], 50, 1))

with tab_futures:
    st.subheader("Simulador de Futuros")
    with st.container():
        st.markdown('<div class="trade-card">', unsafe_allow_html=True)
        c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 1, 1])
        f_coin = c1.text_input("Cripto", value=st.session_state.selected_coin, key="f_coin").upper()
        f_side = c2.selectbox("Tipo", ["LONG", "SHORT"])
        f_lev = c3.slider("X", 1, 50, 10)
        f_amt = c4.number_input("USDT", 10, 5000, 100)
        if c5.button("🚀 ABRIR"):
            try:
                target = f"{f_coin}/USDT"
                p_entry = ccxt.kucoin().fetch_ticker(target)['last']
                conn = sqlite3.connect(DB_FILE); c = conn.cursor()
                c.execute("INSERT INTO trades (symbol, type, leverage, amount, entry_price, status, timestamp) VALUES (?,?,?,?,?,?,?)",
                          (target, f_side, f_lev, f_amt, p_entry, 'OPEN', datetime.now().strftime("%H:%M:%S")))
                conn.commit(); conn.close(); st.success("Abierta!")
            except: st.error("Error al abrir.")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("### 🟢 Posiciones")
    conn = sqlite3.connect(DB_FILE)
    open_trades = pd.read_sql_query("SELECT * FROM trades WHERE status='OPEN'", conn)
    for i, row in open_trades.iterrows():
        try:
            curr_p = ccxt.kucoin().fetch_ticker(row['symbol'])['last']
            pnl_base = ((curr_p - row['entry_price']) / row['entry_price']) * 100 if row['type'] == 'LONG' else ((row['entry_price'] - curr_p) / row['entry_price']) * 100
            final_pnl = pnl_base * row['leverage']
            
            if final_pnl <= -90.0:
                feedback = analizar_con_ia(row['symbol'], curr_p, 0, row['leverage'], modo="liquidacion")
                c = conn.cursor(); c.execute("UPDATE trades SET status='LIQUIDATED', pnl=-100, feedback=? WHERE id=?", (feedback, row['id']))
                conn.commit(); send_telegram_msg(f"💀 LIQUIDADO: {row['symbol']}\nIA: {feedback}"); st.rerun()

            color = "#00ff88" if final_pnl >= 0 else "#ff4b4b"
            st.markdown(f'<div class="trade-card"><b>{row["symbol"]}</b> {row["type"]} {row["leverage"]}x | PnL: <b style="color:{color};">{final_pnl:.2f}%</b></div>', unsafe_allow_html=True)
            
            if st.button(f"CERRAR #{row['id']}", key=f"cls_{row['id']}"):
                ganancia_usd = (row['amount'] * final_pnl) / 100
                feedback = analizar_con_ia(row['symbol'], curr_p, 0, final_pnl, modo="futuros")
                c = conn.cursor(); c.execute("UPDATE trades SET status='CLOSED', pnl=?, feedback=? WHERE id=?", (final_pnl, feedback, row['id']))
                conn.commit(); st.balloons()
                st.write(f"### Ticket: {'🟢' if final_pnl>=0 else '🔴'} ${ganancia_usd:.2f} ({final_pnl:.2f}%)")
                send_telegram_msg(f"⚔️ CIERRE: {row['symbol']} | PnL: {final_pnl:.2f}% | USD: {ganancia_usd:.2f}"); time.sleep(3); st.rerun()
        except: pass
    conn.close()

with tab_risk:
    st.markdown("### 📊 Portfolio Spot")
    if os.path.exists(PORTFOLIO_FILE):
        port = pd.read_csv(PORTFOLIO_FILE)
        for i, p_row in port.iterrows():
            try:
                actual = ccxt.kucoin().fetch_ticker(p_row['symbol'])['last']
                diff = ((actual - p_row['buy_price']) / p_row['buy_price']) * 100
                st.write(f"**{p_row['symbol']}** | PnL: {diff:.2f}%")
                if st.button("VENDIDO ✅", key=f"v_{i}"):
                    pd.read_csv(PORTFOLIO_FILE).drop(i).to_csv(PORTFOLIO_FILE, index=False); st.rerun()
            except: pass

# --- TELEGRAM ---
upds = get_updates()
for update in upds:
    st.session_state.last_update_id = update["update_id"]
    if "message" in update and "text" in update["message"]:
        msg = update["message"]["text"].lower()
        if "/help" in msg: send_telegram_msg("📜 /analizar, /scalping, /noticias")
        elif any(cmd in msg for cmd in ["/analizar", "/scalping", "/noticias"]):
            try:
                parts = msg.split(" "); cmd = parts[0].replace("/", ""); coin = parts[1].upper(); target = f"{coin}/USDT"
                ticker = ccxt.kucoin().fetch_ticker(target)
                res = analizar_con_ia(target, ticker['last'], 50.0, 1.0, modo=cmd)
                send_telegram_msg(f"🧠 {cmd.upper()}: {target}\n\n{res}")
            except: send_telegram_msg("❌ Error")

time.sleep(120); st.rerun()
import os
from dotenv import load_dotenv

# Forzamos la carga del archivo .env
load_dotenv()

TOKEN_TELEGRAM = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Debug opcional para tu terminal (borralo después)
# print(f"DEBUG LOCAL: Key cargada -> {GROQ_API_KEY[:5] if GROQ_API_KEY else 'NULA'}")
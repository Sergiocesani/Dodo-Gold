import os
from dotenv import load_dotenv

# Intentar cargar el archivo .env si existe
if os.path.exists(".env"):
    load_dotenv()

TOKEN_TELEGRAM = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Validación rápida para tu terminal local
if not TOKEN_TELEGRAM:
    print("⚠️ ADVERTENCIA: No se cargó el TOKEN_TELEGRAM. Revisá tu archivo .env")
# Debug opcional para tu terminal (borralo después)
# print(f"DEBUG LOCAL: Key cargada -> {GROQ_API_KEY[:5] if GROQ_API_KEY else 'NULA'}")
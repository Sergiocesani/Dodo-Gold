import os
from dotenv import load_dotenv

# Cargar variables desde .env (en local) o desde el Sistema (en la Nube)
load_dotenv()

TOKEN_TELEGRAM = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
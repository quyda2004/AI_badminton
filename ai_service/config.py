from dotenv import load_dotenv
import os

load_dotenv()

GEMINIUS_API_KEY      = os.getenv("GEMINIUS_API_KEY", "")
GEMINIUS_MODEL        = os.getenv("GEMINIUS_MODEL", "gemini-2.5-flash-preview-04-17")
MONGODB_URI           = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB            = os.getenv("MONGODB_DB", "ai_worker_db")
BACKEND_SERVICE_URL   = os.getenv("BACKEND_SERVICE_URL", "http://localhost:8000")
SECRET_KEY            = os.getenv("SECRET_KEY", "change-this")

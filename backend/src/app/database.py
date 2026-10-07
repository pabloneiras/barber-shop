from pathlib import Path
from app.database_manager import DatabaseManager

# Path to Database/peluqueria.db
DB_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent / "Database" / "peluqueria.db"
)

# Single typed instance for FastAPI endpoints
db: DatabaseManager = DatabaseManager(DB_PATH)
db.connect()
db.create_tables()

from pathlib import Path
from app.database_manager import DatabaseManager

# Path to Database/barber_shop.db
DB_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent / "Database" / "barber_shop.db"
)

# Single typed instance for FastAPI endpoints
db: DatabaseManager = DatabaseManager(DB_PATH)
db.connect()
db.create_tables()

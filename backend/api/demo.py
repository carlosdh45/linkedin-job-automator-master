from fastapi import APIRouter, Depends

from backend.config import get_db_path
from src.seed_data import clear_demo_data, seed_demo_data

router = APIRouter()


@router.post("/demo/seed")
def seed(db_path: str = Depends(get_db_path)):
    """Seed the DB with safe demo data. No external calls."""
    stats = seed_demo_data(db_path)
    return {"seeded": True, "stats": stats}


@router.post("/demo/clear")
def clear(db_path: str = Depends(get_db_path)):
    """Remove all demo records (.test domains). No external calls."""
    clear_demo_data(db_path)
    return {"cleared": True}

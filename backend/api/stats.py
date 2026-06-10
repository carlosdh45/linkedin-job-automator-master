from fastapi import APIRouter, Depends

from backend.config import get_db_path
from src import db as src_db

router = APIRouter()


@router.get("/stats")
def get_stats(db_path: str = Depends(get_db_path)):
    return src_db.get_stats(db_path)

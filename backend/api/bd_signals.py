from datetime import datetime

from fastapi import APIRouter, Depends

from backend.config import get_bd_signal_path
from backend.models.bd import BDSignal, BDSignalCreate
from backend.services.bd_signal_store import list_signals, create_signal

router = APIRouter(prefix="/bd/signals", tags=["bd-signals"])


@router.get("", response_model=list[BDSignal])
def get_signals(path: str = Depends(get_bd_signal_path)):
    return list_signals(path)


@router.post("", response_model=BDSignal, status_code=201)
def create_signal_endpoint(data: BDSignalCreate, path: str = Depends(get_bd_signal_path)):
    payload = data.model_dump()
    if not payload.get("detected_at"):
        payload["detected_at"] = datetime.utcnow().date().isoformat()
    return create_signal(path, payload)

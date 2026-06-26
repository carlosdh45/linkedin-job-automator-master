from fastapi import APIRouter, Depends

from backend.config import get_bd_icp_config_path
from backend.models.bd import BDICPConfig, BDICPConfigUpdate
from backend.services.bd_icp_store import load_icp_config, update_icp_config

router = APIRouter(prefix="/bd/icp-config", tags=["bd-icp"])


@router.get("", response_model=BDICPConfig)
def get_icp_config(path: str = Depends(get_bd_icp_config_path)):
    return load_icp_config(path)


@router.put("", response_model=BDICPConfig)
def put_icp_config(data: BDICPConfigUpdate, path: str = Depends(get_bd_icp_config_path)):
    return update_icp_config(path, data.model_dump(exclude_none=True))

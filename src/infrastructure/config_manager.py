import os
import json
from typing import List, Dict, Any, Optional

try:
    from pydantic import BaseModel
except ImportError:
    class BaseModel:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
        def get(self, key: str, default: Any = None) -> Any:
            return getattr(self, key, default)
        def dict(self) -> Dict[str, Any]:
            return self.__dict__

class XAppConfig(BaseModel):
    name: str = "iqos-xapp-rdl"
    version: str = "2.0.0"

class RMRConfig(BaseModel):
    port: int = 4560
    max_message_size: int = 65536
    wait_for_ready: bool = True

class HttpConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8080

class MetricsConfig(BaseModel):
    port: int = 8081

class SDLConfig(BaseModel):
    use_fake: bool = True
    namespace: str = "iqos-xapp-rdl"

class E2Config(BaseModel):
    subscription_period_ms: int = 1000
    retry_interval_seconds: int = 5
    maximum_retries: int = 10

class KpmConfig(BaseModel):
    service_model_versions: List[str] = ["v2", "v3"]
    measurements: List[str] = ["DRB.UEThpDl", "DRB.UEThpUl", "DRB.RlcSduDelayDl", "RRU.PrbUsedDl"]

class ControlConfig(BaseModel):
    enabled: bool = True
    dry_run: bool = False
    service_model: str = "E2SM-RC"

class AppConfig(BaseModel):
    xapp: Optional[XAppConfig] = None
    rmr: Optional[RMRConfig] = None
    http: Optional[HttpConfig] = None
    metrics: Optional[MetricsConfig] = None
    sdl: Optional[SDLConfig] = None
    e2: Optional[E2Config] = None
    kpm: Optional[KpmConfig] = None
    control: Optional[ControlConfig] = None
    
    class Config:
        extra = "allow"
        arbitrary_types_allowed = True

    def get(self, key: str, default: Any = None) -> Any:
        val = getattr(self, key, None)
        if val is not None:
            return val
        if hasattr(self, "__pydantic_extra__") and self.__pydantic_extra__:
            return self.__pydantic_extra__.get(key, default)
        return default
        
    def __getitem__(self, item):
        val = getattr(self, item, None)
        if val is not None:
            return val
        if hasattr(self, "__pydantic_extra__") and self.__pydantic_extra__:
            return self.__pydantic_extra__[item]
        raise KeyError(item)

class ConfigManager:
    def __init__(self, filepath: str = "configs/config-file.json"):
        self.filepath = filepath
        self.config = self.load_config(filepath)

    def load_config(self, filepath: str = None) -> AppConfig:
        target = filepath or self.filepath or "configs/config-file.json"
        if not os.path.exists(target):
            # Fallback to default
            self.config = AppConfig()
            return self.config
        
        try:
            with open(target, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.config = AppConfig(**data)
        except Exception:
            self.config = AppConfig()
            
        return self.config

import os
import re
from dataclasses import dataclass, MISSING

from dotenv import load_dotenv

load_dotenv()

def _to_env_name(name: str) -> str:
    return re.sub(r'(?<!^)(?=[A-Z])', '_', name).upper()


def _get_env_value(field_name: str, default=None, field_type=str):
    env_name = field_name.upper()
    value = os.getenv(env_name, default)
    
    if value is None:
        return None
        
    if field_type == int:
        return int(value)
    elif field_type == bool:
        return value.lower() in ('true', '1', 'yes', 'on')
    elif field_type == float:
        return float(value)
    
    return value


def _create_instance(cls):
    fields = cls.__dataclass_fields__
    kwargs = {}
    
    for field_name, field_info in fields.items():
        field_type = field_info.type
        default = field_info.default
        
        if field_info.default_factory is not MISSING:
            default = field_info.default_factory()

        value = _get_env_value(field_name, default, field_type)

        if value is None and default is MISSING:
            raise ValueError(f"{field_name} not found in .env file")
        
        kwargs[field_name] = value
    
    return cls(**kwargs)


@dataclass(frozen=True)
class Telegram:
    BOT_TOKEN: str


@dataclass(frozen=True)
class Database:
    URI: str = "sqlite:///bot.db"


@dataclass(frozen=True)
class Logging:
    LEVEL: str = "INFO"
    FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


_locals = list(locals().items())
for name, obj in _locals:
    if isinstance(obj, type) and hasattr(obj, '__dataclass_fields__'):
        locals()[name] = _create_instance(obj)

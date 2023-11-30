import json
import platform
from datetime import date, datetime
from typing import Any, Dict, Union

import psutil
from app.schemas import JSONSerializable


def get_system_info(cpu_percent_interval: int = 1) -> Dict:
    # Gather OS information
    os_info = {
        "os_name": platform.system(),
        "os_release": platform.release(),
        "os_version": platform.version(),
        "machine_type": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
    }

    # Gather CPU information
    cpu_info = {
        "cpu_count": psutil.cpu_count(),
        "cpu_usage_percent": psutil.cpu_percent(interval=cpu_percent_interval),
    }

    # Gather Memory information
    memory = psutil.virtual_memory()
    memory_info = {
        "total_memory_mb": memory.total / (1024 * 1024),
        "available_memory_mb": memory.available / (1024 * 1024),
        "used_memory_mb": memory.used / (1024 * 1024),
        "memory_usage_percent": memory.percent,
    }

    # Combining all the information
    system_info = {"operating_system": os_info, "cpu": cpu_info, "memory": memory_info}

    return system_info


def is_json_serializable(obj: Union[JSONSerializable, Any]) -> bool:
    """Check if an object is JSON serializable."""

    try:
        json.dumps(obj, cls=DateTimeEncoder)
        return True
    except TypeError:
        return False


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super(DateTimeEncoder, self).default(obj)

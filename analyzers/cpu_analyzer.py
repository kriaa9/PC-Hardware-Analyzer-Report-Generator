import psutil
import cpuinfo
import platform
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CPUData:
    brand: str = "Unknown"
    architecture: str = "Unknown"
    bits: int = 64
    hz_actual: str = "N/A"
    hz_advertised: str = "N/A"
    physical_cores: int = 0
    logical_cores: int = 0
    l2_cache_size: Optional[int] = None
    l3_cache_size: Optional[int] = None
    usage_percent: float = 0.0
    per_core_usage: list = field(default_factory=list)
    temperature: Optional[float] = None
    frequency_current: float = 0.0
    frequency_min: float = 0.0
    frequency_max: float = 0.0
    ctx_switches: int = 0
    interrupts: int = 0
    is_throttling: bool = False


class CPUAnalyzer:
    def __init__(self):
        self._info = cpuinfo.get_cpu_info()

    def collect(self) -> CPUData:
        data = CPUData()
        data.brand = self._info.get("brand_raw", platform.processor())
        data.architecture = self._info.get("arch", platform.machine())
        data.bits = self._info.get("bits", 64)
        data.hz_actual = self._info.get("hz_actual_friendly", "N/A")
        data.hz_advertised = self._info.get("hz_advertised_friendly", "N/A")
        data.l2_cache_size = self._info.get("l2_cache_size")
        data.l3_cache_size = self._info.get("l3_cache_size")
        data.physical_cores = psutil.cpu_count(logical=False) or 1
        data.logical_cores = psutil.cpu_count(logical=True) or 1
        data.usage_percent = psutil.cpu_percent(interval=1)
        data.per_core_usage = psutil.cpu_percent(interval=0.5, percpu=True)
        freq = psutil.cpu_freq()
        if freq:
            data.frequency_current = round(freq.current, 2)
            data.frequency_min = round(freq.min, 2)
            data.frequency_max = round(freq.max, 2)
        data.temperature = self._get_cpu_temp()
        data.is_throttling = self._detect_throttling(data)
        stats = psutil.cpu_stats()
        data.ctx_switches = stats.ctx_switches
        data.interrupts = stats.interrupts
        return data

    def _get_cpu_temp(self) -> Optional[float]:
        try:
            temps = psutil.sensors_temperatures()
            if not temps:
                return None
            for key in ("coretemp", "cpu_thermal", "k10temp", "acpitz"):
                if key in temps and temps[key]:
                    return round(temps[key][0].current, 1)
        except (AttributeError, Exception):
            pass
        return None

    def _detect_throttling(self, data: CPUData) -> bool:
        if data.frequency_current and data.frequency_max:
            ratio = data.frequency_current / data.frequency_max
            if ratio < 0.75 and data.temperature and data.temperature > 85:
                return True
        return False

    def get_usage_history(self, duration: int = 5, interval: float = 0.5) -> list:
        samples = []
        end_time = time.time() + duration
        while time.time() < end_time:
            samples.append(psutil.cpu_percent(interval=interval))
        return samples

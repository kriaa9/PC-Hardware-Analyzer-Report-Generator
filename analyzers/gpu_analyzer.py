import platform
import subprocess
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class GPUData:
    name: str = "Not Available"
    index: int = 0
    vram_total_mb: float = 0.0
    vram_used_mb: float = 0.0
    vram_free_mb: float = 0.0
    gpu_utilization: float = 0.0
    memory_utilization: float = 0.0
    temperature: Optional[float] = None
    fan_speed: Optional[float] = None
    power_draw: Optional[float] = None
    power_limit: Optional[float] = None
    driver_version: str = "N/A"
    compute_capability: str = "N/A"


class GPUAnalyzer:
    def collect(self) -> list[GPUData]:
        gpus = self._try_gputil()
        if gpus:
            return gpus

        gpus = self._try_nvidia_smi()
        if gpus:
            return gpus

        gpus = self._try_platform_tools()
        if gpus:
            return gpus

        return [GPUData()]

    def _try_gputil(self) -> list[GPUData]:
        try:
            import GPUtil
            nvidia_gpus = GPUtil.getGPUs()
            if not nvidia_gpus:
                return []
            results = []
            for gpu in nvidia_gpus:
                data = GPUData(
                    name=gpu.name,
                    index=gpu.id,
                    vram_total_mb=gpu.memoryTotal,
                    vram_used_mb=gpu.memoryUsed,
                    vram_free_mb=gpu.memoryFree,
                    gpu_utilization=gpu.load * 100,
                    memory_utilization=gpu.memoryUtil * 100 if gpu.memoryUtil else 0.0,
                    temperature=gpu.temperature,
                    driver_version=gpu.driver,
                )
                results.append(data)
            return results
        except Exception:
            return []

    def _try_nvidia_smi(self) -> list[GPUData]:
        try:
            out = subprocess.check_output(
                [
                    "nvidia-smi",
                    "--query-gpu=name,index,memory.total,memory.used,memory.free,"
                    "utilization.gpu,utilization.memory,temperature.gpu,"
                    "fan.speed,power.draw,power.limit,driver_version",
                    "--format=csv,noheader,nounits"
                ],
                text=True, stderr=subprocess.DEVNULL, timeout=10
            )
            results = []
            for line in out.strip().splitlines():
                parts = [p.strip() for p in line.split(",")]
                if len(parts) < 12:
                    continue
                data = GPUData(
                    name=parts[0],
                    index=int(parts[1]),
                    vram_total_mb=float(parts[2]),
                    vram_used_mb=float(parts[3]),
                    vram_free_mb=float(parts[4]),
                    gpu_utilization=float(parts[5]),
                    memory_utilization=float(parts[6]),
                    temperature=float(parts[7]) if parts[7] != "[N/A]" else None,
                    fan_speed=float(parts[8]) if parts[8] != "[N/A]" else None,
                    power_draw=float(parts[9]) if parts[9] != "[N/A]" else None,
                    power_limit=float(parts[10]) if parts[10] != "[N/A]" else None,
                    driver_version=parts[11],
                )
                results.append(data)
            return results
        except Exception:
            return []

    def _try_platform_tools(self) -> list[GPUData]:
        system = platform.system()
        if system == "Windows":
            return self._windows_gpu()
        elif system == "Darwin":
            return self._macos_gpu()
        elif system == "Linux":
            return self._linux_gpu()
        return []

    def _windows_gpu(self) -> list[GPUData]:
        try:
            import wmi
            c = wmi.WMI()
            results = []
            for idx, gpu in enumerate(c.Win32_VideoController()):
                data = GPUData(
                    name=gpu.Name or "Unknown GPU",
                    index=idx,
                    vram_total_mb=round(int(gpu.AdapterRAM or 0) / (1024 ** 2), 0),
                    driver_version=gpu.DriverVersion or "N/A",
                )
                results.append(data)
            return results if results else []
        except Exception:
            return []

    def _macos_gpu(self) -> list[GPUData]:
        try:
            out = subprocess.check_output(
                ["system_profiler", "SPDisplaysDataType"], text=True
            )
            results = []
            current_gpu = None
            for line in out.splitlines():
                line = line.strip()
                if "Chipset Model:" in line:
                    if current_gpu:
                        results.append(current_gpu)
                    current_gpu = GPUData(
                        name=line.split(":")[1].strip(),
                        index=len(results),
                    )
                elif current_gpu and "VRAM" in line:
                    try:
                        vram_str = line.split(":")[1].strip().split()[0]
                        current_gpu.vram_total_mb = float(vram_str) * 1024  # GB → MB
                    except (ValueError, IndexError):
                        pass
            if current_gpu:
                results.append(current_gpu)
            return results
        except Exception:
            return []

    def _linux_gpu(self) -> list[GPUData]:
        try:
            out = subprocess.check_output(["lspci"], text=True, stderr=subprocess.DEVNULL)
            results = []
            for line in out.splitlines():
                if "VGA" in line or "3D" in line or "Display" in line:
                    name = line.split(": ", 1)[1] if ": " in line else line
                    results.append(GPUData(name=name.strip(), index=len(results)))
            return results if results else []
        except Exception:
            return []

import psutil
import platform
import subprocess
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class MemoryData:
    total_gb: float = 0.0
    available_gb: float = 0.0
    used_gb: float = 0.0
    free_gb: float = 0.0
    usage_percent: float = 0.0
    swap_total_gb: float = 0.0
    swap_used_gb: float = 0.0
    swap_percent: float = 0.0
    memory_type: str = "Unknown"
    speed_mhz: Optional[int] = None
    slots_used: int = 0
    slots_total: int = 0
    channel_mode: str = "Unknown"


class MemoryAnalyzer:
    def collect(self) -> MemoryData:
        data = MemoryData()
        vm = psutil.virtual_memory()
        data.total_gb = round(vm.total / (1024 ** 3), 2)
        data.available_gb = round(vm.available / (1024 ** 3), 2)
        data.used_gb = round(vm.used / (1024 ** 3), 2)
        data.free_gb = round(vm.free / (1024 ** 3), 2)
        data.usage_percent = vm.percent

        swap = psutil.swap_memory()
        data.swap_total_gb = round(swap.total / (1024 ** 3), 2)
        data.swap_used_gb = round(swap.used / (1024 ** 3), 2)
        data.swap_percent = swap.percent

        system = platform.system()
        if system == "Linux":
            self._collect_linux_dmi(data)
        elif system == "Windows":
            self._collect_windows_wmi(data)
        elif system == "Darwin":
            self._collect_macos_system_profiler(data)

        return data

    def _collect_linux_dmi(self, data: MemoryData):
        try:
            out = subprocess.check_output(
                ["sudo", "dmidecode", "-t", "memory"], text=True, stderr=subprocess.DEVNULL
            )
            slots_total = 0
            slots_used = 0
            for line in out.splitlines():
                line = line.strip()
                if "Number Of Devices:" in line:
                    slots_total = int(line.split(":")[1].strip())
                elif line.startswith("Size:") and "No Module" not in line:
                    slots_used += 1
                elif line.startswith("Speed:") and "Unknown" not in line:
                    try:
                        data.speed_mhz = int(line.split(":")[1].strip().split()[0])
                    except (ValueError, IndexError):
                        pass
                elif line.startswith("Type:") and "Unknown" not in line:
                    mem_type = line.split(":")[1].strip()
                    if mem_type in ("DDR4", "DDR5", "DDR3", "LPDDR4", "LPDDR5"):
                        data.memory_type = mem_type
            data.slots_total = slots_total
            data.slots_used = slots_used
            if slots_used >= 2:
                data.channel_mode = "Dual Channel"
            elif slots_used == 1:
                data.channel_mode = "Single Channel"
        except Exception:
            pass

    def _collect_windows_wmi(self, data: MemoryData):
        try:
            import wmi
            c = wmi.WMI()
            modules = c.Win32_PhysicalMemory()
            data.slots_used = len(modules)
            for m in modules:
                if m.Speed:
                    data.speed_mhz = int(m.Speed)
                if m.SMBIOSMemoryType:
                    type_map = {20: "DDR", 21: "DDR2", 24: "DDR3", 26: "DDR4", 34: "DDR5"}
                    data.memory_type = type_map.get(m.SMBIOSMemoryType, "Unknown")
            if data.slots_used >= 2:
                data.channel_mode = "Dual Channel"
            elif data.slots_used == 1:
                data.channel_mode = "Single Channel"
            # Try to get total slots
            try:
                arrays = c.Win32_PhysicalMemoryArray()
                if arrays:
                    data.slots_total = int(arrays[0].MemoryDevices or 0)
            except Exception:
                data.slots_total = data.slots_used
        except ImportError:
            pass
        except Exception:
            pass

    def _collect_macos_system_profiler(self, data: MemoryData):
        try:
            out = subprocess.check_output(
                ["system_profiler", "SPMemoryDataType"], text=True
            )
            slots_used = 0
            for line in out.splitlines():
                line = line.strip()
                if "Speed:" in line:
                    try:
                        data.speed_mhz = int(line.split(":")[1].strip().split()[0])
                    except (ValueError, IndexError):
                        pass
                elif "Type:" in line:
                    mem_type = line.split(":")[1].strip()
                    if mem_type in ("DDR4", "DDR5", "DDR3", "LPDDR4", "LPDDR5"):
                        data.memory_type = mem_type
                elif "Size:" in line and "Empty" not in line:
                    slots_used += 1
            data.slots_used = slots_used
            data.slots_total = slots_used  # macOS doesn't easily expose total slots
            if slots_used >= 2:
                data.channel_mode = "Dual Channel"
            elif slots_used == 1:
                data.channel_mode = "Single Channel"
        except Exception:
            pass

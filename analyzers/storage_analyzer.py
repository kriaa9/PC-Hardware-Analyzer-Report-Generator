import psutil
import platform
import subprocess
import shutil
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PartitionData:
    device: str = ""
    mountpoint: str = ""
    fstype: str = ""
    total_gb: float = 0.0
    used_gb: float = 0.0
    free_gb: float = 0.0
    usage_percent: float = 0.0


@dataclass
class DiskData:
    name: str = ""
    model: str = "Unknown"
    serial: str = "Unknown"
    disk_type: str = "Unknown"  # HDD / SSD / NVMe
    size_gb: float = 0.0
    partitions: list = field(default_factory=list)
    read_bytes: int = 0
    write_bytes: int = 0
    smart_status: str = "Unknown"
    smart_temperature: Optional[float] = None


class StorageAnalyzer:
    def collect(self) -> list[DiskData]:
        disks = []
        io_counters = psutil.disk_io_counters(perdisk=True)
        partitions = psutil.disk_partitions(all=False)

        # Group partitions by physical disk (simplified approach)
        disk_map = {}
        for part in partitions:
            try:
                usage = psutil.disk_usage(part.mountpoint)
            except (PermissionError, OSError):
                continue

            part_data = PartitionData(
                device=part.device,
                mountpoint=part.mountpoint,
                fstype=part.fstype,
                total_gb=round(usage.total / (1024 ** 3), 2),
                used_gb=round(usage.used / (1024 ** 3), 2),
                free_gb=round(usage.free / (1024 ** 3), 2),
                usage_percent=usage.percent,
            )

            # Use the base device name as the disk key
            base_device = self._get_base_device(part.device)
            if base_device not in disk_map:
                disk_map[base_device] = DiskData(name=base_device)
            disk_map[base_device].partitions.append(part_data)

        # Enrich disk data
        for name, disk in disk_map.items():
            disk.size_gb = round(
                sum(p.total_gb for p in disk.partitions), 2
            )
            disk.disk_type = self._detect_disk_type(name)
            self._get_smart_data(name, disk)

            # I/O counters
            for io_name, counters in (io_counters or {}).items():
                if io_name in name or name in io_name:
                    disk.read_bytes = counters.read_bytes
                    disk.write_bytes = counters.write_bytes
                    break

            disks.append(disk)

        return disks

    def _get_base_device(self, device: str) -> str:
        system = platform.system()
        if system == "Windows":
            return device[:2]  # e.g., "C:"
        elif system == "Linux":
            import re
            match = re.match(r"(/dev/[a-z]+)", device)
            return match.group(1) if match else device
        elif system == "Darwin":
            return device.rsplit("s", 1)[0] if "s" in device else device
        return device

    def _detect_disk_type(self, device: str) -> str:
        system = platform.system()
        if system == "Linux":
            try:
                dev_name = device.replace("/dev/", "")
                rotational_path = f"/sys/block/{dev_name}/queue/rotational"
                with open(rotational_path) as f:
                    return "HDD" if f.read().strip() == "1" else "SSD"
            except Exception:
                if "nvme" in device:
                    return "NVMe"
        elif system == "Windows":
            try:
                import wmi
                c = wmi.WMI()
                for d in c.Win32_DiskDrive():
                    if "SSD" in (d.Model or "").upper() or "NVME" in (d.Model or "").upper():
                        return "NVMe" if "NVME" in (d.Model or "").upper() else "SSD"
                    elif "NVM" in (d.InterfaceType or "").upper():
                        return "NVMe"
                return "HDD"
            except Exception:
                pass
        elif system == "Darwin":
            try:
                out = subprocess.check_output(
                    ["diskutil", "info", device], text=True, stderr=subprocess.DEVNULL
                )
                if "Solid State" in out:
                    return "SSD"
                return "HDD"
            except Exception:
                pass
        return "Unknown"

    def _get_smart_data(self, device: str, disk: DiskData):
        if not shutil.which("smartctl"):
            disk.smart_status = "N/A (smartctl not installed)"
            return
        try:
            out = subprocess.check_output(
                ["smartctl", "-H", "-A", device],
                text=True, stderr=subprocess.DEVNULL, timeout=10
            )
            if "PASSED" in out:
                disk.smart_status = "PASSED"
            elif "FAILED" in out:
                disk.smart_status = "FAILED"
            else:
                disk.smart_status = "Unknown"

            for line in out.splitlines():
                if "Temperature_Celsius" in line or "Temperature_Internal" in line:
                    parts = line.split()
                    for p in reversed(parts):
                        try:
                            disk.smart_temperature = float(p)
                            break
                        except ValueError:
                            continue
        except Exception:
            disk.smart_status = "N/A"

import psutil
import platform
import subprocess
from dataclasses import dataclass
from typing import Optional


@dataclass
class BatteryData:
    present: bool = False
    percent: float = 0.0
    plugged_in: bool = False
    time_remaining_min: Optional[float] = None
    design_capacity_mwh: Optional[int] = None
    full_charge_capacity_mwh: Optional[int] = None
    health_percent: float = 100.0
    charge_cycles: Optional[int] = None
    status: str = "Unknown"


class BatteryAnalyzer:
    def collect(self) -> BatteryData:
        data = BatteryData()
        battery = psutil.sensors_battery()
        if battery is None:
            data.present = False
            return data

        data.present = True
        data.percent = round(battery.percent, 1)
        data.plugged_in = battery.power_plugged
        if battery.secsleft and battery.secsleft > 0:
            data.time_remaining_min = round(battery.secsleft / 60, 1)
        data.status = "Charging" if battery.power_plugged else "Discharging"

        # Platform-specific deep info
        if platform.system() == "Linux":
            self._linux_battery_details(data)
        elif platform.system() == "Darwin":
            self._macos_battery_details(data)
        elif platform.system() == "Windows":
            self._windows_battery_details(data)

        return data

    def _linux_battery_details(self, data: BatteryData):
        import glob
        paths = glob.glob("/sys/class/power_supply/BAT*")
        if not paths:
            return
        bat = paths[0]
        try:
            with open(f"{bat}/energy_full_design") as f:
                data.design_capacity_mwh = int(f.read()) // 1000
            with open(f"{bat}/energy_full") as f:
                data.full_charge_capacity_mwh = int(f.read()) // 1000
            if data.design_capacity_mwh:
                data.health_percent = round(
                    (data.full_charge_capacity_mwh / data.design_capacity_mwh) * 100, 1
                )
            with open(f"{bat}/cycle_count") as f:
                data.charge_cycles = int(f.read().strip())
        except Exception:
            pass

    def _macos_battery_details(self, data: BatteryData):
        try:
            out = subprocess.check_output(
                ["system_profiler", "SPPowerDataType"], text=True
            )
            for line in out.splitlines():
                if "Cycle Count:" in line:
                    data.charge_cycles = int(line.split(":")[1].strip())
                elif "Maximum Capacity:" in line:
                    val = line.split(":")[1].strip().replace("%", "")
                    data.health_percent = float(val)
        except Exception:
            pass

    def _windows_battery_details(self, data: BatteryData):
        try:
            import wmi
            c = wmi.WMI()
            for b in c.Win32_Battery():
                data.design_capacity_mwh = int(b.DesignCapacity or 0)
                data.health_percent = round(float(b.EstimatedChargeRemaining or 0), 1)
        except Exception:
            pass

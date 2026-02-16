import psutil
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class InterfaceData:
    name: str = ""
    mac_address: str = "N/A"
    ipv4_address: str = "N/A"
    bytes_sent: int = 0
    bytes_recv: int = 0
    speed_mbps: Optional[int] = None
    is_up: bool = False
    upload_speed_kbps: float = 0.0
    download_speed_kbps: float = 0.0


@dataclass
class NetworkData:
    interfaces: list = field(default_factory=list)


class NetworkAnalyzer:
    def collect(self) -> NetworkData:
        data = NetworkData()
        addrs = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
        io_before = psutil.net_io_counters(pernic=True)

        # Wait 1 second to measure speed
        time.sleep(1)
        io_after = psutil.net_io_counters(pernic=True)

        for iface_name, iface_addrs in addrs.items():
            iface = InterfaceData(name=iface_name)

            # MAC and IPv4
            for addr in iface_addrs:
                if addr.family.name == "AF_LINK" or addr.family.value == -1:
                    iface.mac_address = addr.address
                elif addr.family.name == "AF_INET":
                    iface.ipv4_address = addr.address

            # Stats
            if iface_name in stats:
                st = stats[iface_name]
                iface.is_up = st.isup
                iface.speed_mbps = st.speed if st.speed > 0 else None

            # I/O counters
            if iface_name in io_after:
                iface.bytes_sent = io_after[iface_name].bytes_sent
                iface.bytes_recv = io_after[iface_name].bytes_recv

            # Speed calculation (KB/s over 1 second sample)
            if iface_name in io_before and iface_name in io_after:
                sent_diff = io_after[iface_name].bytes_sent - io_before[iface_name].bytes_sent
                recv_diff = io_after[iface_name].bytes_recv - io_before[iface_name].bytes_recv
                iface.upload_speed_kbps = round(sent_diff / 1024, 2)
                iface.download_speed_kbps = round(recv_diff / 1024, 2)

            data.interfaces.append(iface)

        return data

"""
PC Hardware Analyzer — Main Entry Point
Usage:
  python main.py                  # Run full analysis + HTML report
  python main.py --pdf            # Also generate PDF
  python main.py --no-benchmark   # Skip benchmarks (faster)
  python main.py --output ./my_reports
"""

import click
import time
import platform
import socket
from datetime import datetime
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.table import Table

from analyzers.cpu_analyzer import CPUAnalyzer
from analyzers.memory_analyzer import MemoryAnalyzer
from analyzers.storage_analyzer import StorageAnalyzer
from analyzers.gpu_analyzer import GPUAnalyzer
from analyzers.battery_analyzer import BatteryAnalyzer
from analyzers.network_analyzer import NetworkAnalyzer
from benchmarks.cpu_bench import single_core_benchmark, multi_core_benchmark
from benchmarks.memory_bench import read_bandwidth_test, write_bandwidth_test
from benchmarks.disk_bench import sequential_write_test, sequential_read_test
from reporters.html_report import HTMLReporter
from reporters.pdf_report import PDFReporter
import config

console = Console()


def collect_system_overview():
    import psutil
    boot_time = psutil.boot_time()
    uptime_seconds = time.time() - boot_time
    uptime_hours = int(uptime_seconds // 3600)
    uptime_minutes = int((uptime_seconds % 3600) // 60)
    return {
        "hostname": socket.gethostname(),
        "os": f"{platform.system()} {platform.release()}",
        "os_version": platform.version(),
        "architecture": platform.machine(),
        "python_version": platform.python_version(),
        "boot_time": datetime.fromtimestamp(boot_time).strftime("%Y-%m-%d %H:%M:%S"),
        "uptime": f"{uptime_hours}h {uptime_minutes}m",
        "scan_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def compute_health_score(data: dict) -> tuple[int, list]:
    """
    Compute overall system health score (0-100) and recommendations.
    Deducts points for issues, adds to recommendations list.
    """
    score = 100
    recommendations = []

    # CPU checks
    cpu = data.get("cpu")
    if cpu:
        if cpu.temperature and cpu.temperature > config.TEMP_CPU_CRITICAL:
            score -= 20
            recommendations.append({
                "level": "critical",
                "message": f"CPU temperature is dangerously high ({cpu.temperature}°C). Check cooling immediately."
            })
        elif cpu.temperature and cpu.temperature > config.TEMP_CPU_WARNING:
            score -= 10
            recommendations.append({
                "level": "warning",
                "message": f"CPU temperature is elevated ({cpu.temperature}°C). Consider improving airflow."
            })
        if cpu.is_throttling:
            score -= 15
            recommendations.append({
                "level": "critical",
                "message": "CPU is thermal throttling — performance is being reduced to prevent damage."
            })

    # RAM checks
    memory = data.get("memory")
    if memory:
        if memory.usage_percent > config.RAM_USAGE_CRITICAL:
            score -= 15
            recommendations.append({
                "level": "critical",
                "message": f"RAM usage is critically high ({memory.usage_percent}%). Upgrade RAM or close applications."
            })
        elif memory.usage_percent > config.RAM_USAGE_WARNING:
            score -= 8
            recommendations.append({
                "level": "warning",
                "message": f"RAM usage is high ({memory.usage_percent}%). Consider adding more RAM."
            })

    # Storage checks
    for disk in data.get("storage", []):
        if disk.smart_status == "FAILED":
            score -= 30
            recommendations.append({
                "level": "critical",
                "message": f"Drive {disk.name} has FAILED S.M.A.R.T. status. Back up data immediately!"
            })
        if disk.smart_temperature and disk.smart_temperature > config.TEMP_DISK_WARNING:
            score -= 10
            recommendations.append({
                "level": "warning",
                "message": f"Drive {disk.name} is running hot ({disk.smart_temperature}°C). Check case airflow."
            })
        for part in disk.partitions:
            if part.usage_percent > config.DISK_USAGE_CRITICAL:
                score -= 10
                recommendations.append({
                    "level": "critical",
                    "message": f"Partition {part.mountpoint} is nearly full ({part.usage_percent}%). Free up space."
                })

    # Battery checks
    battery = data.get("battery")
    if battery and battery.present:
        if battery.health_percent < config.BATTERY_HEALTH_FAIR:
            score -= 15
            recommendations.append({
                "level": "warning",
                "message": f"Battery health is poor ({battery.health_percent:.0f}%). Consider replacing the battery."
            })

    # Clamp score between 0 and 100
    score = max(0, min(100, score))

    if not recommendations:
        recommendations.append({
            "level": "good",
            "message": "All systems healthy! No issues detected."
        })

    return score, recommendations


@click.command()
@click.option("--pdf", is_flag=True, help="Also generate a PDF report")
@click.option("--no-benchmark", is_flag=True, help="Skip performance benchmarks")
@click.option("--output", default=config.DEFAULT_OUTPUT_DIR, help="Output directory for reports")
def main(pdf, no_benchmark, output):
    console.print(Panel.fit(
        "[bold cyan]🖥️  PC Hardware Analyzer[/bold cyan]\n"
        "[dim]Scanning your system...[/dim]",
        border_style="cyan"
    ))

    data = {}

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:

        # System Overview
        t = progress.add_task("Collecting system overview...", total=None)
        data["system"] = collect_system_overview()
        progress.remove_task(t)
        console.print("[green]✓[/green] System overview collected")

        # CPU
        t = progress.add_task("Analyzing CPU...", total=None)
        data["cpu"] = CPUAnalyzer().collect()
        progress.remove_task(t)
        console.print("[green]✓[/green] CPU analyzed")

        # Memory
        t = progress.add_task("Analyzing Memory...", total=None)
        data["memory"] = MemoryAnalyzer().collect()
        progress.remove_task(t)
        console.print("[green]✓[/green] Memory analyzed")

        # Storage
        t = progress.add_task("Analyzing Storage...", total=None)
        data["storage"] = StorageAnalyzer().collect()
        progress.remove_task(t)
        console.print("[green]✓[/green] Storage analyzed")

        # GPU
        t = progress.add_task("Analyzing GPU...", total=None)
        data["gpu"] = GPUAnalyzer().collect()
        progress.remove_task(t)
        console.print("[green]✓[/green] GPU analyzed")

        # Battery
        t = progress.add_task("Checking Battery...", total=None)
        data["battery"] = BatteryAnalyzer().collect()
        progress.remove_task(t)
        console.print("[green]✓[/green] Battery checked")

        # Network
        t = progress.add_task("Analyzing Network...", total=None)
        data["network"] = NetworkAnalyzer().collect()
        progress.remove_task(t)
        console.print("[green]✓[/green] Network analyzed")

        # Benchmarks
        if not no_benchmark:
            console.print("\n[bold yellow]Running Benchmarks...[/bold yellow]")

            t = progress.add_task(f"CPU single-core benchmark ({config.CPU_BENCH_DURATION}s)...", total=None)
            data["bench_cpu_single"] = single_core_benchmark(duration=config.CPU_BENCH_DURATION)
            progress.remove_task(t)

            t = progress.add_task(f"CPU multi-core benchmark ({config.CPU_BENCH_DURATION}s)...", total=None)
            data["bench_cpu_multi"] = multi_core_benchmark(duration=config.CPU_BENCH_DURATION)
            progress.remove_task(t)

            t = progress.add_task("Memory bandwidth test...", total=None)
            data["bench_mem_read"] = read_bandwidth_test(size_mb=config.MEMORY_BENCH_SIZE_MB)
            data["bench_mem_write"] = write_bandwidth_test(size_mb=config.MEMORY_BENCH_SIZE_MB)
            progress.remove_task(t)

            t = progress.add_task("Disk I/O benchmark...", total=None)
            tmp_path = sequential_write_test(size_mb=config.DISK_BENCH_SIZE_MB)
            data["bench_disk_write"] = tmp_path[1]   # speed MB/s
            data["bench_disk_read"] = sequential_read_test(tmp_path[0])
            progress.remove_task(t)

            console.print("[green]✓[/green] Benchmarks complete")

    # Health Score
    health_score, recommendations = compute_health_score(data)
    data["health_score"] = health_score
    data["recommendations"] = recommendations

    # Print quick summary
    console.print("\n")
    table = Table(title="System Health Summary", border_style="cyan")
    table.add_column("Component", style="bold")
    table.add_column("Status")
    cpu = data["cpu"]
    table.add_row("CPU", f"{cpu.brand} | {cpu.physical_cores}C/{cpu.logical_cores}T | {cpu.usage_percent}% usage")
    mem = data["memory"]
    table.add_row("RAM", f"{mem.total_gb} GB {mem.memory_type} | {mem.usage_percent}% used")
    for disk in data["storage"][:2]:
        table.add_row(f"Disk ({disk.name})", f"{disk.size_gb} GB {disk.disk_type} | SMART: {disk.smart_status}")
    score_color = "green" if health_score >= 80 else "yellow" if health_score >= 60 else "red"
    table.add_row("Health Score", f"[{score_color}]{health_score}/100[/{score_color}]")
    console.print(table)

    # Generate Reports
    import os
    os.makedirs(output, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    console.print("\n[bold]Generating Reports...[/bold]")
    html_path = os.path.join(output, f"hardware_report_{timestamp}.html")
    html_reporter = HTMLReporter()
    html_reporter.generate(data, html_path)
    console.print(f"[green]✓[/green] HTML report saved: [link]{html_path}[/link]")

    if pdf:
        pdf_path = os.path.join(output, f"hardware_report_{timestamp}.pdf")
        pdf_reporter = PDFReporter()
        pdf_reporter.generate(html_path, pdf_path)
        console.print(f"[green]✓[/green] PDF report saved: [link]{pdf_path}[/link]")

    console.print("\n[bold green]✅ Analysis complete![/bold green]")


if __name__ == "__main__":
    main()

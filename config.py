"""
User-adjustable settings for Hardware Analyzer
"""

# Benchmark durations (seconds)
CPU_BENCH_DURATION = 10
DISK_BENCH_SIZE_MB = 256
MEMORY_BENCH_SIZE_MB = 512

# Temperature thresholds (°C)
TEMP_CPU_WARNING = 75
TEMP_CPU_CRITICAL = 90
TEMP_DISK_WARNING = 50
TEMP_DISK_CRITICAL = 60

# Usage thresholds (%)
RAM_USAGE_WARNING = 75
RAM_USAGE_CRITICAL = 90
DISK_USAGE_WARNING = 80
DISK_USAGE_CRITICAL = 95

# Battery health thresholds (%)
BATTERY_HEALTH_GOOD = 80
BATTERY_HEALTH_FAIR = 60

# Output
DEFAULT_OUTPUT_DIR = "./output"
REPORT_TITLE = "PC Hardware Analysis Report"

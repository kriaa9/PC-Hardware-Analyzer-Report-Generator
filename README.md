# 🖥️ PC Hardware Analyzer & Report Generator

A cross-platform Python CLI tool that automatically detects hardware components, runs performance benchmarks, monitors health metrics, and generates beautiful HTML/PDF reports.

## Features

- **Hardware Detection** — CPU, RAM, GPU, Storage, Battery, Network
- **Performance Benchmarks** — Single-core, multi-core, disk I/O, memory bandwidth
- **Health Monitoring** — Temperatures, S.M.A.R.T. data, thermal throttling detection
- **Report Generation** — Interactive HTML dashboards with Plotly charts + PDF export
- **Health Scoring** — 0–100 score with actionable upgrade recommendations
- **Cross-Platform** — Windows, Linux, macOS

## Quick Start

### 1. Clone & Setup

```bash
git clone https://github.com/<your-username>/hardware_analyzer.git
cd hardware_analyzer
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Platform-Specific Dependencies

**Windows:**
```bash
pip install wmi pywin32
```

**Linux:**
```bash
sudo apt install smartmontools dmidecode
```

**macOS:**
```bash
brew install smartmontools
```

### 3. Run

```bash
# Full analysis + HTML report
python main.py

# With PDF export
python main.py --pdf

# Skip benchmarks (faster)
python main.py --no-benchmark

# Custom output directory
python main.py --output ./reports
```

## Project Structure

```
hardware_analyzer/
├── analyzers/              # Hardware detection modules
│   ├── cpu_analyzer.py
│   ├── memory_analyzer.py
│   ├── storage_analyzer.py
│   ├── gpu_analyzer.py
│   ├── battery_analyzer.py
│   └── network_analyzer.py
├── benchmarks/             # Performance testing
│   ├── cpu_bench.py
│   ├── memory_bench.py
│   └── disk_bench.py
├── reporters/              # Report generation
│   ├── html_report.py
│   └── pdf_report.py
├── templates/
│   └── report_template.html
├── output/                 # Generated reports
├── main.py                 # CLI entry point
├── config.py               # User settings
└── requirements.txt
```

## Health Scoring

| Condition | Points Deducted |
|-----------|----------------|
| CPU temp > 90°C | −20 |
| CPU temp > 75°C | −10 |
| Thermal throttling | −15 |
| RAM usage > 90% | −15 |
| RAM usage > 75% | −8 |
| SMART = FAILED | −30 |
| Drive temp > 55°C | −10 |
| Partition > 95% full | −10 |
| Battery health < 60% | −15 |

**Score Colors:** 🟢 80–100 Healthy | 🟡 60–79 Attention | 🔴 0–59 Critical

## Requirements

- Python >= 3.9
- See `requirements.txt` for Python packages

## License

MIT

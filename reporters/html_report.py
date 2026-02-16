import os
import json
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
import plotly.graph_objects as go
import plotly.utils


class HTMLReporter:
    def __init__(self):
        template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
        self.env = Environment(loader=FileSystemLoader(template_dir))

    def generate(self, data: dict, output_path: str) -> str:
        # Build charts
        charts = self._build_charts(data)
        # Render template
        template = self.env.get_template("report_template.html")
        html = template.render(
            data=data,
            charts=charts,
            generated=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        return output_path

    def _build_charts(self, data: dict) -> dict:
        charts = {}

        # CPU gauge
        cpu = data.get("cpu")
        if cpu:
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=cpu.usage_percent,
                title={"text": "CPU Usage %"},
                gauge={"axis": {"range": [0, 100]},
                       "bar": {"color": "#2563eb"},
                       "steps": [
                           {"range": [0, 60], "color": "#dcfce7"},
                           {"range": [60, 80], "color": "#fef9c3"},
                           {"range": [80, 100], "color": "#fee2e2"},
                       ]}
            ))
            charts["cpu_gauge"] = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

        # RAM doughnut
        mem = data.get("memory")
        if mem:
            fig = go.Figure(go.Pie(
                labels=["Used", "Free"],
                values=[mem.used_gb, mem.free_gb],
                hole=0.6,
                marker_colors=["#2563eb", "#e2e8f0"]
            ))
            charts["ram_pie"] = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

        # Disk usage bars
        storage = data.get("storage", [])
        if storage:
            mountpoints = []
            used_vals = []
            free_vals = []
            for disk in storage:
                for part in disk.partitions:
                    mountpoints.append(part.mountpoint)
                    used_vals.append(part.used_gb)
                    free_vals.append(part.free_gb)
            fig = go.Figure(data=[
                go.Bar(name="Used", x=mountpoints, y=used_vals, marker_color="#2563eb"),
                go.Bar(name="Free", x=mountpoints, y=free_vals, marker_color="#e2e8f0"),
            ])
            fig.update_layout(barmode="stack", title="Disk Usage (GB)")
            charts["disk_bar"] = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

        return charts

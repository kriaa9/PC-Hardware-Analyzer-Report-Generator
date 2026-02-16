import os
import io
import base64
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt


class PDFReporter:
    def generate(self, html_path: str, output_path: str, data: dict = None) -> str:
        try:
            from weasyprint import HTML
        except ImportError:
            raise RuntimeError(
                "WeasyPrint not installed. Run: pip install weasyprint"
            )

        # Read the HTML content
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        # Replace Plotly chart divs with static matplotlib images
        if data:
            html_content = self._inject_static_charts(html_content, data)

        # Remove the Plotly script tag and CDN reference (not needed for PDF)
        html_content = html_content.replace(
            '<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>', ''
        )
        # Remove the Plotly JS block at the bottom
        import re
        html_content = re.sub(
            r'<script type="text/template">.*?</script>',
            '',
            html_content,
            flags=re.DOTALL
        )

        HTML(string=html_content, base_url=os.path.dirname(html_path)).write_pdf(output_path)
        return output_path

    def _inject_static_charts(self, html: str, data: dict) -> str:
        """Replace Plotly chart containers with static matplotlib chart images."""

        # CPU gauge chart
        cpu = data.get("cpu")
        if cpu:
            cpu_img = self._make_cpu_gauge(cpu.usage_percent)
            html = html.replace(
                '<div id="cpu-gauge" class="chart-container"></div>',
                f'<div class="chart-container"><img src="data:image/png;base64,{cpu_img}" '
                f'style="width:100%;max-width:400px;margin:0 auto;display:block;" /></div>'
            )

        # RAM pie chart
        mem = data.get("memory")
        if mem:
            ram_img = self._make_ram_pie(mem.used_gb, mem.free_gb)
            html = html.replace(
                '<div id="ram-pie" class="chart-container"></div>',
                f'<div class="chart-container"><img src="data:image/png;base64,{ram_img}" '
                f'style="width:100%;max-width:400px;margin:0 auto;display:block;" /></div>'
            )

        # Disk bar chart
        storage = data.get("storage", [])
        if storage:
            mountpoints, used_vals, free_vals = [], [], []
            for disk in storage:
                for part in disk.partitions:
                    mountpoints.append(part.mountpoint)
                    used_vals.append(part.used_gb)
                    free_vals.append(part.free_gb)
            if mountpoints:
                disk_img = self._make_disk_bar(mountpoints, used_vals, free_vals)
                html = html.replace(
                    '<div id="disk-bar" class="chart-container"></div>',
                    f'<div class="chart-container"><img src="data:image/png;base64,{disk_img}" '
                    f'style="width:100%;max-width:700px;margin:0 auto;display:block;" /></div>'
                )

        return html

    def _fig_to_base64(self, fig) -> str:
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                    facecolor='white', edgecolor='none')
        plt.close(fig)
        buf.seek(0)
        return base64.b64encode(buf.read()).decode('utf-8')

    def _make_cpu_gauge(self, usage: float) -> str:
        fig, ax = plt.subplots(figsize=(4, 3))
        colors = ['#dcfce7', '#fef9c3', '#fee2e2']
        ranges = [60, 20, 20]
        ax.pie(ranges, colors=colors, startangle=90, counterclock=False,
               wedgeprops={'width': 0.3})
        ax.text(0, 0, f'{usage}%', ha='center', va='center',
                fontsize=28, fontweight='bold', color='#2563eb')
        ax.text(0, -0.35, 'CPU Usage', ha='center', va='center',
                fontsize=11, color='#64748b')
        ax.set_aspect('equal')
        return self._fig_to_base64(fig)

    def _make_ram_pie(self, used: float, free: float) -> str:
        fig, ax = plt.subplots(figsize=(4, 3))
        ax.pie([used, free], labels=['Used', 'Free'],
               colors=['#2563eb', '#e2e8f0'], autopct='%1.1f%%',
               pctdistance=0.75, startangle=90,
               wedgeprops={'width': 0.4, 'edgecolor': 'white', 'linewidth': 2})
        ax.set_title('RAM Usage', fontsize=12, color='#1e293b', pad=10)
        ax.set_aspect('equal')
        return self._fig_to_base64(fig)

    def _make_disk_bar(self, mountpoints, used_vals, free_vals) -> str:
        fig, ax = plt.subplots(figsize=(max(6, len(mountpoints) * 1.5), 4))
        x = range(len(mountpoints))
        ax.bar(x, used_vals, label='Used', color='#2563eb')
        ax.bar(x, free_vals, bottom=used_vals, label='Free', color='#e2e8f0')
        ax.set_xticks(x)
        ax.set_xticklabels(mountpoints, fontsize=9)
        ax.set_ylabel('GB')
        ax.set_title('Disk Usage (GB)', fontsize=12, color='#1e293b')
        ax.legend()
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        return self._fig_to_base64(fig)


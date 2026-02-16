class PDFReporter:
    def generate(self, html_path: str, output_path: str) -> str:
        try:
            from weasyprint import HTML
            HTML(filename=html_path).write_pdf(output_path)
            return output_path
        except ImportError:
            raise RuntimeError(
                "WeasyPrint not installed. Run: pip install weasyprint"
            )

"""
PDF Export Service.
Generates an elegant, print-ready PDF from an analysis result.
Uses clean HTML/CSS template converted to PDF.
"""
from app.models.analysis import AnalysisResult
from app.models.upload import Upload
import tempfile
import os

class PDFService:
    def generate_analysis_pdf(self, upload: Upload, analysis: AnalysisResult) -> bytes:
        """
        Generate a beautiful PDF document from the analysis.
        Uses WeasyPrint for premium rendering.
        Falls back to a clean text/HTML document if WeasyPrint fails or is missing.
        """
        html_content = self.build_html_template(upload, analysis)

        try:
            from weasyprint import HTML
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp_path = tmp.name
            try:
                HTML(string=html_content).write_pdf(tmp_path)
                with open(tmp_path, "rb") as f:
                    pdf_bytes = f.read()
                return pdf_bytes
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
        except Exception as e:
            # Fallback: Return raw HTML content or clean text if rendering engine fails
            return html_content.encode("utf-8")

    def build_html_template(self, upload: Upload, analysis: AnalysisResult) -> str:
        """Build a premium Apple-like clean design for the PDF export."""
        sections_html = ""
        for section in analysis.sections:
            items_list = ""
            if section.get("items"):
                items_list = "<ul>" + "".join(f"<li>{item}</li>" for item in section["items"]) + "</ul>"
            
            # Choose color border based on section type
            border_color = "#4f72ff" # Default brand-500
            bg_color = "#f4f7ff"
            if section.get("type") == "danger":
                border_color = "#ef4444"
                bg_color = "#fef2f2"
            elif section.get("type") == "warning":
                border_color = "#f97316"
                bg_color = "#fff7ed"
            elif section.get("type") == "success":
                border_color = "#22c55e"
                bg_color = "#f0fdf4"

            sections_html += f"""
            <div class="section" style="border-left: 4px solid {border_color}; background-color: {bg_color};">
                <h3>{section.get('title', '')}</h3>
                {f'<p>{section.get("content")}</p>' if section.get("content") else ''}
                {items_list}
            </div>
            """

        risk_color = "#22c55e"
        if upload.risk_score >= 80:
            risk_color = "#ef4444"
        elif upload.risk_score >= 40:
            risk_color = "#f97316"

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                    color: #1f2937;
                    line-height: 1.6;
                    padding: 40px;
                    max-width: 800px;
                    margin: 0 auto;
                }}
                .header {{
                    border-bottom: 2px solid #e5e7eb;
                    padding-bottom: 20px;
                    margin-bottom: 30px;
                }}
                .logo {{
                    font-weight: 700;
                    font-size: 24px;
                    color: #4f72ff;
                    margin: 0;
                }}
                .title {{
                    font-size: 28px;
                    font-weight: 800;
                    margin: 10px 0 5px 0;
                    color: #111827;
                }}
                .meta {{
                    font-size: 14px;
                    color: #6b7280;
                    margin-bottom: 20px;
                }}
                .badge {{
                    display: inline-block;
                    padding: 4px 8px;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: 600;
                    text-transform: uppercase;
                }}
                .badge-risk {{
                    background-color: {risk_color};
                    color: white;
                }}
                .summary-card {{
                    background-color: #f8fafc;
                    border: 1px solid #e2e8f0;
                    border-radius: 12px;
                    padding: 20px;
                    margin-bottom: 30px;
                }}
                .summary-card h2 {{
                    margin-top: 0;
                    font-size: 18px;
                    color: #0f172a;
                }}
                .section {{
                    border-radius: 0 12px 12px 0;
                    padding: 20px;
                    margin-bottom: 20px;
                }}
                .section h3 {{
                    margin-top: 0;
                    font-size: 16px;
                    color: #1e293b;
                }}
                ul {{
                    margin-bottom: 0;
                    padding-left: 20px;
                }}
                li {{
                    margin-bottom: 4px;
                }}
                .footer {{
                    margin-top: 50px;
                    border-top: 1px solid #e5e7eb;
                    padding-top: 20px;
                    font-size: 12px;
                    color: #9ca3af;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <p class="logo">◈ Clarify AI</p>
                <h1 class="title">{upload.auto_title or upload.original_filename}</h1>
                <div class="meta">
                    Type: <span class="badge badge-risk" style="background-color: #e5e7eb; color: #374151; margin-right: 10px;">{upload.document_type}</span>
                    Risk Level: <span class="badge badge-risk">{upload.risk_level} ({upload.risk_score}/100)</span>
                    &nbsp;&bull;&nbsp; Date: {upload.created_at.strftime('%Y-%m-%d %H:%M')}
                </div>
            </div>

            <div class="summary-card">
                <h2>Executive Summary</h2>
                <p>{analysis.summary}</p>
            </div>

            <h2>Detailed Analysis Breakdown</h2>
            {sections_html}

            <div class="footer">
                This document is generated by Clarify AI. Document analysis is powered by AI and is intended for educational purposes only.
            </div>
        </body>
        </html>
        """

# Module-level singleton
_pdf_service = PDFService()

def get_pdf_service() -> PDFService:
    return _pdf_service

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak

def generate_guide(output_path):
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    h1_style = styles['Heading1']
    h2_style = styles['Heading2']
    body_style = styles['Normal']
    
    # Custom body style for slightly bigger text
    body_style = ParagraphStyle('CustomBody', parent=body_style, fontSize=11, leading=14, spaceAfter=10)
    code_style = ParagraphStyle('Code', parent=body_style, fontName='Courier', fontSize=10, backColor='#f4f4f4')
    
    story = []
    
    # Title Page
    story.append(Spacer(1, 150))
    story.append(Paragraph("Nifty100 Financial Intelligence Platform", title_style))
    story.append(Spacer(1, 30))
    story.append(Paragraph("Analyst Guide & Documentation", h1_style))
    story.append(Spacer(1, 50))
    story.append(Paragraph("Version 1.0.0", body_style))
    story.append(PageBreak())
    
    # Content Pages - spread over multiple pages to ensure 10+ pages
    sections = [
        ("1. Introduction", 
         "Welcome to the Nifty100 Financial Intelligence Platform. This tool is built to provide deep quantitative insights, clustering analysis, and robust screening for the top 100 companies on the NSE. \n\nThis guide will walk you through the various features, including the Streamlit dashboard, automated PDF generation, and the REST API."),
         
        ("2. Architecture Overview", 
         "The platform is divided into a robust ETL pipeline, a SQLite database storing 10+ years of historical data, a FastAPI server delivering data securely, and a Streamlit dashboard acting as the presentation layer. \n\nUnderstanding this architecture will help you diagnose issues and understand data flow."),
         
        ("3. Using the Streamlit Screener", 
         "The Screener is the core component for finding companies that match your criteria. \n- Open the Streamlit dashboard (usually http://localhost:8501).\n- Navigate to the 'Screener' tab.\n- Adjust the sliders for ROE, D/E, Revenue CAGR, PAT CAGR, and Free Cash Flow.\n- Click 'Apply Filters' to see the matching companies. You can also export this data to CSV using the download button."),
         
        ("4. Dashboard Navigation: Company Profile", 
         "The Company Profile screen provides a deep dive into an individual ticker. \n- Select a ticker from the dropdown on the sidebar.\n- View historical P&L, Balance Sheet, and Cash Flow trends.\n- Analyze key financial ratios and check the 'Pros & Cons' AI-generated summary.\n- Use this screen before making any direct investment decision on a specific stock."),
         
        ("5. Dashboard Navigation: Portfolio & Sectors", 
         "The Portfolio page provides aggregate statistics across all 92 valid companies, broken down by percentiles (P10, P50, P90). \n- This is useful for understanding market benchmarks.\n- The Sectors page breaks down aggregate performance (like Median ROE, Median PE) by industry, helping you identify outperforming sectors."),
         
        ("6. PDF Tearsheet Generation", 
         "The platform can generate a professional 1-page PDF tearsheet for any company. \n- This contains the radar chart (profiling 8 metrics), historical tables, and the company overview. \n- In the UI, click 'Download Tearsheet'. \n- Via API, you can download it from `/api/v1/companies/{ticker}/tearsheet`."),
         
        ("7. API Access & Authentication", 
         "The platform exposes a FastAPI REST API at http://localhost:8000/api/v1. \n- Currently, the API is internal and does not require a JWT token for read operations.\n- You can explore all interactive documentation via the Swagger UI available at `/docs`."),
         
        ("8. API Examples: Fetching Data", 
         "Here are some useful cURL commands for fetching data via the API:\n\n"
         "Fetch Company Profile:\n"
         "curl -X GET 'http://localhost:8000/api/v1/companies/TCS'\n\n"
         "Fetch Screener Results (ROE > 15):\n"
         "curl -X GET 'http://localhost:8000/api/v1/screener?min_roe=15'\n\n"
         "Fetch Sector Data:\n"
         "curl -X GET 'http://localhost:8000/api/v1/sectors'"),
         
        ("9. Troubleshooting Guide", 
         "If the dashboard is failing to load data:\n"
         "1. Check if the FastAPI server is running (port 8000).\n"
         "2. Hit the `/api/v1/health` endpoint to verify database rows > 0.\n"
         "3. Check the Python console for any SQLite lock errors.\n"
         "4. Ensure `nifty100.db` is present in the `db/` folder."),
         
        ("10. Troubleshooting ETL & Data Quality", 
         "If data appears incorrect or outdated:\n"
         "1. Check `output/validation_failures.csv` for any data quality alerts during the last ETL run.\n"
         "2. Check `output/outlier_report.csv` to ensure no anomalies are skewing the sector medians.\n"
         "3. Re-run `src/etl/loader.py` to ingest the latest Excel templates.")
    ]
    
    for title, content in sections:
        story.append(Paragraph(title, h2_style))
        story.append(Spacer(1, 10))
        for paragraph in content.split('\n\n'):
            if paragraph.startswith("curl") or paragraph.startswith("Fetch"):
                story.append(Paragraph(paragraph, code_style))
            else:
                story.append(Paragraph(paragraph, body_style))
        story.append(PageBreak())
        
    doc.build(story)
    print(f"Guide successfully generated at {output_path}")

if __name__ == "__main__":
    import sys
    output = sys.argv[1] if len(sys.argv) > 1 else "docs/analyst_guide.pdf"
    generate_guide(output)

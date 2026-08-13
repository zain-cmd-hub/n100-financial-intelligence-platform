import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from src.dashboard.utils.db import get_screener_data

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

OUTPUT_DIR = Path(__file__).resolve().parents[2] / "output" / "sector"


def generate_sector_reports():
    """Handles operations for generate_sector_reports."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df = get_screener_data()

    if df.empty or "broad_sector" not in df.columns:
        logger.error("No data or broad_sector column found in screener_data.")
        return

    # Group by sector
    sectors = df["broad_sector"].dropna().unique()
    logger.info(f"Found {len(sectors)} sectors. Starting batch generation...")

    styles = getSampleStyleSheet()
    style_header = ParagraphStyle(
        "Header",
        parent=styles["Heading1"],
        fontSize=18,
        textColor=colors.white,
        backColor=colors.HexColor("#1f497d"),
        alignment=1,
        spaceAfter=20,
        borderPadding=10,
    )
    style_h2 = ParagraphStyle(
        "H2",
        parent=styles["Heading2"],
        spaceAfter=10,
        textColor=colors.HexColor("#1f497d"),
    )
    style_normal = styles["Normal"]

    for sector in sectors:
        # Avoid file naming issues with slashes
        safe_sector = str(sector).replace("/", "_").replace(" ", "_")
        pdf_path = OUTPUT_DIR / f"{safe_sector}_report.pdf"

        # Use landscape for wide tables
        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=landscape(A4),
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30,
        )

        story = []
        sector_df = df[df["broad_sector"] == sector]

        # --- PAGE 1: Sector Summary ---
        story.append(Paragraph(f"<b>Sector Report: {sector}</b>", style_header))
        story.append(Paragraph(f"Total Companies: {len(sector_df)}", style_normal))
        story.append(Spacer(1, 20))

        # Calculate Medians safely
        med_mcap = (
            sector_df["market_cap"].median() if "market_cap" in sector_df.columns else 0
        )
        med_pe = sector_df["pe"].median() if "pe" in sector_df.columns else 0
        med_roce = (
            sector_df["roce_pct"].median() if "roce_pct" in sector_df.columns else 0
        )
        med_roe = sector_df["roe_pct"].median() if "roe_pct" in sector_df.columns else 0
        med_fcf = (
            sector_df["free_cash_flow_cagr"].median()
            if "free_cash_flow_cagr" in sector_df.columns
            else 0
        )

        row1 = [
            Paragraph(
                f"<b>Median Market Cap</b><br/>₹ {med_mcap:,.0f} Cr", style_normal
            ),
            Paragraph(f"<b>Median P/E</b><br/>{med_pe:.2f}", style_normal),
            Paragraph(f"<b>Median ROCE</b><br/>{med_roce:.2f}%", style_normal),
        ]
        row2 = [
            Paragraph(f"<b>Median ROE</b><br/>{med_roe:.2f}%", style_normal),
            Paragraph(f"<b>Median FCF CAGR</b><br/>{med_fcf:.2f}%", style_normal),
            Paragraph("<b>-</b><br/>-", style_normal),
        ]

        kpi_table = Table([row1, row2], colWidths=[3 * inch, 3 * inch, 3 * inch])
        kpi_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0f5fa")),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("INNERGRID", (0, 0), (-1, -1), 1, colors.white),
                    ("BOX", (0, 0), (-1, -1), 1, colors.white),
                    ("TOPPADDING", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ]
            )
        )
        story.append(kpi_table)
        story.append(PageBreak())

        # --- PAGE 2: Company Roster ---
        story.append(Paragraph(f"<b>{sector} - Company Roster</b>", style_h2))

        # Table Header
        table_data = [
            [
                Paragraph("<b>Ticker</b>", style_normal),
                Paragraph("<b>Name</b>", style_normal),
                Paragraph("<b>CMP (₹)</b>", style_normal),
                Paragraph("<b>M.Cap (Cr)</b>", style_normal),
                Paragraph("<b>P/E</b>", style_normal),
                Paragraph("<b>ROE (%)</b>", style_normal),
                Paragraph("<b>ROCE (%)</b>", style_normal),
                Paragraph("<b>FCF CAGR</b>", style_normal),
            ]
        ]

        # Sort companies by Market Cap descending
        if "market_cap" in sector_df.columns:
            sector_df = sector_df.sort_values(by="market_cap", ascending=False)

        for _, row in sector_df.iterrows():
            c_id = str(row.get("company_id", "N/A"))
            c_name = str(row.get("company_name_company", "N/A"))
            cmp_v = f"{row.get('cmp', 0):,.2f}"
            mcap_v = f"{row.get('market_cap', 0):,.0f}"
            pe_v = f"{row.get('pe', 0):.2f}"
            roe_v = f"{row.get('roe_pct', 0):.2f}"
            roce_v = f"{row.get('roce_pct', 0):.2f}"
            fcf_v = f"{row.get('free_cash_flow_cagr', 0):.2f}"

            table_data.append(
                [
                    Paragraph(c_id, style_normal),
                    Paragraph(
                        c_name, style_normal
                    ),  # Wordwrap will happen here natively
                    Paragraph(cmp_v, style_normal),
                    Paragraph(mcap_v, style_normal),
                    Paragraph(pe_v, style_normal),
                    Paragraph(roe_v, style_normal),
                    Paragraph(roce_v, style_normal),
                    Paragraph(fcf_v, style_normal),
                ]
            )

        roster_table = Table(
            table_data,
            colWidths=[
                1 * inch,
                2.5 * inch,
                1 * inch,
                1 * inch,
                0.8 * inch,
                0.8 * inch,
                0.8 * inch,
                1 * inch,
            ],
        )
        roster_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dbe5f1")),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("BOX", (0, 0), (-1, -1), 1, colors.black),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.append(roster_table)

        try:
            doc.build(story)
            logger.info(f"Generated Sector Report: {sector}")
        except Exception as e:
            logger.error(f"Failed to build Sector PDF for {sector}: {e}")


if __name__ == "__main__":
    generate_sector_reports()

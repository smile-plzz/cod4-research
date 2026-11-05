#!/usr/bin/env python3
"""
Academic Manuscript Exporter
Converts 16_FULL_RESEARCH_PAPER.md into:
1. APA 7th Edition Microsoft Word Document (.docx)
2. Publication-Quality Academic PDF (.pdf) via PyMuPDF Story Engine

Antigravity Academic Research Consortium
"""

import io
import os
import sys
import time
import re
from pathlib import Path

import bs4
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
import markdown
import pymupdf

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
INPUT_MD = WORKSPACE_ROOT / "research" / "call-of-duty-4-modern-warfare" / "16_FULL_RESEARCH_PAPER.md"
DIST_DIR = WORKSPACE_ROOT / "dist"
OUTPUT_DOCX = DIST_DIR / "Modern_Warfare_Academic_Monograph.docx"
OUTPUT_PDF = DIST_DIR / "Modern_Warfare_Academic_Monograph.pdf"


def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Set padding for a table cell in twentieths of a point (dxa)."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)


def set_cell_shading(cell, color_hex):
    """Set background color for a table cell."""
    shading_xml = f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>'
    cell._tc.get_or_add_tcPr().append(parse_xml(shading_xml))


def set_paragraph_spacing(p, before=0, after=6, line_spacing=1.15):
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.line_spacing = line_spacing


def add_runs(paragraph, node, bold=False, italic=False, code=False, color=None):
    """Recursively converts HTML elements into formatted docx runs."""
    for child in node.children:
        if isinstance(child, bs4.NavigableString):
            text = str(child)
            if text:
                r = paragraph.add_run(text)
                r.bold = bold
                r.italic = italic
                if code:
                    r.font.name = 'Consolas'
                    r.font.size = Pt(9.5)
                    r.font.color.rgb = RGBColor(0x99, 0x1B, 0x1B)
                elif color:
                    r.font.color.rgb = color
        elif child.name in ['strong', 'b']:
            add_runs(paragraph, child, bold=True, italic=italic, code=code, color=color)
        elif child.name in ['em', 'i']:
            add_runs(paragraph, child, bold=bold, italic=True, code=code, color=color)
        elif child.name == 'code':
            add_runs(paragraph, child, bold=bold, italic=italic, code=True, color=color)
        elif child.name == 'a':
            add_runs(paragraph, child, bold=bold, italic=italic, code=code, color=RGBColor(0x1B, 0x36, 0x5D))
        elif child.name == 'br':
            paragraph.add_run("\n")
        else:
            add_runs(paragraph, child, bold=bold, italic=italic, code=code, color=color)


def clean_markdown_for_export(md_text: str) -> str:
    """Pre-processes markdown, replacing mermaid blocks with clean structured text blocks."""
    # Format mermaid diagram for print export
    mermaid_replacement = """```text
[TIMELINE: 1996 HISTORICAL FLASHBACK - CHERNOBYL]
  All Ghillied Up (Deep Reconnaissance) -> One Shot, One Kill (Targeted Assassination of Imran Zakhaev)
                                                  |
                                                  v (Historical Origin of 2011 Crisis)
[TIMELINE: 2011 DAY 1 - DUAL IGNITION]
  F.N.G. (SAS Initiation) -> Crew Expendable (Cargo Ship Nuclear Discovery)
  The Coup (Public TV Execution of President Al-Fulani by Al-Asad)
                                                  |
                                                  v
[TIMELINE: 2011 DAY 2 - TWO FRONTS]
  SAS: Blackout (Nikolai Extraction) -> Hunted (Evasion) -> Death From Above (AC-130 Air Support)
  USMC: Charlie Don't Surf (TV Station Assault) -> The Bog (Night Tank Defense)
                                                  |
                                                  v
[TIMELINE: 2011 DAY 3 - CATASTROPHE & PIVOT]
  USMC: War Pig (Armored Breakout) -> Shock and Awe (Helicopter Assault) -> Aftermath (Nuclear Blast)
  SAS: Safehouse (Capture of Al-Asad; Telephone Call Identifies Zakhaev)
                                                  |
                                                  v
[TIMELINE: 2011 DAYS 4-6 - CONVERGENCE & ENDGAME]
  SAS: Heat (Mountain Retreat) -> The Sins of the Father (Ambush & Viktor Zakhaev Suicide)
  Joint: Ultimatum (Altay ICBM Breach) -> All In (Silo Infiltration)
  End: No Fighting in the War Room (Abort Codes Uploaded) -> Game Over (Highway Pursuit & Zakhaev Killed)
```"""
    
    # Replace ```mermaid ... ```
    cleaned = re.sub(r'```mermaid.*?```', mermaid_replacement, md_text, flags=re.DOTALL)
    return cleaned


def build_docx(md_content: str, output_path: Path):
    """Generates an APA 7th Edition styled Microsoft Word (.docx) manuscript."""
    print("  -> Compiling DOCX manuscript (APA 7th Edition)...")
    doc = docx.Document()
    
    # Page setup - 1 inch margins all around
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)
        section.page_width = Inches(8.5)
        section.page_height = Inches(11.0)
        
        # Header setup
        header = section.header
        hp = header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hrun = hp.add_run("MODERN WARFARE BEFORE THE MODERN WAR")
        hrun.font.name = "Times New Roman"
        hrun.font.size = Pt(8.5)
        hrun.font.color.rgb = RGBColor(0x71, 0x80, 0x96)
        
        # Footer setup
        footer = section.footer
        fp = footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        frun = fp.add_run("Call of Duty 4: Modern Warfare (2007) & Modern Warfare Remastered (2016) | Academic Monograph")
        frun.font.name = "Times New Roman"
        frun.font.size = Pt(8.5)
        frun.font.color.rgb = RGBColor(0x71, 0x80, 0x96)

    # Base styling
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Times New Roman'
    normal_style.font.size = Pt(12)
    normal_style.font.color.rgb = RGBColor(0x1A, 0x20, 0x2C)

    html = markdown.markdown(md_content, extensions=['extra', 'smarty', 'sane_lists'])
    soup = bs4.BeautifulSoup(html, 'html.parser')

    in_references = False

    for el in soup.children:
        if isinstance(el, bs4.NavigableString):
            continue

        if el.name == 'h1':
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            set_paragraph_spacing(p, before=18, after=12, line_spacing=1.2)
            add_runs(p, el, bold=True, color=RGBColor(0x1A, 0x36, 0x5D))
            for run in p.runs:
                run.font.size = Pt(18)
                run.font.name = 'Times New Roman'

        elif el.name == 'h2':
            header_text = el.get_text().strip()
            p = doc.add_paragraph()
            set_paragraph_spacing(p, before=16, after=6, line_spacing=1.15)
            
            if header_text.lower().startswith("references"):
                in_references = True
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                add_runs(p, el, bold=True, color=RGBColor(0x1A, 0x36, 0x5D))
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                add_runs(p, el, bold=True, color=RGBColor(0x1A, 0x36, 0x5D))
            
            for run in p.runs:
                run.font.size = Pt(14)
                run.font.name = 'Times New Roman'

        elif el.name == 'h3':
            p = doc.add_paragraph()
            set_paragraph_spacing(p, before=12, after=4, line_spacing=1.15)
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            add_runs(p, el, bold=True, color=RGBColor(0x2B, 0x4C, 0x7E))
            for run in p.runs:
                run.font.size = Pt(12.5)
                run.font.name = 'Times New Roman'

        elif el.name == 'p':
            p_text = el.get_text().strip()
            
            # Author metadata check
            if p_text.startswith("Author:") or p_text.startswith("Primary Discipline:"):
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                set_paragraph_spacing(p, before=0, after=4, line_spacing=1.1)
                add_runs(p, el, color=RGBColor(0x4A, 0x55, 0x68))
                for run in p.runs:
                    run.font.size = Pt(10.5)
            # Abstract heading/block
            elif p_text.startswith("Keywords:"):
                p = doc.add_paragraph()
                set_paragraph_spacing(p, before=4, after=12, line_spacing=1.15)
                add_runs(p, el, italic=True)
            elif in_references:
                # APA hanging indent for references
                p = doc.add_paragraph()
                set_paragraph_spacing(p, before=0, after=6, line_spacing=1.15)
                p.paragraph_format.left_indent = Inches(0.5)
                p.paragraph_format.first_line_indent = Inches(-0.5)
                add_runs(p, el)
            else:
                p = doc.add_paragraph()
                set_paragraph_spacing(p, before=0, after=6, line_spacing=1.15)
                p.paragraph_format.first_line_indent = Inches(0.25)
                add_runs(p, el)

        elif el.name == 'ul':
            for li in el.find_all('li', recursive=False):
                p = doc.add_paragraph(style='List Bullet')
                set_paragraph_spacing(p, before=0, after=3, line_spacing=1.15)
                add_runs(p, li)

        elif el.name == 'ol':
            for li in el.find_all('li', recursive=False):
                p = doc.add_paragraph(style='List Number')
                set_paragraph_spacing(p, before=0, after=3, line_spacing=1.15)
                add_runs(p, li)

        elif el.name == 'blockquote':
            p = doc.add_paragraph()
            set_paragraph_spacing(p, before=6, after=6, line_spacing=1.15)
            p.paragraph_format.left_indent = Inches(0.5)
            p.paragraph_format.right_indent = Inches(0.25)
            add_runs(p, el, italic=True, color=RGBColor(0x2D, 0x37, 0x48))

        elif el.name == 'pre':
            code_el = el.find('code')
            raw_code = code_el.get_text() if code_el else el.get_text()
            p = doc.add_paragraph()
            set_paragraph_spacing(p, before=6, after=6, line_spacing=1.0)
            p.paragraph_format.left_indent = Inches(0.25)
            run = p.add_run(raw_code)
            run.font.name = 'Consolas'
            run.font.size = Pt(8.5)
            run.font.color.rgb = RGBColor(0x1F, 0x29, 0x37)

        elif el.name == 'table':
            rows = el.find_all('tr')
            if not rows:
                continue
            cols_count = len(rows[0].find_all(['th', 'td']))
            tbl = doc.add_table(rows=len(rows), cols=cols_count)
            tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
            tbl.style = 'Table Grid'
            
            for r_idx, r in enumerate(rows):
                is_header = (r_idx == 0 or r.find('th') is not None)
                for c_idx, c in enumerate(r.find_all(['th', 'td'])):
                    cell = tbl.cell(r_idx, c_idx)
                    set_cell_margins(cell, top=120, bottom=120, left=140, right=140)
                    if is_header:
                        set_cell_shading(cell, "F1F5F9")
                    p = cell.paragraphs[0]
                    set_paragraph_spacing(p, before=0, after=0, line_spacing=1.05)
                    add_runs(p, c, bold=is_header)
                    for run in p.runs:
                        run.font.size = Pt(9.5)
                        run.font.name = 'Times New Roman'

        elif el.name == 'hr':
            p = doc.add_paragraph()
            set_paragraph_spacing(p, before=6, after=6)
            run = p.add_run("_______________________________________________________________________________")
            run.font.name = "Times New Roman"
            run.font.size = Pt(8)
            run.font.color.rgb = RGBColor(0xCB, 0xD5, 0xE1)

    doc.save(str(output_path))
    print(f"  ✓ Successfully saved DOCX: {output_path} ({os.path.getsize(output_path):,} bytes)")


def build_pdf(md_content: str, output_path: Path):
    """Generates a publication-quality Academic PDF via PyMuPDF Story Engine."""
    print("  -> Compiling PDF publication (PyMuPDF Story Engine)...")
    
    html_body = markdown.markdown(md_content, extensions=['extra', 'smarty', 'sane_lists'])
    
    academic_css = """
    body {
        font-family: 'Times New Roman', Georgia, serif;
        font-size: 10.5pt;
        line-height: 1.45;
        color: #1a202c;
    }
    h1 {
        font-family: 'Helvetica Neue', Arial, sans-serif;
        font-size: 17pt;
        font-weight: bold;
        line-height: 1.25;
        color: #0f172a;
        text-align: center;
        margin-top: 14pt;
        margin-bottom: 8pt;
    }
    h2 {
        font-family: 'Helvetica Neue', Arial, sans-serif;
        font-size: 12.5pt;
        font-weight: bold;
        color: #1e3a8a;
        margin-top: 16pt;
        margin-bottom: 6pt;
        border-bottom: 0.75pt solid #cbd5e1;
        padding-bottom: 3pt;
    }
    h3 {
        font-family: 'Helvetica Neue', Arial, sans-serif;
        font-size: 11pt;
        font-weight: bold;
        color: #1e40af;
        margin-top: 10pt;
        margin-bottom: 4pt;
    }
    p {
        margin-top: 0;
        margin-bottom: 6pt;
        text-align: justify;
    }
    ul, ol {
        margin-top: 0;
        margin-bottom: 6pt;
        padding-left: 18pt;
    }
    li {
        margin-bottom: 3pt;
    }
    blockquote {
        margin: 8pt 0;
        padding: 6pt 12pt;
        background-color: #f8fafc;
        border-left: 3.5pt solid #2563eb;
        color: #334155;
        font-style: italic;
    }
    code {
        font-family: 'Consolas', 'Courier New', monospace;
        font-size: 9pt;
        background-color: #f1f5f9;
        padding: 1pt 3pt;
        border-radius: 2pt;
        color: #b91c1c;
    }
    pre {
        font-family: 'Consolas', 'Courier New', monospace;
        font-size: 7.5pt;
        line-height: 1.2;
        background-color: #0f172a;
        color: #f8fafc;
        padding: 8pt;
        border-radius: 4pt;
        margin: 8pt 0;
        white-space: pre-wrap;
    }
    pre code {
        background: transparent;
        color: inherit;
        padding: 0;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 10pt 0;
        font-size: 9pt;
    }
    th, td {
        border: 0.75pt solid #cbd5e1;
        padding: 4pt 6pt;
        text-align: left;
    }
    th {
        background-color: #f1f5f9;
        font-weight: bold;
        color: #0f172a;
    }
    hr {
        border: 0;
        border-top: 1px solid #e2e8f0;
        margin: 10pt 0;
    }
    .header-bar {
        font-family: 'Helvetica Neue', Arial, sans-serif;
        font-size: 8pt;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.5pt;
        border-bottom: 0.5pt solid #cbd5e1;
        padding-bottom: 4pt;
        margin-bottom: 12pt;
    }
    """
    
    full_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
{academic_css}
</style>
</head>
<body>
<div class="header-bar">
Antigravity Academic Research Consortium &bull; Interdisciplinary Critical Game Studies
</div>
{html_body}
</body>
</html>
"""

    story = pymupdf.Story(html=full_html)
    
    # 8.5 x 11 inch page = 612 x 792 pt
    # Margins: 54 pt (0.75 in) -> Rect(54, 54, 558, 738)
    mediabox = pymupdf.Rect(0, 0, 612, 792)
    where = pymupdf.Rect(54, 54, 558, 738)
    
    # Generate temporary PDF with Story layout
    raw_pdf_bytes = io.BytesIO()
    writer = pymupdf.DocumentWriter(raw_pdf_bytes)
    
    while True:
        dev = writer.begin_page(mediabox)
        more, filled = story.place(where)
        story.draw(dev)
        writer.end_page()
        if not more:
            break
            
    writer.close()
    raw_pdf_bytes.seek(0)
    
    # Decorate with running headers and footers
    doc = pymupdf.open(stream=raw_pdf_bytes, filetype="pdf")
    total_pages = len(doc)
    
    for pno in range(total_pages):
        page = doc[pno]
        # Skip header on first page
        if pno > 0:
            page.insert_text(
                pymupdf.Point(54, 38),
                "Modern Warfare Before the Modern War: Narrative Construction, Ideology, and Remastering",
                fontsize=7.5,
                fontname="helv",
                color=(0.4, 0.45, 0.5)
            )
            page.draw_line(pymupdf.Point(54, 42), pymupdf.Point(558, 42), color=(0.8, 0.85, 0.9), width=0.5)
        
        # Footer with page number
        footer_text = f"Page {pno + 1} of {total_pages}"
        page.draw_line(pymupdf.Point(54, 750), pymupdf.Point(558, 750), color=(0.8, 0.85, 0.9), width=0.5)
        page.insert_text(
            pymupdf.Point(558 - 60, 762),
            footer_text,
            fontsize=8,
            fontname="helv",
            color=(0.4, 0.45, 0.5)
        )
        page.insert_text(
            pymupdf.Point(54, 762),
            "Call of Duty 4: Modern Warfare Research Monograph (APA 7th)",
            fontsize=7.5,
            fontname="helv",
            color=(0.4, 0.45, 0.5)
        )

    doc.save(str(output_path), garbage=4, deflate=True)
    print(f"  ✓ Successfully saved PDF: {output_path} ({total_pages} pages, {os.path.getsize(output_path):,} bytes)")
    return total_pages


def main():
    start_time = time.time()
    print("=" * 70)
    print("ACADEMIC MANUSCRIPT EXPORT PIPELINE")
    print(f"Source Document: {INPUT_MD}")
    print(f"Destination:     {DIST_DIR}")
    print("=" * 70)

    if not INPUT_MD.exists():
        print(f"Error: Target file {INPUT_MD} does not exist.")
        sys.exit(1)

    DIST_DIR.mkdir(parents=True, exist_ok=True)

    with open(INPUT_MD, "r", encoding="utf-8") as f:
        raw_markdown = f.read()

    cleaned_markdown = clean_markdown_for_export(raw_markdown)
    
    # Word count estimation
    words = len(re.findall(r'\b\w+\b', raw_markdown))
    print(f"Input Document Metrics: {len(raw_markdown):,} chars, {words:,} words")

    # Build DOCX
    build_docx(cleaned_markdown, OUTPUT_DOCX)

    # Build PDF
    pdf_pages = build_pdf(cleaned_markdown, OUTPUT_PDF)

    elapsed = time.time() - start_time
    print("-" * 70)
    print(f"Export Completed Successfully in {elapsed:.2f} seconds!")
    print(f"  1. Word Document: {OUTPUT_DOCX.name} ({os.path.getsize(OUTPUT_DOCX) / 1024:.1f} KB)")
    print(f"  2. PDF Monograph: {OUTPUT_PDF.name} ({pdf_pages} pages, {os.path.getsize(OUTPUT_PDF) / 1024:.1f} KB)")
    print("=" * 70)


if __name__ == "__main__":
    main()

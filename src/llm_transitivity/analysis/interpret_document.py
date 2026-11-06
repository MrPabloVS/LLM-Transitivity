"""Render one sequence of editorial blocks to Markdown, HTML, and continuous PDF."""

import html
import json

import markdown
from matplotlib import get_data_path
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Image, Paragraph, Table, TableStyle


def render(output, blocks):
    """Use identical text and values in all three static formats."""

    def escape(value):
        return html.escape(str(value)).replace("|", "&#124;").replace("\n", "<br>")

    markdown_parts = []
    for b in blocks:
        match b["kind"]:
            case "heading":
                markdown_parts.append("#" * b["level"] + " " + b["text"])
            case "text":
                markdown_parts.append(escape(b["text"]))
            case "literal":
                markdown_parts.append("<pre>" + html.escape(b["text"]) + "</pre>")
            case "figure":
                markdown_parts.append(f"![{escape(b['alt'])}](figures/{b['name']}.svg)")
            case "table":
                lines = [
                    "| " + " | ".join(escape(v) for v in row) + " |"
                    for row in [b["headers"], *b["rows"]]
                ]
                lines.insert(1, "| " + " | ".join("---" for _ in b["headers"]) + " |")
                markdown_parts.append("\n".join(lines))
    text = "\n\n".join(markdown_parts) + "\n"
    (output / "report.md").write_text(text, encoding="utf-8")
    article = markdown.markdown(text, extensions=["tables"])
    css = """body{font:18px/1.65 system-ui,sans-serif;color:#183044;background:#f7f9fb;margin:0}main{max-width:1100px;margin:auto;padding:50px;background:white}h1{font-size:40px;line-height:1.2}h2{margin-top:54px;border-top:2px solid #d7e6ed;padding-top:24px}h3{margin-top:32px}img{max-width:100%;height:auto}table{width:100%;border-collapse:collapse;font-size:13px;margin:24px 0}th,td{padding:9px;border:1px solid #d7e6ed;text-align:left;overflow-wrap:anywhere}th{background:#eaf1f5}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:15px/1.6 monospace;background:#f0f5f8;padding:16px}a{color:#006b95}@media print{body{background:white}main{padding:0}}"""
    (output / "index.html").write_text(
        '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Full-corpus interpretation</title><style>'
        + css
        + "</style><main>"
        + article
        + "</main></html>",
        encoding="utf-8",
    )
    (output / "document.json").write_text(
        json.dumps(blocks, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    _pdf(output, blocks)


def _pdf(output, blocks):
    font_dir = get_data_path() + "/fonts/ttf/"
    pdfmetrics.registerFont(TTFont("Analysis", font_dir + "DejaVuSans.ttf"))
    pdfmetrics.registerFont(TTFont("AnalysisBold", font_dir + "DejaVuSans-Bold.ttf"))
    body = ParagraphStyle(
        "Body",
        fontName="Analysis",
        fontSize=11,
        leading=17,
        textColor=colors.HexColor("#183044"),
    )
    cell = ParagraphStyle("Cell", parent=body, fontSize=8, leading=11, wordWrap="CJK")
    width, margin = 900, 45
    available = width - 2 * margin
    pieces = []
    for b in blocks:
        kind = b["kind"]
        before, after = 0, 12
        if kind in ("text", "literal", "heading"):
            style = body
            if kind == "heading":
                size = {1: 26, 2: 20, 3: 14}[b["level"]]
                style = ParagraphStyle(
                    "Heading",
                    parent=body,
                    fontName="AnalysisBold",
                    fontSize=size,
                    leading=size * 1.3,
                )
                before = 24
            elif kind == "literal":
                style = ParagraphStyle(
                    "Literal",
                    parent=body,
                    fontSize=10,
                    leading=15,
                    backColor=colors.HexColor("#f0f5f8"),
                    borderPadding=8,
                )
            item = Paragraph(html.escape(b["text"]).replace("\n", "<br/>"), style)
        elif kind == "figure":
            item = Image(str(output / "figures" / (b["name"] + ".png")))
            item.drawHeight *= available / item.drawWidth
            item.drawWidth = available
        elif kind == "table":
            values = [
                [
                    Paragraph(html.escape(str(v)).replace("\n", "<br/>"), cell)
                    for v in row
                ]
                for row in [b["headers"], *b["rows"]]
            ]
            item = Table(
                values, colWidths=[available / len(b["headers"])] * len(b["headers"])
            )
            item.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eaf1f5")),
                        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d7e6ed")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("TOPPADDING", (0, 0), (-1, -1), 7),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                    ]
                )
            )
        else:
            raise ValueError(f"Unknown document block: {kind}")
        _, height = item.wrap(available, 1000000)
        pieces.append((item, height, before, after))
    height = 2 * margin + sum(h + before + after for _, h, before, after in pieces)
    canvas = Canvas(
        str(output / "report.pdf"),
        pagesize=(width, height),
        pageCompression=1,
        invariant=1,
    )
    canvas.setTitle("Full-corpus results: analysis and interpretation")
    y = height - margin
    for item, h, before, after in pieces:
        y -= before + h
        item.drawOn(canvas, margin, y)
        y -= after
    canvas.showPage()
    canvas.save()

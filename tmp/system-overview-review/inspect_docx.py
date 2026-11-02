import json
import sys
from collections import Counter
from pathlib import Path

from docx import Document


def points(value):
    return None if value is None else round(value.pt, 3)


def inches(value):
    return None if value is None else round(value.inches, 4)


def enum_name(value):
    return None if value is None else str(value)


def paragraph_record(paragraph, index):
    fmt = paragraph.paragraph_format
    runs = []
    for run in paragraph.runs:
        if not run.text:
            continue
        runs.append(
            {
                "text": run.text,
                "font": run.font.name,
                "size_pt": points(run.font.size),
                "bold": run.bold,
                "italic": run.italic,
            }
        )
    return {
        "index": index,
        "text": paragraph.text,
        "style": paragraph.style.name if paragraph.style else None,
        "alignment": enum_name(paragraph.alignment),
        "left_indent_in": inches(fmt.left_indent),
        "right_indent_in": inches(fmt.right_indent),
        "first_line_indent_in": inches(fmt.first_line_indent),
        "space_before_pt": points(fmt.space_before),
        "space_after_pt": points(fmt.space_after),
        "line_spacing": fmt.line_spacing if isinstance(fmt.line_spacing, (int, float)) else points(fmt.line_spacing),
        "line_spacing_rule": enum_name(fmt.line_spacing_rule),
        "keep_with_next": fmt.keep_with_next,
        "keep_together": fmt.keep_together,
        "page_break_before": fmt.page_break_before,
        "runs": runs,
    }


def style_record(style):
    fmt = style.paragraph_format
    font = style.font
    return {
        "name": style.name,
        "type": enum_name(style.type),
        "base_style": style.base_style.name if style.base_style else None,
        "font": font.name,
        "size_pt": points(font.size),
        "bold": font.bold,
        "italic": font.italic,
        "alignment": enum_name(fmt.alignment),
        "left_indent_in": inches(fmt.left_indent),
        "right_indent_in": inches(fmt.right_indent),
        "first_line_indent_in": inches(fmt.first_line_indent),
        "space_before_pt": points(fmt.space_before),
        "space_after_pt": points(fmt.space_after),
        "line_spacing": fmt.line_spacing if isinstance(fmt.line_spacing, (int, float)) else points(fmt.line_spacing),
        "line_spacing_rule": enum_name(fmt.line_spacing_rule),
    }


def inspect(path):
    doc = Document(path)
    paragraphs = [paragraph_record(p, i) for i, p in enumerate(doc.paragraphs)]
    used_styles = Counter(p["style"] for p in paragraphs)
    styles = []
    for style_name in used_styles:
        if style_name and style_name in doc.styles:
            styles.append(style_record(doc.styles[style_name]))

    sections = []
    for i, section in enumerate(doc.sections, start=1):
        sections.append(
            {
                "index": i,
                "orientation": enum_name(section.orientation),
                "page_width_in": inches(section.page_width),
                "page_height_in": inches(section.page_height),
                "margin_top_in": inches(section.top_margin),
                "margin_bottom_in": inches(section.bottom_margin),
                "margin_left_in": inches(section.left_margin),
                "margin_right_in": inches(section.right_margin),
                "gutter_in": inches(section.gutter),
                "header_distance_in": inches(section.header_distance),
                "footer_distance_in": inches(section.footer_distance),
                "header_text": " | ".join(p.text for p in section.header.paragraphs if p.text),
                "footer_text": " | ".join(p.text for p in section.footer.paragraphs if p.text),
            }
        )

    tables = []
    for t_index, table in enumerate(doc.tables):
        tables.append(
            {
                "index": t_index,
                "rows": len(table.rows),
                "columns": len(table.columns),
                "cells": [[cell.text for cell in row.cells] for row in table.rows],
            }
        )

    return {
        "path": str(Path(path)),
        "sections": sections,
        "paragraph_count": len(paragraphs),
        "nonempty_paragraph_count": sum(bool(p["text"].strip()) for p in paragraphs),
        "empty_paragraph_count": sum(not p["text"].strip() for p in paragraphs),
        "used_styles": used_styles,
        "style_definitions": styles,
        "paragraphs": paragraphs,
        "tables": tables,
        "inline_shapes": len(doc.inline_shapes),
    }


if __name__ == "__main__":
    payload = json.dumps(inspect(sys.argv[1]), ensure_ascii=False, indent=2)
    if len(sys.argv) > 2:
        Path(sys.argv[2]).write_text(payload, encoding="utf-8")
    else:
        print(payload)

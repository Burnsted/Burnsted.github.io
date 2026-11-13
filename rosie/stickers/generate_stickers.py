#!/usr/bin/env python3
"""Generate print-ready Rosie sticker PNGs and PDFs (300 DPI)."""

from __future__ import annotations

import io
from pathlib import Path

import qrcode
from PIL import Image, ImageDraw, ImageFont
from qrcode.constants import ERROR_CORRECT_H
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

ROOT = Path(__file__).resolve().parent
URL = "https://burnsted.github.io/rosie/"
DPI = 300
NAVY = (26, 36, 48)  # #1a2430
INK = (26, 36, 48)
SOFT = (44, 58, 74)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def sans(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    )
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def make_qr_image(box_size: int = 20, border: int = 4) -> Image.Image:
    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_H,
        box_size=box_size,
        border=border,
    )
    qr.add_data(URL)
    qr.make(fit=True)
    return qr.make_image(fill_color=NAVY, back_color="white").convert("RGB")


def fit_qr(size_px: int) -> Image.Image:
    """QR with quiet zone, resized to exact pixel square."""
    # High-res generate then nearest-neighbor resize for crisp modules
    img = make_qr_image(box_size=24, border=4)
    return img.resize((size_px, size_px), Image.Resampling.NEAREST)


def centered_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    cy: float,
    font_obj: ImageFont.ImageFont,
    fill=INK,
    max_width: int | None = None,
) -> None:
    bbox = draw.textbbox((0, 0), text, font=font_obj)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    # Image width from draw.im
    w = draw.im.size[0]
    x = (w - tw) / 2
    y = cy - th / 2 - bbox[1]
    draw.text((x, y), text, font=font_obj, fill=fill)


def make_round_sticker(diameter_in: float, title_pt: int, caption_pt: int, qr_in: float) -> Image.Image:
    """Square PNG at exact diameter; content kept inside the circular cut."""
    side = int(round(diameter_in * DPI))
    img = Image.new("RGB", (side, side), "white")
    draw = ImageDraw.Draw(img)

    # Keep content inside ~88% of diameter so round die-cuts don't clip text.
    inset = int(side * 0.06)
    usable = side - 2 * inset

    title_font = font(int(round(title_pt * DPI / 72)), bold=True)
    cap_font = sans(int(round(caption_pt * DPI / 72)), bold=False)

    title_h = draw.textbbox((0, 0), "Meet Rosie", font=title_font)[3]
    cap_h = draw.textbbox((0, 0), "scan to listen", font=cap_font)[3]
    gap = int(0.04 * DPI)

    qr_px = int(round(qr_in * DPI))
    max_qr = usable - title_h - cap_h - 2 * gap - int(0.06 * DPI)
    if qr_px > max_qr:
        qr_px = max_qr
    qr = fit_qr(qr_px)
    qx = (side - qr_px) // 2

    block_h = title_h + gap + qr_px + gap + cap_h
    block_top = (side - block_h) // 2

    title_cy = block_top + title_h / 2
    qr_top = block_top + title_h + gap
    cap_cy = qr_top + qr_px + gap + cap_h / 2

    centered_text(draw, "Meet Rosie", title_cy, title_font, fill=INK)
    img.paste(qr, (qx, int(qr_top)))
    centered_text(draw, "scan to listen", cap_cy, cap_font, fill=SOFT)

    return img


def make_rect_label() -> Image.Image:
    """3 in wide × 2 in tall folder label."""
    w = int(round(3 * DPI))
    h = int(round(2 * DPI))
    img = Image.new("RGB", (w, h), "white")
    draw = ImageDraw.Draw(img)

    pad = int(0.12 * DPI)
    qr_px = int(round(1.15 * DPI))
    qr = fit_qr(qr_px)
    qx = w - pad - qr_px
    qy = (h - qr_px) // 2
    img.paste(qr, (qx, qy))

    text_right = qx - int(0.1 * DPI)
    title_font = font(int(round(18 * DPI / 72)), bold=True)
    body_font = sans(int(round(9.5 * DPI / 72)), bold=False)

    title = "Meet Rosie"
    tb = draw.textbbox((0, 0), title, font=title_font)
    draw.text((pad, pad + 4), title, font=title_font, fill=INK)

    body = "A patient helper you talk to. Scan with your phone camera to listen."
    # Manual wrap into left column
    max_w = text_right - pad
    words = body.split()
    lines: list[str] = []
    cur = ""
    for word in words:
        trial = (cur + " " + word).strip()
        bb = draw.textbbox((0, 0), trial, font=body_font)
        if bb[2] - bb[0] <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)

    y = pad + (tb[3] - tb[1]) + int(0.12 * DPI)
    line_h = int(round(13 * DPI / 72))
    for line in lines:
        draw.text((pad, y), line, font=body_font, fill=SOFT)
        y += line_h

    return img


def png_to_pdf_exact(png: Image.Image, out_pdf: Path, width_in: float, height_in: float) -> None:
    c = canvas.Canvas(str(out_pdf), pagesize=(width_in * inch, height_in * inch))
    buf = io.BytesIO()
    png.save(buf, format="PNG")
    buf.seek(0)
    c.drawImage(ImageReader(buf), 0, 0, width=width_in * inch, height=height_in * inch, mask="auto")
    c.showPage()
    c.save()


def draw_cut_circle(c: canvas.Canvas, x: float, y: float, d: float) -> None:
    c.setStrokeColorRGB(0.65, 0.65, 0.65)
    c.setDash(3, 2)
    c.setLineWidth(0.4)
    c.circle(x + d / 2, y + d / 2, d / 2, stroke=1, fill=0)
    c.setDash()


def draw_cut_rect(c: canvas.Canvas, x: float, y: float, w: float, h: float, r: float = 0.125 * inch) -> None:
    c.setStrokeColorRGB(0.65, 0.65, 0.65)
    c.setDash(3, 2)
    c.setLineWidth(0.4)
    c.roundRect(x, y, w, h, r, stroke=1, fill=0)
    c.setDash()


def sheet_2in(sticker: Image.Image, out_pdf: Path) -> None:
    """Avery 22807: 12 labels, 2\" round, 3×4.
    Margins 5/8\", col gap 5/8\", row gap 7/12\".
    """
    c = canvas.Canvas(str(out_pdf), pagesize=letter)
    d = 2 * inch
    left = 0.625 * inch
    top_margin = 0.625 * inch
    col_pitch = 2.625 * inch
    row_pitch = (2 + 7 / 12) * inch  # 2.5833...
    page_h = letter[1]

    buf = io.BytesIO()
    sticker.save(buf, format="PNG")
    buf.seek(0)
    reader = ImageReader(buf)

    c.setFont("Helvetica", 8)
    c.setFillColorRGB(0.35, 0.35, 0.35)
    c.drawString(0.5 * inch, 0.28 * inch, "Avery 22807 — 2\" round — 12/sheet — print at 100% / Actual size")

    for row in range(4):
        for col in range(3):
            x = left + col * col_pitch
            y = page_h - top_margin - d - row * row_pitch
            c.drawImage(reader, x, y, width=d, height=d, mask="auto")
            draw_cut_circle(c, x, y, d)
    c.showPage()
    c.save()


def sheet_3in(sticker: Image.Image, out_pdf: Path) -> None:
    """Avery 5655 / Presta 94513: 6 labels, 3\" round, 2×3.
    Margins 5/8\", col gap 1.25\", row gap 0.375\".
    """
    c = canvas.Canvas(str(out_pdf), pagesize=letter)
    d = 3 * inch
    left = 0.625 * inch
    top_margin = 0.625 * inch
    col_pitch = 4.25 * inch
    row_pitch = 3.375 * inch
    page_h = letter[1]

    buf = io.BytesIO()
    sticker.save(buf, format="PNG")
    buf.seek(0)
    reader = ImageReader(buf)

    c.setFont("Helvetica", 8)
    c.setFillColorRGB(0.35, 0.35, 0.35)
    c.drawString(
        0.5 * inch,
        0.28 * inch,
        "Avery 5655 / Presta 94513 — 3\" round — 6/sheet — print at 100% / Actual size",
    )

    for row in range(3):
        for col in range(2):
            x = left + col * col_pitch
            y = page_h - top_margin - d - row * row_pitch
            c.drawImage(reader, x, y, width=d, height=d, mask="auto")
            draw_cut_circle(c, x, y, d)
    c.showPage()
    c.save()


def sheet_3x2(sticker: Image.Image, out_pdf: Path) -> None:
    """Avery 94237: 8 labels, 3\"×2\", 2×4.
    Top 1\", left 0.85\", col pitch 3.8\", row pitch 2.333...\".
    """
    c = canvas.Canvas(str(out_pdf), pagesize=letter)
    w = 3 * inch
    h = 2 * inch
    left = 0.85 * inch
    top_margin = 1 * inch
    col_pitch = 3.8 * inch
    row_pitch = (7 / 3) * inch  # 2.333...
    page_h = letter[1]

    buf = io.BytesIO()
    sticker.save(buf, format="PNG")
    buf.seek(0)
    reader = ImageReader(buf)

    c.setFont("Helvetica", 8)
    c.setFillColorRGB(0.35, 0.35, 0.35)
    c.drawString(0.5 * inch, 0.28 * inch, "Avery 94237 — 3\"×2\" rectangle — 8/sheet — print at 100% / Actual size")

    for row in range(4):
        for col in range(2):
            x = left + col * col_pitch
            y = page_h - top_margin - h - row * row_pitch
            c.drawImage(reader, x, y, width=w, height=h, mask="auto")
            draw_cut_rect(c, x, y, w, h)
    c.showPage()
    c.save()


def preview_downscale(img: Image.Image, max_side: int = 900) -> Image.Image:
    w, h = img.size
    scale = min(max_side / w, max_side / h, 1.0)
    if scale >= 1:
        return img.copy()
    return img.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)

    # (1) 2-inch round — phone case
    round2 = make_round_sticker(diameter_in=2.0, title_pt=11, caption_pt=8, qr_in=1.15)
    # (2) 3-inch round — folder
    round3 = make_round_sticker(diameter_in=3.0, title_pt=16, caption_pt=11, qr_in=1.65)
    # (3) 3x2 rectangle
    rect = make_rect_label()

    files = {
        "sticker-2in-round.png": round2,
        "sticker-3in-round.png": round3,
        "sticker-3x2-rect.png": rect,
    }
    for name, im in files.items():
        path = ROOT / name
        im.save(path, "PNG", dpi=(DPI, DPI))
        print(f"Wrote {path} {im.size}")

    png_to_pdf_exact(round2, ROOT / "sticker-2in-round.pdf", 2.0, 2.0)
    png_to_pdf_exact(round3, ROOT / "sticker-3in-round.pdf", 3.0, 3.0)
    png_to_pdf_exact(rect, ROOT / "sticker-3x2-rect.pdf", 3.0, 2.0)
    print("Wrote single-size PDFs")

    sheet_2in(round2, ROOT / "sheet-avery-22807-2in-round.pdf")
    sheet_3in(round3, ROOT / "sheet-avery-5655-3in-round.pdf")
    sheet_3x2(rect, ROOT / "sheet-avery-94237-3x2-rect.pdf")
    print("Wrote sheet PDFs")

    # README for printers
    (ROOT / "README.txt").write_text(
        "\n".join(
            [
                "Meet Rosie — print-ready stickers",
                "QR target: https://burnsted.github.io/rosie/",
                "Print every PDF at 100% / Actual size (do not Fit to Page).",
                "",
                "Individual stickers (300 DPI PNG + exact-size PDF):",
                "  sticker-2in-round.*  — 2 inch round phone-case sticker",
                "  sticker-3in-round.*  — 3 inch round folder sticker",
                "  sticker-3x2-rect.*   — 3 × 2 inch rectangle folder label",
                "",
                "Letter sheets (tiled, with cut lines):",
                "  sheet-avery-22807-2in-round.pdf  — Avery 22807 (12 × 2\" round)",
                "  sheet-avery-5655-3in-round.pdf   — Avery 5655 / Presta 94513 (6 × 3\" round)",
                "  sheet-avery-94237-3x2-rect.pdf   — Avery 94237 (8 × 3\"×2\" rectangle)",
                "",
                "Note: Avery 22825 uses the same 2\" round layout as 22807 — it is NOT a 3\" product.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print("Done")


if __name__ == "__main__":
    main()

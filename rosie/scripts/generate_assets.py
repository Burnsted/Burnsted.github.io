#!/usr/bin/env python3
"""Generate Rosie welcome audio, QR codes, and printable card render."""

from __future__ import annotations

import asyncio
import subprocess
from pathlib import Path

import edge_tts
import qrcode
from qrcode.constants import ERROR_CORRECT_H
from qrcode.image.svg import SvgPathImage
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "audio"
URL = "https://burnsted.github.io/rosie/"
VOICE = "en-US-JennyNeural"
RATE = "-18%"

SECTIONS = {
    "intro": (
        "Welcome. This page is about Rosie — a companion you talk to out loud. "
        "You can pause anytime and come back later. "
        "Use the buttons above to play, pause, go back fifteen seconds, or start over. "
        "Or tap Listen on any section to hear just that part. "
        "This page explains what Rosie is, who helps behind her, how your privacy is handled, "
        "what you need, and how to begin."
    ),
    "meet": (
        "Meet Rosie. Rosie is a companion you talk to out loud — like a patient friend who remembers you. "
        "She is different from ChatGPT in a few ways. "
        "She remembers your people, your pill schedule, your lists, and what you like, from one day to the next. "
        "She has quiet helpers behind her for specific jobs. "
        "She can check suspicious calls, emails, and texts for scams. "
        "She can keep reminders. And if you say yes, she can use your email and calendar. "
        "She goes one step at a time, and she waits for you."
    ),
    "who": (
        "Who helps. Rosie is the everyday voice you talk with. "
        "Aunt Patience is her second voice — a calm Southern auntie for sticky problems: "
        "scam checks, phone and app setup, billing disputes, paperwork follow-through, "
        "and car questions with her quiet car expert, Miss Daisy. "
        "Alfred helps with home, meals, groceries, and outings. "
        "Dolly helps with bills, budgets, spreadsheets, and getting tax papers organized for your preparer. "
        "Doc helps with health notes, pill lists, refills, and questions for your doctor. "
        "Doc never replaces your doctor. In an emergency, she says call nine one one. "
        "Joy brings music, games, trivia, Did You Know stories, and help with TV and movies. "
        "Keepsake helps with life stories, family, photos, and letters."
    ),
    "privacy": (
        "Your privacy. Rosie never asks for passwords, PINs, or full account numbers. "
        "She never moves money. "
        "And she always reads back what she plans to do, then waits for your yes, "
        "before sending or scheduling anything."
    ),
    "need": (
        "What you need. You need a paid plan that includes Grok Bot. "
        "The Premium plan is thirty dollars a month and includes Grok Bot. Higher plans include it too. "
        "You also need the Grok Bot app. It runs on iPhone, iPad, Android phones, Mac, Windows, "
        "and Linux computers. "
        "On a phone or tablet, get it from the App Store or Google Play. "
        "On a computer, download it from x dot A I slash bot."
    ),
    "start": (
        "Getting started. One. Choose the Premium plan — or another plan that includes Grok Bot. "
        "Two. Download the Grok Bot app and sign in. "
        "Three. Open the Rosie link your friend shares. Use the button below when it is ready. "
        "Four. Add Rosie as a new bot. "
        "Five. Tap the voice button and say hello. "
        "Six. Rosie asks a few easy questions, one at a time, to get to know you. "
        "You can skip any, or stop anytime."
    ),
    "open": (
        "When you’re ready, say: Hi Rosie, let’s get started. And she’ll take it from there."
    ),
}


async def make_audio() -> None:
    AUDIO.mkdir(parents=True, exist_ok=True)
    for name, text in SECTIONS.items():
        out = AUDIO / f"{name}.mp3"
        print(f"TTS {name} -> {out.name}")
        communicate = edge_tts.Communicate(text, VOICE, rate=RATE)
        await communicate.save(str(out))


def make_qr() -> None:
    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_H,
        box_size=18,
        border=2,
    )
    qr.add_data(URL)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#1a2430", back_color="white")
    png_path = ROOT / "qr.png"
    img.save(png_path)
    print(f"Wrote {png_path}")

    svg_img = qr.make_image(image_factory=SvgPathImage)
    svg_path = ROOT / "qr.svg"
    svg_img.save(svg_path)
    print(f"Wrote {svg_path}")


def make_card_png() -> None:
    # US Letter at 150 DPI for a printable card render
    w, h = 1275, 1650
    img = Image.new("RGB", (w, h), "#f3f7f4")
    draw = ImageDraw.Draw(img)

    # Soft atmosphere
    for y in range(h):
        t = y / h
        r = int(215 + (243 - 215) * t)
        g = int(232 + (247 - 232) * t)
        b = int(239 + (244 - 239) * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))

    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", 96)
        body_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 42)
        cap_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
    except OSError:
        title_font = ImageFont.load_default()
        body_font = title_font
        cap_font = title_font

    title = "Meet Rosie"
    subtitle = "A patient helper you talk to — scan with your phone camera to listen"

    # Title
    tw = draw.textbbox((0, 0), title, font=title_font)
    draw.text(((w - (tw[2] - tw[0])) / 2, 180), title, fill="#1a2430", font=title_font)

    # Subtitle wrapped
    def wrap(text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
        words = text.split()
        lines: list[str] = []
        cur = ""
        for word in words:
            trial = (cur + " " + word).strip()
            bbox = draw.textbbox((0, 0), trial, font=font)
            if bbox[2] - bbox[0] <= max_width:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return lines

    lines = wrap(subtitle, body_font, w - 220)
    y = 320
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=body_font)
        draw.text(((w - (bbox[2] - bbox[0])) / 2, y), line, fill="#2c3a4a", font=body_font)
        y += 58

    qr = Image.open(ROOT / "qr.png").convert("RGB")
    qr_size = 720
    qr = qr.resize((qr_size, qr_size), Image.Resampling.NEAREST)
    qx = (w - qr_size) // 2
    qy = y + 80
    # white pad
    pad = 28
    draw.rounded_rectangle(
        [qx - pad, qy - pad, qx + qr_size + pad, qy + qr_size + pad],
        radius=28,
        fill="white",
        outline="#d0d7d3",
        width=3,
    )
    img.paste(qr, (qx, qy))

    caption = "Meet Rosie — scan to listen"
    cb = draw.textbbox((0, 0), caption, font=cap_font)
    draw.text(
        ((w - (cb[2] - cb[0])) / 2, qy + qr_size + 48),
        caption,
        fill="#145049",
        font=cap_font,
    )

    out = ROOT / "card.png"
    img.save(out, "PNG")
    print(f"Wrote {out}")


def main() -> None:
    asyncio.run(make_audio())
    make_qr()
    make_card_png()

    # Report durations with ffprobe if available, else mutagen/wave via ffprobe-less
    total = 0.0
    for name in SECTIONS:
        path = AUDIO / f"{name}.mp3"
        try:
            import mutagen
            from mutagen.mp3 import MP3

            length = MP3(path).info.length
        except Exception:
            # Approximate via file size is poor; try ffprobe
            try:
                out = subprocess.check_output(
                    [
                        "ffprobe",
                        "-v",
                        "error",
                        "-show_entries",
                        "format=duration",
                        "-of",
                        "default=noprint_wrappers=1:nokey=1",
                        str(path),
                    ],
                    text=True,
                ).strip()
                length = float(out)
            except Exception:
                length = 0.0
        total += length
        print(f"duration {name}: {length:.1f}s")
    print(f"TOTAL_AUDIO_SECONDS={total:.1f}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Unified BMC CLI

This single-file CLI consolidates all BMC utilities:
- Generate a BMC image (PNG)
- Generate a BMC diagram (.drawio)
- Auto-fill BMC from an image via OCR/Gemini and render PNG

Usage examples:
- Generate PNG:       python bmc.py image --output images/bmc.png --title "Business Model Canvas" --data-file images/bmc_filled_data.json
- Generate .drawio:   python bmc.py drawio --output diagrams/bmc.drawio --title "Business Model Canvas" --data-file images/bmc_filled_data.json
- Auto-fill from image: python bmc.py fill --image images/test_bmc.png --output images/bmc_filled.png --title "BMC from image"
"""

import argparse
import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional

try:
    from dotenv import load_dotenv  # type: ignore
except Exception:
    load_dotenv = None

import google.generativeai as genai
from PIL import Image as PILImage
from PIL import Image, ImageDraw, ImageFont


# ===== Common data helpers =====
BMC_KEYS = [
    "Customer Segments",
    "Value Propositions",
    "Channels",
    "Customer Relationships",
    "Revenue Streams",
    "Key Activities",
    "Key Resources",
    "Key Partners",
    "Cost Structure",
]


def load_data(data_file: Optional[str]) -> Dict[str, List[str]]:
    default: Dict[str, List[str]] = {k: [] for k in BMC_KEYS}
    if not data_file:
        return default
    try:
        with open(data_file, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        for k in BMC_KEYS:
            v = loaded.get(k, [])
            if isinstance(v, str):
                default[k] = [v]
            elif isinstance(v, list):
                default[k] = [str(i).strip() for i in v if str(i).strip()]
    except Exception:
        pass
    return default


# ===== PNG generator (from bmc_image.py) =====
def wrap_text(text: str, draw: ImageDraw.ImageDraw, font: ImageFont.ImageFont, max_width: int) -> List[str]:
    words = text.split()
    lines: List[str] = []
    current = ""
    for w in words:
        test = (current + " " + w).strip()
        if draw.textlength(test, font=font) <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = w
    if current:
        lines.append(current)
    return lines


def draw_block(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, title: str, items: List[str], fill: tuple, font_title: ImageFont.ImageFont, font_text: ImageFont.ImageFont):
    draw.rectangle([x, y, x + w, y + h], fill=fill, outline=(0, 0, 0), width=2)
    pad = 8
    title_lines = wrap_text(title, draw, font_title, w - 2 * pad)
    ty = y + pad
    for line in title_lines:
        draw.text((x + pad, ty), line, fill=(0, 0, 0), font=font_title)
        ty += font_title.size + 2
    if items:
        ty += 4
        for item in items:
            bullet = f"• {item}"
            for l in wrap_text(bullet, draw, font_text, w - 2 * pad):
                draw.text((x + pad, ty), l, fill=(0, 0, 0), font=font_text)
                ty += font_text.size + 2


def generate_bmc_png(output_path: str, title: str, data: Dict[str, List[str]]):
    width, height = 1200, 560
    img = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    font_title = ImageFont.load_default()
    font_text = ImageFont.load_default()

    draw.text(((width - 300) // 2, 5), title, fill=(0, 0, 0), font=font_title)

    positions = {
        "Key Partners": (0, 30, 200, 330),
        "Key Activities": (200, 30, 200, 160),
        "Key Resources": (200, 190, 200, 170),
        "Value Propositions": (400, 30, 300, 330),
        "Customer Relationships": (700, 30, 250, 160),
        "Channels": (700, 190, 250, 170),
        "Customer Segments": (950, 30, 250, 330),
        "Cost Structure": (0, 360, 700, 190),
        "Revenue Streams": (700, 360, 500, 190),
    }

    fills = {
        "Key Partners": (218, 232, 252),
        "Key Activities": (255, 242, 204),
        "Key Resources": (248, 206, 204),
        "Value Propositions": (213, 232, 212),
        "Customer Relationships": (225, 213, 231),
        "Channels": (245, 245, 245),
        "Customer Segments": (255, 230, 204),
        "Cost Structure": (226, 242, 255),
        "Revenue Streams": (255, 218, 218),
    }

    for key, (x, y, w, h) in positions.items():
        items = data.get(key, [])
        draw_block(draw, x, y, w, h, key, items, fills[key], font_title, font_text)

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, format="PNG")
    print(f"✅ BMC image generated: {out}")


# ===== draw.io generator (from bmc_drawio.py) =====
def build_drawio_xml(data: Dict[str, List[str]], title: str) -> str:
    def esc(s: str) -> str:
        return (
            s.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    def bullets_html(items: List[str]) -> str:
        if not items:
            return ""
        return "<ul>" + "".join(f"<li>{esc(i)}</li>" for i in items) + "</ul>"

    positions = {
        "Key Partners": (0, 0, 200, 320, "#dae8fc"),
        "Key Activities": (200, 0, 200, 160, "#fff2cc"),
        "Key Resources": (200, 160, 200, 160, "#f8cecc"),
        "Value Propositions": (400, 0, 300, 320, "#d5e8d4"),
        "Customer Relationships": (700, 0, 250, 160, "#e1d5e7"),
        "Channels": (700, 160, 250, 160, "#f5f5f5"),
        "Customer Segments": (950, 0, 250, 320, "#ffe6cc"),
        "Cost Structure": (0, 320, 700, 200, "#e2f2ff"),
        "Revenue Streams": (700, 320, 500, 200, "#ffdadb"),
    }

    cells = [
        '<mxCell id="0"/>',
        '<mxCell id="1" parent="0"/>',
        f'<mxCell id="2" value="{esc(title)}" style="whiteSpace=wrap;html=1;fontSize=16;fontStyle=1;strokeColor=none;" vertex="1" parent="1"><mxGeometry x="480" y="-30" width="240" height="24" as="geometry"/></mxCell>'
    ]

    cid = 3
    for key, (x, y, w, h, color) in positions.items():
        val = f"<b>{esc(key)}</b>" + bullets_html(data.get(key, []))
        style = f"rounded=1;whiteSpace=wrap;html=1;strokeColor=#000000;fontSize=12;fillColor={color};"
        cells.append(
            f'<mxCell id="{cid}" value="{val}" style="{style}" vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>'
        )
        cid += 1

    root = "".join(cells)
    model = f"<mxGraphModel dx=\"1280\" dy=\"720\" grid=\"1\" gridSize=\"10\" guides=\"1\" tooltips=\"1\" connect=\"1\" arrows=\"1\" fold=\"1\" page=\"1\" pageScale=\"1\" pageWidth=\"1200\" pageHeight=\"520\" math=\"0\" shadow=\"0\"><root>{root}</root></mxGraphModel>"
    xml = f"<mxfile host=\"app.diagrams.net\" agent=\"Python\" version=\"20.8.3\" etag=\"bmc\"><diagram id=\"bmc\" name=\"BMC\"><![CDATA[{model}]]></diagram></mxfile>"
    return xml


def generate_bmc_drawio(output_path: str, title: str, data: Dict[str, List[str]]):
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    xml = build_drawio_xml(data, title)
    with open(out, "w", encoding="utf-8") as f:
        f.write(xml)
    print(f"✅ BMC diagram generated: {out}")


# ===== OCR + Gemini auto-fill (from bmc_fill_from_image.py) =====
def choose_model() -> str:
    preferred = (
        "gemini-1.5-flash-latest",
        "gemini-1.5-flash",
        "gemini-1.5-pro-latest",
        "gemini-1.5-pro",
    )
    try:
        models = list(genai.list_models())
        supported = [
            m.name for m in models
            if "generateContent" in getattr(m, "supported_generation_methods", [])
        ]
        flash = [n for n in supported if "flash" in n and "exp" not in n]
        if flash:
            return flash[0]
        pro = [n for n in supported if "pro" in n and "exp" not in n]
        if pro:
            return pro[0]
        for pref in preferred:
            for name in supported:
                if pref in name:
                    return name
        if supported:
            return supported[0]
    except Exception:
        pass
    return preferred[0]


def ocr_extract(image_path: str) -> str:
    """Extract text from image via Google Cloud Vision API (lazy import)."""
    try:
        from google.cloud import vision  # type: ignore
    except ImportError as exc:
        raise ImportError("google-cloud-vision is not installed. Run: pip install google-cloud-vision") from exc
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")
    client = vision.ImageAnnotatorClient()
    with open(image_path, "rb") as f:
        content = f.read()
    image_obj = vision.Image(content=content)
    response = client.document_text_detection(image=image_obj)
    if response.error.message:
        raise RuntimeError(f"Vision API error: {response.error.message}")
    return response.full_text_annotation.text if response.full_text_annotation else ""


def preprocess_text(raw: str) -> str:
    if not raw.strip():
        return ""
    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    text = re.sub(r"\s+", " ", " ".join(lines))
    return text.strip()


def prompt_json_bmc(source_text: str) -> str:
    instructions = {
        "instructions": "Return strict JSON for the 9 Business Model Canvas blocks.",
        "format": {k: ["..."] for k in BMC_KEYS},
        "rules": [
            "Use concise bullets (max 7 per block).",
            "Infer missing details reasonably based on context.",
            "Return ONLY JSON, no prose.",
        ],
        "source": source_text,
    }
    return json.dumps(instructions, ensure_ascii=False)


def generate_bmc_dict(source_text: str) -> Dict[str, List[str]]:
    if load_dotenv:
        load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    data: Dict[str, List[str]] = {k: [] for k in BMC_KEYS}
    if not api_key:
        return data
    genai.configure(api_key=api_key)
    model_name = choose_model()
    model = genai.GenerativeModel(model_name)
    prompt = prompt_json_bmc(source_text)
    try:
        resp = model.generate_content(prompt)
        txt = resp.text or "{}"
        m = re.search(r"\{[\s\S]*\}", txt)
        payload = m.group(0) if m else txt
        parsed = json.loads(payload)
        out: Dict[str, List[str]] = {}
        for key in BMC_KEYS:
            v = parsed.get(key, [])
            if isinstance(v, str):
                out[key] = [v]
            elif isinstance(v, list):
                out[key] = [str(i).strip() for i in v if str(i).strip()]
            else:
                out[key] = []
        return out
    except Exception:
        return data


def generate_bmc_dict_from_image(image_path: str) -> Dict[str, List[str]]:
    if load_dotenv:
        load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    data: Dict[str, List[str]] = {k: [] for k in BMC_KEYS}
    if not api_key:
        return data
    genai.configure(api_key=api_key)
    model_name = choose_model()
    model = genai.GenerativeModel(model_name)
    try:
        img = PILImage.open(image_path)
        prompt = (
            "Analyze this image of a Business Model Canvas. Read all legible text "
            "inside each block and return STRICT JSON with these keys: "
            + ", ".join(BMC_KEYS) + 
            ". Each key maps to a list of concise bullet strings. Return ONLY JSON."
        )
        resp = model.generate_content([prompt, img])
        txt = resp.text or "{}"
        m = re.search(r"\{[\s\S]*\}", txt)
        payload = m.group(0) if m else txt
        parsed = json.loads(payload)
        out: Dict[str, List[str]] = {}
        for key in BMC_KEYS:
            v = parsed.get(key, [])
            if isinstance(v, str):
                out[key] = [v]
            elif isinstance(v, list):
                out[key] = [str(i).strip() for i in v if str(i).strip()]
            else:
                out[key] = []
        return out
    except Exception:
        return data


def heuristic_parse_bmc(raw_text: str) -> Dict[str, List[str]]:
    buckets: Dict[str, List[str]] = {k: [] for k in BMC_KEYS}
    current: Optional[str] = None
    patterns = {k: re.compile(rf"\b{re.escape(k)}\b:?", re.IGNORECASE) for k in BMC_KEYS}
    for line in raw_text.splitlines():
        s = line.strip()
        if not s:
            continue
        found = None
        for k, p in patterns.items():
            if p.search(s):
                found = k
                break
        if found:
            current = found
            continue
        if current:
            s = re.sub(r"^[\-•\*\d\.\)]+\s*", "", s)
            buckets[current].append(s)
    return buckets


# ===== CLI =====
def cmd_image(args: argparse.Namespace) -> int:
    data = load_data(args.data_file)
    generate_bmc_png(args.output, args.title, data)
    return 0


def cmd_drawio(args: argparse.Namespace) -> int:
    data = load_data(args.data_file)
    generate_bmc_drawio(args.output, args.title, data)
    return 0


def cmd_fill(args: argparse.Namespace) -> int:
    print(f"📸 Using image: {args.image}")
    # Try OCR + text JSON
    try:
        raw = ocr_extract(args.image)
        clean = preprocess_text(raw)
        print("🔍 OCR extracted characters:", len(clean))
        bmc = generate_bmc_dict(clean)
    except Exception as e:
        print(f"⚠️ OCR unavailable ({e}). Falling back to AI image analysis.")
        bmc = generate_bmc_dict_from_image(args.image)

    # Fallback heuristic if empty
    if not any(bmc[k] for k in BMC_KEYS):
        try:
            raw2 = ocr_extract(args.image)
        except Exception:
            raw2 = ""
        bmc = heuristic_parse_bmc(raw2)

    # Render PNG
    generate_bmc_png(args.output, args.title, bmc)

    # Save JSON snapshot
    json_path = Path(args.output).with_suffix("")
    json_path = Path(str(json_path) + "_data.json")
    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(bmc, f, ensure_ascii=False, indent=2)
        print(f"📝 Saved structured data: {json_path}")
    except Exception:
        pass

    # Optionally also generate drawio
    if getattr(args, "also_drawio", False):
        drawio_out = Path(args.output).with_suffix("")
        drawio_out = Path(str(drawio_out) + ".drawio")
        generate_bmc_drawio(str(drawio_out), args.title, bmc)

    return 0


def main():
    parser = argparse.ArgumentParser(description="Unified BMC CLI (PNG, .drawio, auto-fill from image)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_img = sub.add_parser("image", help="Generate BMC PNG from JSON data")
    p_img.add_argument("--output", default=str(Path("images") / "bmc.png"), help="Output PNG path")
    p_img.add_argument("--title", default="Business Model Canvas", help="Title text")
    p_img.add_argument("--data-file", default=None, help="JSON file with BMC block content")
    p_img.set_defaults(func=cmd_image)

    p_draw = sub.add_parser("drawio", help="Generate BMC .drawio from JSON data")
    p_draw.add_argument("--output", default=str(Path("diagrams") / "bmc.drawio"), help="Output .drawio path")
    p_draw.add_argument("--title", default="Business Model Canvas", help="Title text")
    p_draw.add_argument("--data-file", default=None, help="JSON file with BMC block content")
    p_draw.set_defaults(func=cmd_drawio)

    p_fill = sub.add_parser("fill", help="Auto-fill BMC from image via OCR/Gemini, then render PNG")
    p_fill.add_argument("--image", required=True, help="Path to input image")
    p_fill.add_argument("--output", default=str(Path("images") / "bmc_filled.png"), help="Output PNG path")
    p_fill.add_argument("--title", default="Business Model Canvas", help="Title text")
    p_fill.add_argument("--also-drawio", action="store_true", help="Also generate a .drawio alongside the PNG")
    p_fill.set_defaults(func=cmd_fill)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
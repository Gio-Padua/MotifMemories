"""Generate kiosk frame PNGs and install the collage actions while Photobooth is stopped."""

from __future__ import annotations

import copy
import json
import math
import shutil
import socket
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "photobooth-frontend"
DATA = ROOT / "photobooth-data"
PAPER = "#F7F3EB"
INK = "#171717"

PRESETS = (
    (
        "kiosk-fourcut-stack",
        "four-strip-twin",
        "Four Strip ×2",
        "#F4B8C2",
        4,
        tuple((x, y, 520, 390, 0, capture) for capture, y in enumerate((50, 445, 840, 1235)) for x in (40, 640)),
    ),
    (
        "kiosk-fourcut-grid",
        "butter-grid",
        "Butter Grid",
        "#F4D77A",
        4,
        ((60, 260, 520, 390, 0, 0), (620, 260, 520, 390, 0, 1), (60, 700, 520, 390, 0, 2), (620, 700, 520, 390, 0, 3)),
    ),
    (
        "kiosk-fourcut-hero",
        "mint-editorial",
        "Mint Editorial",
        "#BFD8C2",
        4,
        ((80, 80, 1040, 780, 0, 0), (80, 910, 320, 240, 0, 1), (440, 910, 320, 240, 0, 2), (800, 910, 320, 240, 0, 3)),
    ),
    (
        "kiosk-fourcut-scrapbook",
        "lavender-scrapbook",
        "Lavender Scrapbook",
        "#C8BCE8",
        4,
        ((70, 140, 500, 375, -4, 0), (620, 190, 500, 375, 3, 1), (100, 620, 500, 375, 4, 2), (630, 690, 500, 375, -3, 3)),
    ),
    (
        "kiosk-sixcut-grid",
        "mint-six-grid",
        "Six Moments",
        "#BFD8C2",
        6,
        tuple((x, y, 520, 390, 0, capture) for capture, (x, y) in enumerate((x, y) for y in (90, 520, 950) for x in (60, 620))),
    ),
    (
        "kiosk-eightcut-grid",
        "lavender-eight-grid",
        "Eight Story",
        "#C8BCE8",
        8,
        tuple((x, y, 520, 390, 0, capture) for capture, (x, y) in enumerate((x, y) for y in (45, 445, 845, 1245) for x in (60, 620))),
    ),
)


def polygon(x: int, y: int, width: int, height: int, angle: int) -> list[tuple[float, float]]:
    points = ((x, y), (x + width, y), (x + width, y + height), (x, y + height))
    if angle == 0:
        return list(points)
    cx, cy = x + width / 2, y + height / 2
    radians = math.radians(-angle)
    return [
        (cx + (px - cx) * math.cos(radians) - (py - cy) * math.sin(radians), cy + (px - cx) * math.sin(radians) + (py - cy) * math.cos(radians))
        for px, py in points
    ]


def make_assets(slug: str, accent: str, frames: tuple[tuple[int, int, int, int, int, int], ...]) -> tuple[Image.Image, Image.Image]:
    overlay = Image.new("RGBA", (1200, 1800), PAPER)
    draw = ImageDraw.Draw(overlay)
    for frame in frames:
        window = polygon(*frame[:5])
        draw.polygon(window, fill=(0, 0, 0, 0))
        draw.line([*window, window[0]], fill=INK, width=7, joint="curve")

    footer_top = 1655 if max(y + height for _, y, _, height, _, _ in frames) > 1500 else 1510
    footer_boxes = ((40, footer_top, 560, 1760), (640, footer_top, 1160, 1760)) if slug == "four-strip-twin" else ((72, footer_top, 1128, 1760),)
    for left, top, right, bottom in footer_boxes:
        draw.rounded_rectangle((left, top, right, bottom), radius=34, fill=accent)
        draw.ellipse((left + 24, top + 24, left + 68, top + 68), fill=INK)
        draw.line((left + 92, top + 38, right - 36, top + 38), fill=INK, width=10)
        draw.line((left + 92, top + 72, right - 120, top + 72), fill=INK, width=6)

    preview = Image.new("RGBA", (1200, 1800), PAPER)
    preview_draw = ImageDraw.Draw(preview)
    colors = ("#DDA7A4", "#D8C79A", "#98B5AB", "#AFA4C8", "#E7B9A9", "#9BB9C7", "#E2C77B", "#B6A6D4")
    for frame in frames:
        window = polygon(*frame[:5])
        preview_draw.polygon(window, fill=colors[frame[5]])
        xs, ys = zip(*window)
        left, top, right, bottom = min(xs), min(ys), max(xs), max(ys)
        preview_draw.ellipse((left + (right-left)*0.22, top + (bottom-top)*0.16, left + (right-left)*0.78, top + (bottom-top)*0.72), fill="#F7F3EB")
        preview_draw.arc((left + (right-left)*0.15, top + (bottom-top)*0.45, left + (right-left)*0.85, top + (bottom-top)*1.05), 190, 350, fill=INK, width=10)
    preview.alpha_composite(overlay)
    return overlay, preview


def install_assets() -> None:
    source_frames = FRONTEND / "public" / "kiosk" / "frames"
    source_previews = FRONTEND / "public" / "kiosk" / "previews"
    runtime_frames = DATA / "userdata" / "kiosk" / "frames"
    for directory in (source_frames, source_previews, runtime_frames):
        directory.mkdir(parents=True, exist_ok=True)

    for _, slug, _, accent, _, frames in PRESETS:
        overlay, preview = make_assets(slug, accent, frames)
        overlay.save(source_frames / f"{slug}.png", optimize=True)
        overlay.save(runtime_frames / f"{slug}.png", optimize=True)
        preview.save(source_previews / f"{slug}.png", optimize=True)


def install_config() -> None:
    target = DATA / "config" / "config.json"
    if not target.exists():
        raise FileNotFoundError(f"Start Photobooth once to create {target}, then stop it and rerun this installer.")

    config = json.loads(target.read_text(encoding="utf-8"))

    template = config["actions"]["collage"][0]
    actions = []
    for action_name, slug, title, accent, _, frames in PRESETS:
        action = copy.deepcopy(template)
        action["name"] = action_name
        action["jobcontrol"] = {
            "countdown_capture": 10,
            "countdown_capture_second_following": 10,
            "ask_approval_each_capture": False,
            "approve_autoconfirm_timeout": 15,
            "show_individual_captures_in_gallery": False,
        }
        action["processing"] = {
            "capture_remove_background": False,
            "capture_fill_background_enable": False,
            "capture_fill_background_color": PAPER,
            "capture_img_background_enable": False,
            "capture_img_background_file": None,
            "canvas_width": 1200,
            "canvas_height": 1800,
            "merge_definition": [
                {
                    "description": f"Photo {capture_index + 1}",
                    "pos_x": x,
                    "pos_y": y,
                    "pos_z": index,
                    "width": width,
                    "height": height,
                    "rotate": angle,
                    "predefined_image": None,
                    "image_filter": "original",
                    "capture_index": capture_index,
                }
                for index, (x, y, width, height, angle, capture_index) in enumerate(frames, start=1)
            ],
            "canvas_fill_background_enable": True,
            "canvas_fill_background_color": PAPER,
            "canvas_img_background_enable": False,
            "canvas_img_background_file": None,
            "canvas_img_front_enable": True,
            "canvas_img_front_file": f"userdata/kiosk/frames/{slug}.png",
            "canvas_texts_enable": False,
            "canvas_texts": [],
        }
        action["trigger"]["ui_trigger"].update({"show_button": True, "title": title, "icon": "photo_camera", "use_custom_color": True, "custom_color": accent})
        action["trigger"]["keyboard_trigger"]["keycode"] = ""
        action["trigger"]["gpio_trigger"]["pin"] = ""
        actions.append(action)

    config["actions"]["collage"] = actions
    backup = target.with_suffix(".json.bak")
    if target.exists() and not backup.exists():
        shutil.copy2(target, backup)
    target.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    try:
        with socket.create_connection(("127.0.0.1", 8000), timeout=0.25):
            raise SystemExit("Stop Photobooth before installing presets so its in-memory configuration cannot overwrite them.")
    except OSError:
        pass

    install_assets()
    install_config()
    for path in (FRONTEND / "public" / "kiosk" / "frames").glob("*.png"):
        with Image.open(path) as image:
            assert image.size == (1200, 1800) and image.mode == "RGBA"
    print("Installed six kiosk presets and exact 1200x1800 frame assets. Start Photobooth, then refresh the kiosk.")

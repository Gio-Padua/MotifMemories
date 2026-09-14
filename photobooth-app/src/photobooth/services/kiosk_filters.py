"""Four curated looks, rendered from a pristine photo layer before decoration."""

from pathlib import Path

from PIL import Image

from .config.groups.actions import CollageProcessing
from .mediaprocessing.context import ImageContext
from .mediaprocessing.pipeline import Pipeline
from .mediaprocessing.steps.image import FillBackgroundStep, ImageMountStep, PluginFilters, PluginFilterStep, TextStep

FILTERS = {"original": "original", "soft": "FilterPilgram2.reyes", "warm": "FilterPilgram2.crema", "mono": "FilterPilgram2.inkwell"}


def compose_look(source: Path, config: CollageProcessing, look: str, preview: bool = False) -> Image.Image:
    if look not in FILTERS:
        raise ValueError("Unknown kiosk filter")
    with Image.open(source) as original:
        layer = original.convert("RGBA")
    if preview:
        layer.thumbnail((300, 450), Image.Resampling.LANCZOS)
    alpha = layer.getchannel("A")
    context = ImageContext(layer, preview)
    Pipeline(PluginFilterStep(PluginFilters(FILTERS[look])))(context)
    context.image = context.image.convert("RGBA")
    context.image.putalpha(alpha)
    steps = []
    if config.canvas_img_background_enable:
        steps.append(ImageMountStep(config.canvas_img_background_file))
    if config.canvas_fill_background_enable:
        steps.append(FillBackgroundStep(config.canvas_fill_background_color))
    if config.canvas_img_front_enable:
        steps.append(ImageMountStep(config.canvas_img_front_file, reverse=True))
    if config.canvas_texts_enable:
        texts = [text.model_copy(deep=True) for text in config.canvas_texts]
        if preview:
            scale = layer.width / config.canvas_width
            for text in texts:
                text.pos_x = round(text.pos_x * scale)
                text.pos_y = round(text.pos_y * scale)
                text.font_size = max(1, round(text.font_size * scale))
        steps.append(TextStep(texts))
    Pipeline(*steps)(context)
    return context.image.convert("RGB")


def render_look(mediaitem, look: str):
    if look == "original" and not mediaitem.filter_source:
        return
    if not mediaitem.filter_source:
        raise ValueError("This result has no pristine filter source")
    image = compose_look(mediaitem.filter_source, CollageProcessing(**mediaitem.pipeline_config), look)
    temporary = mediaitem.processed.with_suffix(".filtering.jpg")
    try:
        image.save(temporary, format="JPEG", quality=95, subsampling=0)
        temporary.replace(mediaitem.processed)
    finally:
        image.close()
        temporary.unlink(missing_ok=True)

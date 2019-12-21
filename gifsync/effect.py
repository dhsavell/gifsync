import functools
import io
import tempfile
from typing import Callable, Iterable, List

import wand.image
from PIL import Image

AVEffect = Callable[[List[Image.Image], List[float]], Iterable[Image.Image]]


def index_by_amplitude(
    frames: List[Image.Image], amplitudes: List[float]
) -> Iterable[Image.Image]:
    frame_indices = [int((len(frames) - 1) * r) for r in amplitudes]

    for i in frame_indices:
        yield frames[i]


def cas_by_amplitude(
    frames: List[Image.Image], amplitudes: List[float]
) -> Iterable[Image.Image]:
    factors = [1 - a for a in amplitudes]
    frame = frames[0]

    frame_filename = tempfile.mktemp(suffix=".png")
    frame.save(frame_filename)

    with wand.image.Image(filename=frame_filename) as base_image:
        for f in factors:
            with base_image.clone() as i:
                original_width, original_height = i.size
                i.liquid_rescale(int(f * original_width), int(f * original_height))
                print(i.size)
                i.resize(original_width, original_height)

                out = io.BytesIO()
                i.save(out)
                out.seek(0)
                yield Image.open(out)


def _cas(frame: Image.Image, f: float) -> Image.Image:
    frame_filename = tempfile.mktemp(suffix=".png")
    frame.save(frame_filename)

    with wand.image.Image(filename=frame_filename) as base_image:
        with base_image.clone() as i:
            original_width, original_height = i.size
            i.liquid_rescale(int(f * original_width), int(f * original_height))
            print(i.size)
            i.resize(original_width, original_height)

            out = io.BytesIO()
            i.save(out)
            out.seek(0)
            return Image.open(out)


def cas_and_index_by_amplitude(
    frames: List[Image.Image], amplitudes: List[float]
) -> Iterable[Image.Image]:
    indexed_frames = index_by_amplitude(frames, amplitudes)
    frame_indices = [int((len(frames) - 1) * r) for r in amplitudes]
    factors = [1 - a for a in amplitudes]
    frame_cache = {}

    for (idx, f) in zip(frame_indices, factors):
        if idx not in frame_cache:
            frame_cache[idx] = _cas(frames[idx], f)

        yield frame_cache[idx]


def apply_effects(
    frames: List[Image.Image], amplitudes: List[float], **effects: AVEffect
) -> Iterable[Image.Image]:
    return functools.reduce(
        lambda effect_frames, f: f(effect_frames, amplitudes), effects, frames
    )

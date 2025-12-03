import json
import os
from pathlib import Path
from typing import Iterable


class GaussianBlur:
    def __init__(self, radius: int = 2) -> None:
        self.radius = radius


class ImageFilter:
    GaussianBlur = GaussianBlur


class PixelAccess:
    def __init__(self, image: "Image") -> None:
        self.image = image

    def __getitem__(self, xy: tuple[int, int]):
        x, y = xy
        return self.image.get_pixel(x, y)

    def __setitem__(self, xy: tuple[int, int], value):
        x, y = xy
        self.image.put_pixel(x, y, value)


class Image:
    def __init__(self, pixels: list[list]) -> None:
        self.pixels = pixels
        self.height = len(pixels)
        self.width = len(pixels[0]) if pixels else 0

    @property
    def size(self) -> tuple[int, int]:
        return (self.width, self.height)

    @classmethod
    def new(cls, mode: str, size: tuple[int, int], color=(0, 0, 0)) -> "Image":
        width, height = size
        if isinstance(color, str):
            color = (255, 255, 255) if color.lower() == "white" else (0, 0, 0)
        if mode == "RGB":
            r, g, b = color if isinstance(color, (list, tuple)) else (color, color, color)
            pixels = [[(int(r), int(g), int(b)) for _ in range(width)] for _ in range(height)]
        elif mode == "L":
            val = int(color if isinstance(color, (int, float)) else color[0])
            pixels = [[val for _ in range(width)] for _ in range(height)]
        else:
            raise ValueError(f"Unsupported mode {mode}")
        return cls(pixels)

    @classmethod
    def open(cls, fp):
        if isinstance(fp, (str, os.PathLike)):
            data = Path(fp).read_bytes()
        else:
            data = fp.read()
        payload = json.loads(data.decode("utf-8"))
        return cls(payload["pixels"])

    def convert(self, mode: str) -> "Image":
        if mode == "RGB":
            pixels = [
                [self._to_rgb(self.get_pixel(x, y)) for x in range(self.width)]
                for y in range(self.height)
            ]
            return Image(pixels)
        if mode == "L":
            pixels: list[list[int]] = []
            for y in range(self.height):
                row: list[int] = []
                for x in range(self.width):
                    r, g, b = self._to_rgb(self.get_pixel(x, y))
                    grey = int(0.299 * r + 0.587 * g + 0.114 * b)
                    row.append(grey)
                pixels.append(row)
            return Image(pixels)
        raise ValueError(f"Unsupported mode {mode}")

    def load(self) -> PixelAccess:
        return PixelAccess(self)

    def get_pixel(self, x: int, y: int):
        return self.pixels[y][x]

    def getpixel(self, xy: tuple[int, int]):
        x, y = xy
        return self.get_pixel(x, y)

    def put_pixel(self, x: int, y: int, value) -> None:
        self.pixels[y][x] = value

    def copy(self) -> "Image":
        return Image(json.loads(json.dumps(self.pixels)))

    def crop(self, box: tuple[int, int, int, int]) -> "Image":
        x1, y1, x2, y2 = box
        x2 = min(x2, self.width)
        y2 = min(y2, self.height)
        pixels = [row[x1:x2] for row in self.pixels[y1:y2]]
        return Image(pixels)

    def paste(self, other: "Image", box: tuple[int, int, int, int]) -> None:
        x1, y1, x2, y2 = box
        for yy in range(y1, min(y2, self.height)):
            for xx in range(x1, min(x2, self.width)):
                src_x = min(xx - x1, other.width - 1)
                src_y = min(yy - y1, other.height - 1)
                self.put_pixel(xx, yy, other.get_pixel(src_x, src_y))

    def filter(self, filter_obj) -> "Image":
        if isinstance(filter_obj, GaussianBlur):
            return self._blur(filter_obj.radius)
        raise ValueError("Unsupported filter")

    def _blur(self, radius: int) -> "Image":
        new_pixels: list[list] = []
        for y in range(self.height):
            new_row: list = []
            for x in range(self.width):
                neighbors = self._neighbor_pixels(x, y, radius)
                r = sum(p[0] for p in neighbors) // len(neighbors)
                g = sum(p[1] for p in neighbors) // len(neighbors)
                b = sum(p[2] for p in neighbors) // len(neighbors)
                new_row.append((r, g, b))
            new_pixels.append(new_row)
        return Image(new_pixels)

    def _neighbor_pixels(self, x: int, y: int, radius: int) -> list[tuple[int, int, int]]:
        values: list[tuple[int, int, int]] = []
        for yy in range(max(0, y - radius), min(self.height, y + radius + 1)):
            for xx in range(max(0, x - radius), min(self.width, x + radius + 1)):
                values.append(self._to_rgb(self.get_pixel(xx, yy)))
        return values

    def _to_rgb(self, value) -> tuple[int, int, int]:
        if isinstance(value, str):
            return (255, 255, 255) if value.lower() == "white" else (0, 0, 0)
        if isinstance(value, (list, tuple)):
            if len(value) == 3:
                return int(value[0]), int(value[1]), int(value[2])
            return (int(value[0]), int(value[0]), int(value[0]))
        return (int(value), int(value), int(value))

    def save(self, fp, format: str | None = None):
        data = json.dumps({"pixels": self.pixels}).encode("utf-8")
        if isinstance(fp, (str, os.PathLike)):
            Path(fp).write_bytes(data)
        else:
            fp.write(data)
        return fp


class ImageDraw:
    class Draw:
        def __init__(self, image: Image) -> None:
            self.image = image

        def text(self, position: tuple[int, int], text: str, fill=(0, 0, 0)) -> None:
            x_start, y_start = position
            width = max(len(text) * 6, 8)
            height = 12
            for y in range(y_start, min(self.image.height, y_start + height)):
                for x in range(x_start, min(self.image.width, x_start + width)):
                    self.image.put_pixel(x, y, fill)


__all__ = ["Image", "ImageDraw", "ImageFilter", "GaussianBlur"]

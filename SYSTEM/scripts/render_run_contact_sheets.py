"""Create visual-QA contact sheets; does not alter the original evidence images."""
import argparse
from pathlib import Path

from PIL import Image, ImageDraw


def main(source: Path, output: Path):
    paths = sorted(source.rglob("*.png"))
    output.mkdir(parents=True, exist_ok=True)
    for start in range(0, len(paths), 8):
        sheet = Image.new("RGB", (1600, 4 * 540), "#eeeeee")
        draw = ImageDraw.Draw(sheet)
        for index, path in enumerate(paths[start:start + 8]):
            image = Image.open(path).convert("RGB")
            image.thumbnail((780, 500))
            left = (index % 2) * 800 + 10
            top = (index // 2) * 540 + 28
            sheet.paste(image, (left, top))
            draw.text((left, top - 20), str(path.relative_to(source)), fill="black")
        sheet.save(output / f"sheet-{start // 8 + 1:02d}.png")
    print(f"Contact sheets for {len(paths)} images: {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    main(args.source, args.output)

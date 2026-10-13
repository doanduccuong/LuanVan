"""Show the inspected source, face crop, alignment and actual 48x48 tensor."""
from pathlib import Path
import argparse

from PIL import Image,ImageDraw


def main(root: Path):
    labels=("Angry","Disgust","Fear","Happy","Sad","Surprise","Neutral")
    variants=(("source.jpg","Source"),("bbox.jpg","Detected bounding box"),
              ("aligned112.jpg","ArcFace alignment 112"),("tensor48.png","Emotion tensor 48"))
    sheet=Image.new("RGB",(1040,7*255+40),"white")
    draw=ImageDraw.Draw(sheet)
    for col,(_,title) in enumerate(variants):
        draw.text((col*260+10,10),title,fill="black")
    for row,label in enumerate(labels):
        for col,(suffix,_) in enumerate(variants):
            image=Image.open(root/"previews"/f"{label}_{suffix}").convert("RGB")
            image.thumbnail((230,220))
            if suffix=="tensor48.png":
                image=image.resize((192,192),Image.Resampling.NEAREST)
            x=col*260+10+(230-image.width)//2
            y=row*255+58
            sheet.paste(image,(x,y))
        draw.text((10,row*255+39),f"Source label: {label}",fill="black")
    sheet.save(root/"preprocessing-preview.png")


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("root",type=Path)
    main(parser.parse_args().root)

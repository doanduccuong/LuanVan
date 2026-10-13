"""Render all unique native sources for visual checking of pose and labels."""
import argparse
import json
from pathlib import Path

from PIL import Image,ImageDraw


def main(dataset: Path,diagnosis: Path):
    data=json.loads((diagnosis/'preprocessing-ablation.json').read_text())
    rows={row['sha256']:row for row in data['records']}
    rows=sorted(rows.values(),key=lambda row:(row['label'],row['source_filename']))
    columns=8
    height=((len(rows)+columns-1)//columns)*240
    sheet=Image.new('RGB',(columns*180,height),'white')
    draw=ImageDraw.Draw(sheet)
    for index,row in enumerate(rows):
        image=Image.open(dataset/row['image_path']).convert('RGB')
        image.thumbnail((164,205))
        x=(index%columns)*180+8
        y=(index//columns)*240
        draw.text((x,y+2),f"{row['label']} {row['source_filename']}",fill='black')
        sheet.paste(image,(x+(164-image.width)//2,y+25))
    sheet.save(diagnosis/'unique-source-poses.png')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--dataset',type=Path,required=True)
    parser.add_argument('--diagnosis',type=Path,required=True)
    args=parser.parse_args()
    main(args.dataset,args.diagnosis)

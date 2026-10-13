"""Resolve held-aside native sources for a read-only face-preprocessing diagnosis."""
import argparse
import csv
import hashlib
import shutil
from pathlib import Path


def main(dataset: Path, source: Path, output: Path) -> None:
    if output.exists():
        raise ValueError(f"Output already exists: {output}")
    with (dataset/"image_manifest.csv").open(encoding="utf-8",newline="") as handle:
        images=[row for row in csv.DictReader(handle) if row["role"] in ("enrollment","calibration")]
    output.mkdir(parents=True)
    events=[]
    for row in images:
        paths=[p for p in source.rglob(row['source_filename'])
               if hashlib.sha256(p.read_bytes()).hexdigest()==row['source_sha256']]
        assert len(paths)==1
        image_path=Path('observations')/row['subject_id']/row['source_filename']
        (output/image_path).parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(paths[0],output/image_path)
        events.append({'image_path':str(image_path),'expected_expression_label':row['expression_label'],
                       'source_filename':row['source_filename'],'source_role':row['role']})
    with (output/'events.csv').open('w',encoding='utf-8',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=list(events[0]))
        writer.writeheader()
        writer.writerows(events)
    print(f'Prepared {len(events)} untouched enrollment/calibration source images for offline diagnosis.')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--dataset',type=Path,required=True)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    main(args.dataset,args.source,args.output)

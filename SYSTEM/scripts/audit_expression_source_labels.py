"""Check source-to-event labels and duplicate conflicts without relabeling images."""
import argparse
import csv
import hashlib
import json
from collections import Counter,defaultdict
from pathlib import Path

import cv2


def main(source: Path,dataset: Path,output: Path):
    file_groups,pixel_groups=defaultdict(list),defaultdict(list)
    labels=Counter()
    sizes=Counter()
    paths=list(source.rglob('*.jpg'))
    by_name=defaultdict(list)
    for path in paths:
        label=path.parent.name.title()
        file_digest=hashlib.sha256(path.read_bytes()).hexdigest()
        image=cv2.imread(str(path))
        if image is None:raise ValueError(f'Unreadable image: {path}')
        pixel_digest=hashlib.sha256(str(image.shape).encode()+image.tobytes()).hexdigest()
        record={'source_file':str(path.relative_to(source)),'label':label}
        file_groups[file_digest].append(record)
        pixel_groups[pixel_digest].append(record)
        labels[label]+=1
        sizes[f'{image.shape[1]}x{image.shape[0]}']+=1
        by_name[path.name].append((path,file_digest))
    def conflicts(groups):
        return [rows for rows in groups.values() if len({row['label'] for row in rows})>1]
    with (dataset/'events.csv').open(encoding='utf-8',newline='') as handle:
        events=list(csv.DictReader(handle))
    with (dataset/'image_manifest.csv').open(encoding='utf-8',newline='') as handle:
        images={row['output']:row for row in csv.DictReader(handle) if row['role']=='observation'}
    mismatches=[]
    for event in events:
        image=images[event['image_path']]
        candidates=[path for path,digest in by_name[event['source_filename']]
                    if digest==image['source_sha256']]
        if len(candidates)!=1:
            mismatches.append({'event_id':event['event_id'],'reason':'source not uniquely resolved'})
            continue
        source_path=candidates[0]
        if not source_path.parent.name.lower()==event['expected_expression_label'].lower()==image['expression_label'].lower():
            mismatches.append({'event_id':event['event_id'],'reason':'source folder / manifest / event labels differ'})
        if hashlib.sha256((dataset/event['image_path']).read_bytes()).hexdigest()!=image['source_sha256']:
            mismatches.append({'event_id':event['event_id'],'reason':'native frame differs from source'})
    result={'source_count':len(paths),'folder_label_counts':dict(labels),
            'image_sizes':dict(sizes),'exact_file_cross_label_conflicts':conflicts(file_groups),
            'decoded_pixel_cross_label_conflicts':conflicts(pixel_groups),
            'camera_event_count':len(events),'camera_mapping_mismatches':mismatches,
            'official_kdef_labels_verified':False,
            'scope':'Consistency with Kaggle folders is verified; semantic correctness against official KDEF is not established.'}
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print(json.dumps({key:value for key,value in result.items() if key not in ('exact_file_cross_label_conflicts','decoded_pixel_cross_label_conflicts')},ensure_ascii=False))
    print('Cross-label file conflicts:',len(result['exact_file_cross_label_conflicts']))
    print('Cross-label pixel conflicts:',len(result['decoded_pixel_cross_label_conflicts']))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--dataset',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    main(args.source,args.dataset,args.output)

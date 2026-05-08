#!/usr/bin/env python3
import json, pathlib, tempfile
from pycocotools.coco import COCO
from pycocotools.cocoeval import COCOeval

VEHICLE_CAT_IDS=[2,3,4,6,8]
ZERO_STATS={
    'mAP_50_95': 0.0, 'mAP_50': 0.0, 'mAP_75': 0.0,
    'mAP_small': 0.0, 'mAP_medium': 0.0, 'mAP_large': 0.0,
    'AR_1': 0.0, 'AR_10': 0.0, 'AR_100': 0.0,
    'AR_small': 0.0, 'AR_medium': 0.0, 'AR_large': 0.0,
}

def evaluate_coco(predictions_path, ann_path, mode='native_vehicle'):
    predictions_path=str(predictions_path); ann_path=str(ann_path)
    if mode == 'collapsed_vehicle':
        data=json.load(open(ann_path))
        data['categories']=[{'id':1,'name':'vehicle','supercategory':'vehicle'}]
        anns=[]
        for ann in data['annotations']:
            if ann.get('category_id') in VEHICLE_CAT_IDS:
                ann=dict(ann); ann['category_id']=1; anns.append(ann)
        data['annotations']=anns
        preds=[]
        for p in json.load(open(predictions_path)):
            if p.get('category_id') in VEHICLE_CAT_IDS or p.get('category_id') == 1:
                q=dict(p); q['category_id']=1; preds.append(q)
        with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as gf, tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as pf:
            json.dump(data,gf); gf.flush()
            json.dump(preds,pf); pf.flush()
            gt=COCO(gf.name); dt=gt.loadRes(pf.name) if preds else gt.loadRes([])
    else:
        gt=COCO(ann_path)
        preds=[p for p in json.load(open(predictions_path)) if p.get('category_id') in VEHICLE_CAT_IDS]
        with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as pf:
            json.dump(preds,pf); pf.flush()
            dt=gt.loadRes(pf.name) if preds else gt.loadRes([])
    if not preds:
        return dict(ZERO_STATS), 0
    ev=COCOeval(gt, dt, 'bbox')
    if mode != 'collapsed_vehicle':
        ev.params.catIds=VEHICLE_CAT_IDS
    ev.evaluate(); ev.accumulate(); ev.summarize()
    keys=['mAP_50_95','mAP_50','mAP_75','mAP_small','mAP_medium','mAP_large','AR_1','AR_10','AR_100','AR_small','AR_medium','AR_large']
    return dict(zip(keys, [float(x) for x in ev.stats])), len(preds)

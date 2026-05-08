#!/usr/bin/env python3
import json, pathlib, sys
root=pathlib.Path(sys.argv[1]); master=root/'master_detector_results.jsonl'
rows=[]
if master.exists():
    for line in master.read_text().splitlines():
        if line.strip():
            try: rows.append(json.loads(line))
            except: pass
print('# Detector Benchmark Comparison')
print('\nGenerated from `master_detector_results.jsonl`.')
print('\n| Run | Model | Status | HW latency ms | HW FPS | COCO mAP 50:95 | COCO mAP 50 | E2E COCO FPS | Video avg FPS |')
print('|---|---|---:|---:|---:|---:|---:|---:|---:|')
for r in rows:
    env=r.get('environment') or {}; model=((env.get('model') or {}).get('name')) or r.get('run_id','').split('_')[-3]
    lat=r.get('latency') or {}; acc=r.get('accuracy') or {}; vid=r.get('video') or {}
    a=acc.get('accuracy') or {}
    v=vid.get('videos') or []
    okv=[x for x in v if x.get('status')=='ok']
    avg=sum(x.get('end_to_end_fps',0) for x in okv)/len(okv) if okv else None
    def f(x): return '' if x is None else (f'{x:.4f}' if isinstance(x,float) else str(x))
    print(f"| {r.get('run_id','')} | {model} | {r.get('status','')} | {f(lat.get('hw_latency_ms'))} | {f(lat.get('processing_fps_from_hw_latency'))} | {f(a.get('mAP_50_95'))} | {f(a.get('mAP_50'))} | {f(acc.get('end_to_end_fps'))} | {f(avg)} |")
print('\n## Notes')
print('- Video metrics are throughput/detection-count metrics only unless separate ground-truth annotations are added.')
print('- `HW FPS` is computed as `1000 / HW latency ms`; it is not full application FPS.')

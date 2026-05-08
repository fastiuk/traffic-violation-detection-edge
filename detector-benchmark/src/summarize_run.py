#!/usr/bin/env python3
import json, pathlib, sys

TEARDOWN_CODES = {134, 139}

rd = pathlib.Path(sys.argv[1])

def load(name):
    p = rd / name
    if p.exists():
        try:
            with open(p, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            return {'_error': str(e)}
    return None

def raw_status():
    p = rd / 'status.txt'
    return p.read_text().strip() if p.exists() else 'unknown'

def valid_accuracy(metrics, predictions):
    if not isinstance(metrics, dict) or metrics.get('_error'):
        return False
    if int(metrics.get('images_processed') or 0) <= 0:
        return False
    accuracy = metrics.get('accuracy')
    if not isinstance(accuracy, dict) or 'mAP_50_95' not in accuracy:
        return False
    return isinstance(predictions, list)

def valid_video(metrics):
    if not isinstance(metrics, dict) or metrics.get('_error'):
        return False
    videos = metrics.get('videos')
    if not isinstance(videos, list) or not videos:
        return False
    return all(v.get('status') == 'ok' and int(v.get('frames') or 0) > 0 for v in videos)

def derive_status(exit_codes, accuracy, predictions, video):
    adjustments = []
    effective = dict(exit_codes) if isinstance(exit_codes, dict) else {}

    if effective.get('coco') in TEARDOWN_CODES and valid_accuracy(accuracy, predictions):
        adjustments.append({
            'step': 'coco',
            'raw_exit_code': effective['coco'],
            'effective_exit_code': 0,
            'reason': 'native teardown crash after complete COCO metrics',
        })
        effective['coco'] = 0

    if effective.get('video') in TEARDOWN_CODES and valid_video(video):
        adjustments.append({
            'step': 'video',
            'raw_exit_code': effective['video'],
            'effective_exit_code': 0,
            'reason': 'native teardown crash after complete video metrics',
        })
        effective['video'] = 0

    required = ('latency', 'coco', 'video')
    if all(effective.get(k) == 0 for k in required):
        return 'complete', effective, adjustments
    if effective:
        return 'partial_or_failed', effective, adjustments
    return raw_status(), effective, adjustments

latency = load('metrics_latency.json')
accuracy = load('metrics_accuracy.json')
predictions = load('predictions_coco.json')
video = load('metrics_video.json')
exit_codes = load('exit_codes.json')
status, effective_exit_codes, adjustments = derive_status(exit_codes, accuracy, predictions, video)

summary = {
    'run_dir': str(rd),
    'run_id': rd.name,
    'status': status,
    'raw_status': raw_status(),
    'environment': load('environment.json'),
    'latency': latency,
    'accuracy': accuracy,
    'video': video,
    'exit_codes': exit_codes,
    'effective_exit_codes': effective_exit_codes or exit_codes,
}
if adjustments:
    summary['status_adjustments'] = adjustments
print(json.dumps(summary))

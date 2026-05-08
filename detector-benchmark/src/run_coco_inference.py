#!/usr/bin/env python3
import argparse, json, os, sys, time
from pathlib import Path
import cv2
import numpy as np
from tqdm import tqdm
from pycocotools.coco import COCO
sys.path.insert(0, '/usr/lib/python3/dist-packages')
from hailo_platform import VDevice
from coco_vehicle_eval import evaluate_coco, VEHICLE_CAT_IDS

COCO_CONTIGUOUS_TO_ID=[1,2,3,4,5,6,7,8,9,10,11,13,14,15,16,17,18,19,20,21,22,23,24,25,27,28,31,32,33,34,35,36,37,38,39,40,41,42,43,44,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,67,70,72,73,74,75,76,77,78,79,80,81,82,84,85,86,87,88,89,90]

def exit_without_hailo_atexit_segfault(code=0):
    """Terminate after all benchmark artifacts are flushed.

    On the RPi/HailoRT 4.23 stack, Python can segfault during interpreter
    shutdown after successful VDevice inference. The crash happens after the
    output JSON files are written, but it poisons the shell exit code and makes
    valid runs look failed. Use os._exit only at the very end, after explicit
    Hailo deactivation and file writes, to bypass fragile extension-module
    finalizers without masking real exceptions during inference/evaluation.
    """
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(code)

def letterbox(img, new_shape, color=(114,114,114)):
    h,w=img.shape[:2]
    r=min(new_shape[0]/h, new_shape[1]/w)
    nw,nh=int(round(w*r)), int(round(h*r))
    dw,dh=(new_shape[1]-nw)/2, (new_shape[0]-nh)/2
    if (w,h)!=(nw,nh): img=cv2.resize(img,(nw,nh),interpolation=cv2.INTER_LINEAR)
    top,bottom=int(round(dh-.1)), int(round(dh+.1)); left,right=int(round(dw-.1)), int(round(dw+.1))
    return cv2.copyMakeBorder(img,top,bottom,left,right,cv2.BORDER_CONSTANT,value=color), r, (left,top)

def iter_dets(out, classes):
    """Yield detections from HailoRT HAILO_NMS_BY_CLASS output.

    Hailo's BY_CLASS FLOAT32 layout is compact, not fixed-stride. It stores
    each class count at index: class_idx + 5 * detections_before_this_class,
    followed immediately by that class' bbox records. Each bbox record is:
    ymin, xmin, ymax, xmax, score.

    Treating the buffer as 80 equal 501-float chunks silently mislabels every
    detection as class 0/person and destroys vehicle mAP. Do not regress this.
    """
    arr=np.ravel(out)
    if arr.size == 0:
        return
    detections_before=0
    for ci in range(classes):
        count_idx=ci + 5*detections_before
        if count_idx >= arr.size:
            break
        count=max(0, int(round(float(arr[count_idx]))))
        coco_id=1 if classes == 1 else (COCO_CONTIGUOUS_TO_ID[ci] if ci < len(COCO_CONTIGUOUS_TO_ID) else ci+1)
        start=count_idx+1
        max_count=max(0, (arr.size-start)//5)
        for j in range(min(count, max_count)):
            k=start+j*5
            yield coco_id, *arr[k:k+5]
        detections_before += count

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--hef', required=True); ap.add_argument('--model-name', required=True)
    ap.add_argument('--classes', type=int, required=True); ap.add_argument('--height', type=int, required=True); ap.add_argument('--width', type=int, required=True)
    ap.add_argument('--images', required=True); ap.add_argument('--ann', required=True); ap.add_argument('--output', required=True); ap.add_argument('--metrics', required=True)
    args=ap.parse_args()
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    coco=COCO(args.ann); img_ids=coco.getImgIds()
    results=[]; t0=time.time(); n=0
    with VDevice(VDevice.create_params()) as target:
        im=target.create_infer_model(args.hef); cim=im.configure()
        outputs={name: np.zeros(tuple(im.output(name).shape), dtype=np.float32) for name in im.output_names}
        bindings=cim.create_bindings(output_buffers=outputs)
        cim.activate()
        for img_id in tqdm(img_ids, desc=args.model_name):
            info=coco.loadImgs(img_id)[0]
            frame=cv2.imread(str(Path(args.images)/info['file_name']))
            if frame is None: continue
            img,ratio,(pw,ph)=letterbox(frame,(args.height,args.width))
            img=cv2.cvtColor(img,cv2.COLOR_BGR2RGB).astype(np.uint8)
            bindings.input().set_buffer(np.ascontiguousarray(img))
            cim.run([bindings], 10000)
            out=outputs[im.output_names[0]]
            for cid,ymin,xmin,ymax,xmax,score in iter_dets(out,args.classes):
                if float(score) < 0.001: continue
                if args.classes == 1:
                    cat=1
                else:
                    cat=int(cid)
                results.append({'image_id': int(img_id), 'category_id': cat, 'bbox': [float((xmin*args.width-pw)/ratio), float((ymin*args.height-ph)/ratio), float(((xmax-xmin)*args.width)/ratio), float(((ymax-ymin)*args.height)/ratio)], 'score': float(score)})
            n+=1
        cim.deactivate()
    Path(args.output).write_text(json.dumps(results))
    mode='collapsed_vehicle' if args.classes == 1 else 'native_vehicle'
    acc, pred_count=evaluate_coco(args.output, args.ann, mode=mode)
    metrics={'model':args.model_name,'images_processed':n,'predictions':pred_count,'eval_mode':mode,'wall_time_sec':time.time()-t0,'end_to_end_fps':n/(time.time()-t0) if time.time()>t0 else 0,'accuracy':acc}
    Path(args.metrics).write_text(json.dumps(metrics, indent=2))
    print(json.dumps(metrics, indent=2))
if __name__=='__main__':
    main()
    exit_without_hailo_atexit_segfault(0)

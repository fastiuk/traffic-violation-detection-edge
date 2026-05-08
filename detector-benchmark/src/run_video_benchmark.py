#!/usr/bin/env python3
import argparse, json, os, sys, time
from pathlib import Path
import cv2, numpy as np
from tqdm import tqdm
sys.path.insert(0, '/usr/lib/python3/dist-packages')
from hailo_platform import VDevice
from run_coco_inference import letterbox, iter_dets
VEHICLE_IDS={2,3,4,6,8}

def exit_without_hailo_atexit_segfault(code=0):
    """Terminate after all benchmark artifacts are flushed.

    HailoRT 4.23 on the RPi has been observed to segfault during Python
    interpreter shutdown after a successful VDevice run. The metrics and video
    overlays are already written at that point, but the shell sees exit 139.
    We still let real runtime errors propagate normally; this is only called
    after successful completion and explicit resource release.
    """
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(code)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--video-dir', required=True); ap.add_argument('--hef', required=True); ap.add_argument('--model-name', required=True)
    ap.add_argument('--classes', type=int, required=True); ap.add_argument('--height', type=int, required=True); ap.add_argument('--width', type=int, required=True)
    ap.add_argument('--output-dir', required=True); ap.add_argument('--metrics', required=True)
    args=ap.parse_args(); Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    videos=[]
    for ext in ('*.mp4','*.mov','*.avi','*.mkv'):
        videos.extend(Path(args.video_dir).glob(ext))
    all_stats=[]
    with VDevice(VDevice.create_params()) as target:
        im=target.create_infer_model(args.hef); cim=im.configure()
        outputs={name: np.zeros(tuple(im.output(name).shape), dtype=np.float32) for name in im.output_names}
        bindings=cim.create_bindings(output_buffers=outputs); cim.activate()
        for video in videos:
            cap=cv2.VideoCapture(str(video))
            if not cap.isOpened():
                all_stats.append({'video':video.name,'status':'open_failed'}); continue
            fps=cap.get(cv2.CAP_PROP_FPS) or 25
            w=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)); h=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)); total=int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            out_path=Path(args.output_dir)/(args.model_name+'_'+video.stem+'.mp4')
            writer=cv2.VideoWriter(str(out_path), cv2.VideoWriter_fourcc(*'mp4v'), fps, (w,h))
            frames=dets=0; t0=time.time()
            for _ in tqdm(range(total), desc=video.name):
                ok,frame=cap.read()
                if not ok: break
                img,ratio,(pw,ph)=letterbox(frame,(args.height,args.width))
                img=cv2.cvtColor(img,cv2.COLOR_BGR2RGB).astype(np.uint8)
                bindings.input().set_buffer(np.ascontiguousarray(img)); cim.run([bindings],10000)
                out=outputs[im.output_names[0]]
                for cid,ymin,xmin,ymax,xmax,score in iter_dets(out,args.classes):
                    if float(score)<0.3: continue
                    if args.classes != 1 and int(cid) not in VEHICLE_IDS: continue
                    dets += 1
                    x1=int((xmin*args.width-pw)/ratio); y1=int((ymin*args.height-ph)/ratio); x2=int((xmax*args.width-pw)/ratio); y2=int((ymax*args.height-ph)/ratio)
                    cv2.rectangle(frame,(x1,y1),(x2,y2),(0,255,0),2)
                writer.write(frame); frames+=1
            elapsed=time.time()-t0; cap.release(); writer.release()
            all_stats.append({'video':video.name,'status':'ok','frames':frames,'input_fps':fps,'elapsed_sec':elapsed,'end_to_end_fps':frames/elapsed if elapsed else 0,'raw_detections':dets,'overlay':str(out_path)})
        cim.deactivate()
    Path(args.metrics).write_text(json.dumps({'model':args.model_name,'note':'Unannotated videos: counts/FPS only, not accuracy.', 'videos':all_stats}, indent=2))
    print(json.dumps(all_stats, indent=2))
if __name__=='__main__':
    main()
    exit_without_hailo_atexit_segfault(0)

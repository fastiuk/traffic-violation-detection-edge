# Project Instructions: Traffic Violation Detection on Edge Devices

## Role and Scientific Standard

This repository supports a PhD thesis on edge-AI traffic-rule violation detection using Raspberry Pi 5 and Hailo NPU acceleration. Treat the work as research infrastructure, not as a demo application.

Be strict. A claim is not acceptable because a script runs or a video looks convincing. A claim is acceptable only when the dataset, hardware, model version, preprocessing, metric definition, and raw outputs are reproducible.

Reject weak framing immediately:

- "YOLO on Raspberry Pi with Hailo" is engineering integration, not sufficient PhD novelty.
- Raw traffic videos without labels are not accuracy evidence.
- FPS without latency breakdown is not a system-performance result.
- Hailo hardware latency and end-to-end application throughput are different measurements and must not be merged.
- The "best" model is not automatically the model with highest mAP. For this thesis, best means the best defensible trade-off among accuracy, latency, throughput, energy, thermal stability, and downstream violation utility.

## Thesis Direction

The strongest defensible thesis direction is:

Energy- and uncertainty-aware edge architecture for detecting traffic violations from fixed cameras, with reproducible benchmarking of perception modules and a trajectory-based model for unsafe lane-change detection.

The likely scientific novelty should be framed around methods and measurable improvements, not around merely deploying existing models:

1. Event-triggered inference and adaptive scheduling on constrained edge hardware.
2. Uncertainty-aware violation scoring that reduces false positives.
3. Edge-computable trajectory analysis for unsafe lane-change or cut-in detection.
4. Reproducible benchmarking methodology for detector, tracker, lane, and LPR modules under identical hardware and dataset constraints.

Acceptable novelty metrics include:

- Energy reduction at fixed accuracy or bounded accuracy loss.
- Joules per processed frame, tracked vehicle, plate recognition, or violation candidate.
- Accuracy per watt and accuracy per dollar.
- Reduction in false-positive violation decisions.
- Calibrated speed uncertainty, not only point speed estimates.
- F1, precision, recall, expert agreement, and false-positive rate for unsafe lane-change detection.

## Overall System Architecture

Target hardware:

- Raspberry Pi 5, preferably 8GB RAM.
- Hailo-8L for the first working prototype and detector benchmark.
- Hailo-10H only when comparing accelerator scaling or when multi-model/multi-camera workload requires it.
- Fixed camera for traffic scene understanding.
- Optional second narrow-FOV/telephoto camera for license plates.
- Optional radar/mmWave speed sensor if legal-grade or stronger speed evidence is required.
- External power logging is preferred for energy claims.

Runtime architecture:

```text
Camera input
  -> frame acquisition and timestamping
  -> vehicle detector on Hailo NPU
  -> CPU tracker
  -> lane assignment using calibrated geometry or lane detector
  -> speed estimator with uncertainty
  -> violation candidate engine
  -> event-triggered plate detection/OCR
  -> uncertainty-aware decision layer
  -> evidence package and result store
```

Evidence package for each violation candidate:

- Event ID, timestamp, camera ID, location if available.
- Tracked vehicle ID and trajectory segment.
- Violation type and rule version.
- Detector/tracker/lane/speed/OCR confidence values.
- Calibration version.
- Short video clip before and after event.
- Representative frames with boxes, track IDs, lane polygons, virtual gates, and plate crop if available.
- Raw machine-readable metadata.

## Research Architecture

The project should be built as a benchmark factory before it becomes a full violation system.

Control host:

- Local workstation or server orchestrates experiments.
- It owns configs, source code, result aggregation, report generation, and git history.
- It syncs code to the RPi and executes remote jobs over SSH.

Raspberry Pi:

- Treat the Pi as a benchmark target, not as the orchestration brain.
- It runs Hailo inference, video benchmarks, and device telemetry collection.
- It writes raw run artifacts that are pulled back to the control host.

Persistent result artifacts:

- Raw predictions.
- Ground truth or annotation references.
- Logs.
- Hardware latency output.
- Application FPS and per-stage timing.
- Power and temperature logs when available.
- Model metadata, precision, resolution, thresholds, and git commit.
- Generated reports, plots, and tables.

## Mandatory Experimental Discipline

Every experiment must record:

- `experiment_id`
- timestamp
- git commit
- device name
- OS/runtime versions
- HailoRT version
- model name, source, version, precision, input resolution
- dataset name, split, annotation source, and sample count
- preprocessing and postprocessing definitions
- confidence threshold and NMS settings
- warm-up policy
- latency method
- FPS method
- power measurement method if energy is claimed
- success/failure status
- exact command or script used

Minimum result schema:

```json
{
  "experiment_id": "detector_yolov8s_coco_val2017_h8l_int8_640",
  "timestamp": "ISO-8601",
  "git_commit": "unknown",
  "device": "rpi5_hailo8l",
  "task": "vehicle_detection",
  "dataset": "coco_val2017",
  "model": "yolov8s",
  "precision": "int8",
  "input_resolution": "640x640",
  "latency_ms_hw_avg": 0.0,
  "latency_ms_app_p50": 0.0,
  "latency_ms_app_p95": 0.0,
  "fps_app": 0.0,
  "fps_real_end_to_end": 0.0,
  "power_w_avg": null,
  "temperature_c_avg": null,
  "map50": null,
  "map50_95": null,
  "precision_metric": null,
  "recall_metric": null,
  "status": "success"
}
```

Warm-up:

- Discard the first 50-100 frames for timing unless a specific cold-start experiment is being performed.
- Record the warm-up count.

Accuracy:

- COCO Val2017 with official annotations is acceptable for detector mAP.
- Raw videos are acceptable for throughput, qualitative inspection, object count trends, and failure analysis.
- Raw videos are not acceptable for mAP, precision, recall, F1, or violation accuracy unless annotated.

Latency:

- Hardware latency must come from Hailo tooling when possible, e.g. `hailortcli run --measure-latency`.
- Application FPS must include preprocessing, inference call overhead, postprocessing, and data transfer.
- Real end-to-end FPS must include capture/decode and rendering/storage if those are part of the measured pipeline.

Power:

- Prefer logged external measurement.
- If using software telemetry, label it as telemetry, not as calibrated power measurement.
- Energy claims require measurement method, sampling rate, and workload duration.

Failures:

- A failed model download, HEF parse, runtime crash, missing dataset, or incompatible postprocessor is a reproducibility failure.
- Do not silently skip failed models.
- Do not encode failures as zero mAP. Record `status = failed` and preserve logs.

## Research Phases

### Phase 0: Infrastructure and Reproducibility

Goal: make the benchmark harness repeatable and boring.

Required outputs:

- One-command local-to-RPi sync.
- One-command environment check.
- One-command detector benchmark run.
- Structured JSONL/CSV result output.
- Markdown report generation.
- Clear separation between raw artifacts and summarized tables.

Current repo anchor:

- `detector-benchmark/` is the cleaned detector-only benchmark harness.
- `hailo-npu-benchmarks/` contains earlier broader Hailo benchmarking experiments.
- `performance-benchmark/` contains early CPU vs Hailo demos and web-streaming scripts.
- `setup/` contains setup scripts and dataset helpers.

### Phase 1: Detector Benchmarking

This is the current first research block.

Research question:

Which vehicle/object detector gives the best edge-deployable trade-off on Raspberry Pi 5 + Hailo NPU under controlled dataset, resolution, precision, latency, and energy constraints?

Candidate detectors:

- YOLOv5n/s/m where HEF/model support exists.
- YOLOv8n/s.
- YOLOv9-t/s if Hailo compilation/runtime support is practical.
- YOLOv10n/s if Hailo support is practical.
- YOLOv11n/s.
- SSD MobileNet as a lightweight baseline.
- EfficientDet-Lite as another baseline if deployable.
- RT-DETR small only if compilation and latency are realistic.

Required detector metrics:

- COCO mAP@0.5.
- COCO mAP@0.5:0.95.
- Vehicle-class mAP and recall for car, truck, bus, motorcycle, and optionally bicycle.
- Hardware latency.
- Application FPS.
- Real end-to-end FPS where available.
- CPU load, memory, temperature, and power if available.
- Accuracy per watt and FPS per watt when power is measured.

Known baseline from prior work:

- `yolov5m_vehicles` INT8 on Hailo-8L achieved approximately 39.0% mAP@0.5:0.95, 60.6% mAP@0.5, 71.25 ms hardware latency, 14.03 processing FPS, and about 12.7 real FPS.
- Treat this as a historical baseline, not as a final validated result unless the raw run artifacts and exact script versions are available.

Use `detector-benchmark/` for new detector work.

### Phase 2: Tracker Benchmarking

Research question:

Which tracker preserves vehicle identity with acceptable CPU overhead on the edge device?

Candidate trackers:

- SORT.
- ByteTrack.
- OC-SORT.
- BoT-SORT.
- DeepSORT only if embedding cost is justified.

Required tracker metrics:

- MOTA.
- MOTP.
- IDF1.
- HOTA if tooling is available.
- ID switches.
- Track fragmentation.
- Tracking latency.
- CPU load.

Scientific warning:

Tracker benchmarks require annotated multi-object tracking datasets or manually annotated project videos. Detector-only COCO results cannot validate tracker quality.

### Phase 3: Lane and Road Geometry Benchmarking

Research question:

Is neural lane detection worth its compute and energy cost for fixed traffic cameras, or is calibrated geometry better?

Candidates:

- Manual lane polygons as the baseline.
- Virtual gates for speed measurement.
- UltraFast Lane Detection.
- YOLOP.
- LaneATT.
- CLRNet.
- Lightweight semantic segmentation.
- Hybrid manual calibration plus periodic neural lane detection.

Required metrics:

- Lane assignment accuracy for vehicles.
- Lane boundary error in pixels or meters.
- Lane mask IoU where annotations exist.
- Lane detection F1 where annotations exist.
- Runtime latency and energy.
- Robustness under shadows, rain, worn markings, night, occlusion.

Scientific warning:

For fixed cameras, manual calibrated lane geometry may beat neural lane detection in practical system value. That is not embarrassing. It may be the correct baseline and a strong argument for hybrid methods.

### Phase 4: Speed Estimation

Recommended first method:

- Two calibrated virtual gates with known real-world distance.
- Track crossing time between gates.
- Speed = distance / time.

More advanced method:

- Homography from image plane to road plane.
- Track vehicle ground-contact point.
- Propagate localization uncertainty to speed confidence interval.

Required metrics:

- MAE in km/h.
- RMSE.
- Percentage within +/-3 km/h and +/-5 km/h.
- Confidence interval calibration.
- Sensitivity to frame rate, timestamp jitter, occlusion, and calibration error.

Scientific warning:

Camera-only speed estimation can be scientifically useful but is weak for legal enforcement unless calibration is rigorous. If enforcement-grade evidence is required, radar/camera fusion is superior.

### Phase 5: LPR/ANPR Benchmarking

LPR must be split into plate detection and OCR. Do not evaluate it as a single black box unless the thesis also reports stage-level failure causes.

Plate detection candidates:

- YOLOv8n/s plate detector.
- YOLOv11n/s plate detector.
- WPOD-NET-style detector.
- Custom Hailo-compiled plate detector.

OCR candidates:

- LPRNet.
- CRNN.
- Lightweight PaddleOCR.
- EasyOCR only as a heavy baseline if used.
- Custom Ukrainian/EU plate OCR if dataset exists.

Required metrics:

- Plate detector mAP and recall, especially for small plates.
- Character accuracy.
- Full-plate accuracy.
- Edit distance.
- Accuracy by distance, angle, blur, day/night.
- Processing time per vehicle.
- Energy per recognized plate.

Scientific warning:

Wide-angle traffic-scene cameras are usually insufficient for robust plate OCR. A second narrow-FOV camera or crop-triggered high-resolution capture may be required.

### Phase 6: Violation Logic

Implement violation logic only after detector, tracker, geometry, and timing are measured.

Initial supported violations:

- Speeding with calibrated gates.
- Restricted-region or stop-line crossing.
- Lane-change event detection.

Advanced violation:

- Unsafe lane change / cut-in causing rear vehicle braking or unsafe headway.

Unsafe lane-change model should use:

- Lane membership over time.
- Lane-change event boundary.
- Target-lane rear vehicle identification.
- Relative speed.
- Time headway.
- Time-to-collision.
- Required deceleration.
- Rear-vehicle deceleration within a causal time window.

Possible rule:

```text
Unsafe lane change if:
  vehicle enters target lane
  and target-lane rear vehicle is within unsafe headway/TTC
  and rear vehicle decelerates above threshold within 1-2 seconds
  and the temporal ordering supports causality
```

Turn-signal recognition is a late-stage feature. It is fragile because the signal light may be too small, occluded, motion-blurred, or invisible in daylight. Do not make it a core early contribution.

## Current Device and Workflow

Primary RPi target:

- Host: `pi@10.10.10.21`
- Project path on RPi: `~/traffic-violation-detection-edge/`
- Preferred Python environment: `~/hailo-rpi5-examples/venv_hailo_rpi_examples/`

Historical note:

- Older conversation references may mention `192.168.1.69`. Current repository configuration uses `10.10.10.21`. Prefer the repository config unless the user explicitly updates the target.

Local-first workflow:

1. Edit files locally.
2. Sync to RPi.
3. Execute on RPi.
4. Pull results back.
5. Generate reports locally when possible.

Detector benchmark commands:

```bash
make sync-files
make run-detector-benchmark
make sync-results
```

General sync pattern:

```bash
make sync-files
```

Use Hailo hardware latency tooling when available:

```bash
make measure-latency MODEL_PATH=/path/to/model.hef
```

## Repository Conventions

Prefer structured configs over hardcoded experiment constants:

- Device configs belong under benchmark-specific `configs/`.
- Dataset paths belong in dataset config files.
- Model lists belong in model config files.
- Scripts should be resumable and should continue to the next model after a failure.

Do not mix research blocks prematurely:

- Detector benchmark belongs in `detector-benchmark/`.
- Tracker benchmark should become its own harness or a clearly separated submodule.
- Lane/LPR/full-pipeline benchmarks should have separate configs and reports.

Reports must distinguish:

- Raw measurements.
- Aggregated metrics.
- Derived rankings.
- Interpretation.
- Known limitations.

## Writing and Analysis Standards

When summarizing results for the thesis:

- Lead with the experimental design and controls.
- State what the result proves and what it does not prove.
- Separate detector accuracy, application throughput, and violation-detection utility.
- Include negative results. Failed or unsuitable models are scientifically useful if logged correctly.
- Do not overclaim legal enforceability.
- Do not claim generalization from a tiny or biased video set.

Use Ukrainian academic novelty language only when it is backed by measurable improvements. A suitable formulation is:

Удосконалено метод виявлення порушень правил дорожнього руху транспортними засобами на основі подієво-керованої обробки відеопотоку на периферійному обчислювальному пристрої, що на відміну від існуючих підходів враховує невизначеність детекції, стабільність супроводу об'єктів та траєкторні показники небезпечної зміни смуги руху, забезпечуючи зменшення енергоспоживання та частоти хибнопозитивних спрацювань.

This statement is only defensible after the project produces numerical evidence for energy reduction, false-positive reduction, and unsafe-lane-change detection quality.

## Immediate Priority

The current priority is Phase 1: detector benchmarking.

Do not start implementing full violation detection until the detector harness is stable and produces reproducible COCO and video-throughput results on the RPi/Hailo target.

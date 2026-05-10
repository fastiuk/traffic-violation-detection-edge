# Benchmarking Methodology

## Key Metrics
- **Hardware Latency:** "Clean" inference time on NPU, isolated from CPU/Bus overhead.
- **FPS (Frames Per Second):** End-to-end throughput including pre/post-processing.
- **Power & Temperature:** Monitored via `hailo monitor`.

## Measurement Procedures

### Pure Hardware Benchmark (CLI)
Use `hailortcli` for baseline performance:
```bash
hailortcli run --measure-latency path/to/model.hef
```

### Application-Level Benchmark (Python)
When running Python scripts:
1. **Warm-up:** Discard first 50-100 frames to reach thermal/clock stability.
2. **Isolation:** Compare CPU vs. NPU on same hardware to identify bus bottlenecks.
3. **Quantization Analysis:** Compare **int8** vs **int4** for latency/accuracy trade-offs.

## Resource Isolation
Different `Hardware Latency` results at identical `FPS` across architectures (x64 vs ARM) indicates that the "bottleneck" is the CPU or Bus, not the NPU.

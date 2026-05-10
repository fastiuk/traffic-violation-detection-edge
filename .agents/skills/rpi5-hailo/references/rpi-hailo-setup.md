# RPi5 & Hailo-8L Setup Details

## Hardware & Connection
- **Host:** Raspberry Pi 5 (8GB)
- **Accelerator:** Hailo-8L (M.2 PCIe)
- **IP Address:** `10.10.10.21`
- **User/Pass:** `pi` / `pi`
- **Connection Method:** SSH (prefers passwordless after key upload)

## Software Environment
- **Project Path:** `~/traffic-violation-detection-edge/`
- **Virtual Environment:** `~/hailo-rpi5-examples/venv_hailo_rpi_examples/`
- **Python Version:** 3.13.5 (Note: HailoRT 4.23.0 might have numpy/ABI sensitivities)
- **HailoRT Version:** 4.23.0

## Key Model Paths
- **YOLOv5s HEF:** `~/traffic-violation-detection-edge/performance-benchmark/models/yolov5s_h8l.hef`
- **YOLOv5s ONNX:** `~/traffic-violation-detection-edge/performance-benchmark/models/yolov5s.onnx`
- **System Models:** `/usr/local/hailo/resources/models/hailo8l/`

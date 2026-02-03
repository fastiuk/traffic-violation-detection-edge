import cv2
import time
import numpy as np
import os
from flask import Flask, Response

try:
    from hailo_platform import VDevice, HEF, FormatType
except ImportError:
    print("Error: hailo_platform module not found.")
    exit(1)

app = Flask(__name__)

hef_path = "hailo_models/yolov5s_h8l.hef"
target = None
infer_model = None
configured_infer_model = None
bindings = None
input_name = None

def init_hailo():
    global target, infer_model, configured_infer_model, bindings, input_name
    
    if not os.path.exists(hef_path):
        print(f"Error: Model file not found at {hef_path}")
        return False

    try:
        params = VDevice.create_params()
        target = VDevice(params)
        
        infer_model = target.create_infer_model(hef_path)
        configured_infer_model = infer_model.configure()
        
        # Manually create output buffers
        output_buffers = {}
        for name in infer_model.output_names:
            shape = infer_model.output(name).shape
            shape = tuple(shape)
            output_buffers[name] = np.zeros(shape, dtype=np.float32)
            
        bindings = configured_infer_model.create_bindings(output_buffers=output_buffers)
        
        input_name = infer_model.input_names[0]
        print("Hailo initialized successfully.")
        return True
    except Exception as e:
        print(f"Hailo init failed: {e}")
        return False

def generate_frames():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open video capture device.")
        return

    input_shape = infer_model.input().shape
    
    if len(input_shape) == 4:
        input_height, input_width = input_shape[1], input_shape[2]
    else:
        input_height, input_width = input_shape[0], input_shape[1]

    frame_count = 0
    start_time = time.time()

    # Explicit activation
    print("Activating Hailo model...")
    configured_infer_model.activate()
    print("Hailo model activated.")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to read frame")
                break

            img = cv2.resize(frame, (input_width, input_height))
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img = np.expand_dims(img, axis=0).astype(np.uint8)
            
            bindings.input().set_buffer(img)
            
            t1 = time.time()
            configured_infer_model.run([bindings], 1000)
            t2 = time.time()
            
            frame_count += 1
            elapsed_time = time.time() - start_time
            fps = frame_count / elapsed_time if elapsed_time > 0 else 0
            inference_time = (t2 - t1) * 1000

            cv2.putText(frame, f"Hailo FPS: {fps:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
            cv2.putText(frame, f"Inf Time: {inference_time:.2f} ms", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()

            if frame_count % 3 == 0:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    except Exception as e:
        print(f"Streaming loop error: {e}")
    finally:
        print("Deactivating Hailo model...")
        configured_infer_model.deactivate()
        cap.release()

@app.route('/')
def index():
    return """
    <html>
    <head><title>Hailo Inference Stream</title></head>
    <body>
        <h1>YOLOv5s Hailo-8L Inference</h1>
        <img src="/video_feed" width="640" height="480">
    </body>
    </html>
    """

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    if init_hailo():
        app.run(host='0.0.0.0', port=5001, debug=False)
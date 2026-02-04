import cv2
import time
import onnxruntime as ort
import numpy as np
from flask import Flask, Response, render_template_string

app = Flask(__name__)

model_path = "/opt/hailo_models/yolov5s.onnx"
session = None
input_name = None
output_name = None
img_height, img_width = 640, 640

def init_model():
    global session, input_name, output_name
    try:
        session = ort.InferenceSession(model_path, providers=['CPUExecutionProvider'])
        input_name = session.get_inputs()[0].name
        output_name = session.get_outputs()[0].name
        print("Model loaded successfully.")
    except Exception as e:
        print(f"Error loading model: {e}")

def generate_frames():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open video capture device.")
        return

    frame_count = 0
    start_time = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Preprocess
        img = cv2.resize(frame, (img_width, img_height))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = img.transpose(2, 0, 1)
        img = np.expand_dims(img, axis=0).astype(np.float32) / 255.0

        # Inference
        t1 = time.time()
        outputs = session.run([output_name], {input_name: img})
        t2 = time.time()

        frame_count += 1
        elapsed_time = time.time() - start_time
        fps = frame_count / elapsed_time if elapsed_time > 0 else 0
        inference_time = (t2 - t1) * 1000

        # Draw FPS
        cv2.putText(frame, f"FPS: {fps:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, f"Inf Time: {inference_time:.2f} ms", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # Encode frame
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()

        # Yield every 3rd frame to reduce streaming overhead
        if frame_count % 3 == 0:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/')
def index():
    return """
    <html>
    <head><title>Hailo Pi CPU Inference</title></head>
    <body>
        <h1>YOLOv5s CPU Inference</h1>
        <img src="/video_feed" width="640" height="480">
    </body>
    </html>
    """

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    init_model()
    # Host on 0.0.0.0 to be accessible from other machines
    app.run(host='0.0.0.0', port=5000, debug=False)

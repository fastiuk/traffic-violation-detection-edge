import cv2
import time
import onnxruntime as ort
import numpy as np
import sys

def main():
    model_path = "/opt/hailo_models/yolov5s.onnx"
    
    # Initialize ONNX Runtime session
    try:
        session = ort.InferenceSession(model_path, providers=['CPUExecutionProvider'])
    except Exception as e:
        print(f"Error loading model: {e}")
        return

    # Get model inputs and outputs
    input_name = session.get_inputs()[0].name
    output_name = session.get_outputs()[0].name
    
    # YOLOv5s standard resolution
    img_height, img_width = 640, 640

    # Initialize video capture
    cap = cv2.VideoCapture(0)
    use_dummy = False
    if not cap.isOpened():
        print("Warning: Could not open video capture device. Switching to Dummy Mode (Performance Test).")
        use_dummy = True
    else:
        print("Camera detected. Starting visual inference.")

    # Warmup
    print("Warming up...")
    dummy_input = np.random.rand(1, 3, img_height, img_width).astype(np.float32)
    for _ in range(5):
        session.run([output_name], {input_name: dummy_input})
    print("Warmup complete.")

    frame_count = 0
    start_time = time.time()
    
    # Run for 100 frames in dummy mode, or indefinitely with camera
    max_frames = 100 if use_dummy else float('inf')

    try:
        while frame_count < max_frames:
            if not use_dummy:
                ret, frame = cap.read()
                if not ret:
                    print("Error: Could not read frame.")
                    break
            else:
                # Create a fake frame
                frame = np.zeros((480, 640, 3), dtype=np.uint8)

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
            fps = frame_count / elapsed_time
            inference_time = (t2 - t1) * 1000

            if not use_dummy:
                cv2.putText(frame, f"FPS: {fps:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.imshow('CPU Inference', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            else:
                if frame_count % 20 == 0:
                    print(f"Frame {frame_count}/{max_frames} - Current FPS: {fps:.2f}")

    except KeyboardInterrupt:
        pass

    if not use_dummy:
        cap.release()
        cv2.destroyAllWindows()
    
    final_fps = frame_count / (time.time() - start_time)
    print(f"\nBenchmark Complete.")
    print(f"Total Frames: {frame_count}")
    print(f"Average CPU FPS: {final_fps:.2f}")

if __name__ == "__main__":
    main()

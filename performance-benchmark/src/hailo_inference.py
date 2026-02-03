import cv2
import time
import numpy as np
import os

# Try to import Hailo libraries
try:
    from hailo_platform import VDevice, HEF, InferVStreams, ConfigureParams, InputVStreamParams, OutputVStreamParams, FormatType, HailoStreamInterface
except ImportError:
    print("Error: hailo_platform module not found. Please ensure Hailo software is installed.")
    exit(1)

def main():
    hef_path = "hailo_models/yolov5s_h8l.hef"
    
    if not os.path.exists(hef_path):
        print(f"Error: Model file not found at {hef_path}")
        return

    # Initialize Hailo
    try:
        params = VDevice.create_params()
        # Select device (Hailo-8)
        with VDevice(params) as target:
            # Load HEF
            hef = HEF(hef_path)
            
            # Configure network
            configure_params = ConfigureParams.create_from_hef(hef, interface=HailoStreamInterface.PCIe)
            network_groups = target.configure(hef, configure_params)
            network_group = network_groups[0]
            
            # Create input/output stream params
            network_group_params = network_group.create_params()
            input_vstreams_params = InputVStreamParams.make(network_group, format_type=FormatType.FLOAT32)
            output_vstreams_params = OutputVStreamParams.make(network_group, format_type=FormatType.FLOAT32)

            # Define input shape (YOLOv5s usually 640x640)
            # We should get this from the HEF ideally
            input_vstream_info = hef.get_input_vstream_infos()[0]
            input_height = input_vstream_info.shape[1]
            input_width = input_vstream_info.shape[2]
            
            print(f"Model Input Shape: {input_width}x{input_height}")

            # Initialize video capture
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                print("Error: Could not open video capture device.")
                return

            print("Starting inference loop. Press 'q' to exit.")
            
            frame_count = 0
            start_time = time.time()

            # Context manager for streams
            with InferVStreams(network_group, input_vstreams_params, output_vstreams_params) as infer_pipeline:
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        print("Error: Could not read frame.")
                        break

                    # Preprocess
                    img = cv2.resize(frame, (input_width, input_height))
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    img = np.expand_dims(img, axis=0).astype(np.float32)
                    
                    # Inference
                    t1 = time.time()
                    # Feed input
                    infer_pipeline.input()[0].send(img)
                    # Get output
                    output = infer_pipeline.output()[0].recv() 
                    # Note: complex models have multiple outputs, might need adjustment
                    t2 = time.time()

                    # FPS Calculation
                    frame_count += 1
                    elapsed_time = time.time() - start_time
                    fps = frame_count / elapsed_time
                    inference_time = (t2 - t1) * 1000 # ms

                    # Display results
                    cv2.putText(frame, f"FPS: {fps:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    cv2.putText(frame, f"Inference: {inference_time:.2f} ms", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    cv2.imshow('Hailo Inference', frame)

                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break

    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()

    cap.release()
    cv2.destroyAllWindows()
    if 'fps' in locals():
        print(f"Average FPS: {fps:.2f}")

if __name__ == "__main__":
    main()

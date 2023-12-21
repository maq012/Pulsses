import cv2
from ultralytics import YOLO

model = YOLO('ml_models/yolov8n.pt')

video_path = "rtsp://admin:hik@12345@172.23.16.55/"

results_generator = model.track(source=video_path, classes=0, stream=True, persist=True, show = True)

# video_cap = cv2.VideoCapture(video_path)

while True:
    print("HEREE")

    # Get results for the current frame
    results = next(results_generator, None)
    anno_frame = results[0].plot
    
    if results is not None:
        print(results[0])
        try:
            # Extract box coordinates
            box = results[0].boxes.xyxy[0].tolist()
            id = results[0].boxes.id[0].item()

            print(f"ids: {id} coordinates: {box}")
        except Exception as e:
            print(f"Error processing result: {e}")
            continue
        # for i in range(len(results[0])):
        #     r = results[0][i]

        #     try:
        #         # Extract box coordinates
        #         box = r.boxes.xyxy[0].tolist()
        #         id = r.boxes.id[0].item()

        #         print(f"ids: {id} coordinates: {box}")
        #     except Exception as e:
        #         print(f"Error processing result: {e}")
        #         continue

    cv2.imshow("Frame", anno_frame)

    if cv2.waitKey(1) == ord("q"):
        break
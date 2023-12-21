import cv2
import os
from ultralytics import YOLO
from datetime import datetime
from Pulsse.database import db
from Pulsse.models.visits import Visits



username = 'admin'
password = 'hik@12345'
ip = '172.23.16.55'
address = f'rtsp://{username}:{password}@{ip}'


def extract_person(key,pulsse_app):
    model = YOLO('yolov8n.pt')
    exit_list = []
    results_generator = model.track(source="C:/Users\92333\PycharmProjects\Pulsses/231123_1.avi", classes=0,
                                    stream=True, persist=True, conf=0.5)

    while True:
        results = next(results_generator, None)
        print(results.boxes.id)

        scale_percent = 20
        frame = results.plot()
        width = int(frame.shape[1] * scale_percent / 100)
        height = int(frame.shape[0] * scale_percent / 100)
        dim = (width, height)
        resized = cv2.resize(frame, dim, interpolation=cv2.INTER_AREA)
        cv2.imshow("YOLOv8 Inference", resized)

        # Break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

        if results.boxes.id is not None:

            box = results.boxes.xyxy.tolist()
            id = results.boxes.id.tolist()
            frame_counting_buffer = dict(zip(id, box))
            print(frame_counting_buffer)

            frame_counting_buffer = {key: frame_counting_buffer[key] for key in frame_counting_buffer.keys()
                                        if str(key) not in exit_list}
            frame_counting_buffer = {key: values for key, values in frame_counting_buffer.items() if
                                        values[3] > 900}
            exit_list = list(set(exit_list))

            base_directory = f"C:/Users\92333\PycharmProjects\Pulsses\Object_Tracking\Images{key}/"
            for idx, values in frame_counting_buffer.items():
                folder_names = os.listdir(base_directory)
                if str(idx) not in folder_names:
                    if values[3] > 1400:
                        exit_list.append(str(idx))
                        with pulsse_app.app_context():
                            visit = Visits()
                            visit.yolo_id = int(idx)
                            visit.sitekey = key
                            visit.time_out = datetime.now().time()
                            if len(frame_counting_buffer) > 1:
                                visit.group_val = True
                            db.session.add(visit)
                            db.session.commit()
                    else:
                        os.mkdir(os.path.join(base_directory, str(idx)))
                        with pulsse_app.app_context():
                            visit = Visits()
                            visit.yolo_id = int(idx)
                            visit.sitekey = key
                            visit.time_in = datetime.now().time()
                            if len(frame_counting_buffer) > 1:
                                visit.group_val = True
                            db.session.add(visit)
                            db.session.commit()
                else:
                    output_path = os.path.join(base_directory, str(idx),
                                                f"{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg")
                    if len(os.listdir(os.path.join(base_directory, str(idx)))) < 7:
                        img = frame[int(values[1]):int(values[3]), int(values[0]):int(values[2])]
                        cv2.imwrite(output_path, img)
                    else:
                        pass

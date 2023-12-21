import cv2
import os
from flask import Blueprint, Response
from ultralytics import YOLO
from datetime import datetime
import threading
from Pulsse import pulsse_app
from ..database import db
from Pulsse.models.visits import Visits

extract_person_blueprint = Blueprint('extract_person', __name__, url_prefix='/extract_person')


model = YOLO('ml_models/yolov8s.pt')

username = 'admin'
password = 'hik@12345'
ip = '172.23.16.55'
address = f'rtsp://{username}:{password}@{ip}'

model = YOLO('yolov8n.pt')
video_path = address
key = 1
exit_list = []

results_generator = model.track(source=video_path, classes=0, stream=True, persist=True, imgsz=(2560))

    # print(results_generator)
    

while True:
        results = next(results_generator, None)
        print(results.boxes.id)
        if results.boxes.id is not None:

            anno_frame = results.plot()
            cv2.imshow('data', anno_frame)
            cv2.waitKey(2)

            # Extract box coordinates
            box = results.boxes.xyxy.tolist()
            id = results.boxes.id.tolist()
            frame_counting_buffer = dict(zip(id, box))
            print(frame_counting_buffer)

            frame_counting_buffer = {key: frame_counting_buffer[key] for key in frame_counting_buffer.keys()
                                        if str(key) not in exit_list}
            frame_counting_buffer = {key: values for key, values in frame_counting_buffer.items() if
                                        values[3] > 500}
            exit_list = list(set(exit_list))

            base_directory = f"C:/Users\DL\Downloads\Pulsse\Pulsse\Object_Tracking\Images{key}/"
            for idx, values in frame_counting_buffer.items():
                folder_names = os.listdir(base_directory)
                if str(idx) not in folder_names:
                    if values[3] > 600:
                        exit_list.append(str(idx))
                        # with pulsse_app().app_context():
                        #     visit = Visits()
                        #     visit.yolo_id = int(idx)
                        #     visit.sitekey = key
                        #     visit.time_out = datetime.now().time()
                        #     if len(frame_counting_buffer) > 1:
                        #         visit.group_val = True
                        #     db.session.add(visit)
                        #     db.session.commit()
                    else:
                        os.mkdir(os.path.join(base_directory, str(idx)))
                        # with pulsse_app().app_context():
                        #     visit = Visits()
                        #     visit.yolo_id = int(idx)
                        #     visit.sitekey = key
                        #     visit.time_in = datetime.now().time()
                        #     if len(frame_counting_buffer) > 1:
                        #         visit.group_val = True
                        #     db.session.add(visit)
                        #     db.session.commit()
                else:
                    output_path = os.path.join(base_directory, str(idx),
                                                f"{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg")
                    if len(os.listdir(os.path.join(base_directory, str(idx)))) < 7:
                        img = anno_frame[int(values[1]):int(values[3]), int(values[0]):int(values[2])]
                        cv2.imwrite(output_path, img)
                    else:
                        pass
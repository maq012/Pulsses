# import cv2
# import os

# from datetime import datetime

# import pandas as pd
# from ultralytics import YOLO

# exit_list = []
# data_list = []
# filtered_persons = {}
# cap = cv2.VideoCapture("rtsp://admin:hik@12345@172.23.16.55/")
# model = YOLO('ml_models/yolov8n.pt')


# while cap.isOpened():
#     success, frame = cap.read()

#     if success:
#         results = model.track(frame, persist=True, classes=0)
#         annotated_frame = results[0].plot()

#         scale_percent = 20
#         width = int(frame.shape[1] * scale_percent / 100)
#         height = int(frame.shape[0] * scale_percent / 100)
#         dim = (width, height)
#         resized = cv2.resize(annotated_frame, dim, interpolation=cv2.INTER_AREA)
#         cv2.imshow("YOLOv8 Inference", resized)

#         result = results[0].cpu().boxes
#         detect_id = result.id.tolist() if result.id != None else []
#         detect_xyxy = result.xyxy.tolist() if result.xyxy != None else []
#         frame_counting_buffer = dict(zip(detect_id, detect_xyxy))
#         frame_counting_buffer = {key: frame_counting_buffer[key] for key in frame_counting_buffer.keys()
#                                  if str(key) not in exit_list}
#         frame_counting_buffer = {key: values for key, values in frame_counting_buffer.items() if values[3] > 900}
#         exit_list = list(set(exit_list))

#         extraction = {'ID': '', 'info_date':'', 'time_in': '', 'time_out': '', 'Group': ''}
#         base_directory = './Image_folder/'
#         for idx, values in frame_counting_buffer.items():
#             folder_names = os.listdir(base_directory)
#             if str(idx) not in folder_names:
#                 if values[3] > 1400:
#                     exit_list.append(str(idx))
#                     extraction['ID'] = int(idx)
#                     extraction['info_date'] = datetime.now().strftime('%Y%m%d')
#                     extraction['time_out'] = datetime.now().strftime('%H%M%S')
#                     data_list.append(extraction)
#                     data = pd.DataFrame(data_list)
#                     data.to_csv('Extracted_Data/Data.csv')
#                 else:
#                     os.mkdir(os.path.join(base_directory, str(idx)))
#                     extraction['ID'] = int(idx)
#                     extraction['info_date'] = datetime.now().strftime('%Y%m%d')
#                     extraction['time_in'] = datetime.now().strftime('%H%M%S')
#                     data_list.append(extraction)
#                     data = pd.DataFrame(data_list)
#                     data.to_csv('Extracted_Data/Data.csv')
#             else:
#                 output_path = os.path.join(base_directory, str(idx), f"{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg")
#                 if len(os.listdir(os.path.join(base_directory, str(idx)))) < 7:
#                     img = frame[int(values[1]):int(values[3]), int(values[0]):int(values[2])]
#                     cv2.imwrite(output_path, img)
#                 else:
#                     pass

#         if cv2.waitKey(1) & 0xFF == ord("q"):
#             break
#     else:
#         break

# cap.release()
# cv2.destroyAllWindows()

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


def extract_person(model, video_path, key):

    global exit_list
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
                        with pulsse_app().app_context():
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
                        with pulsse_app().app_context():
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
                        img = anno_frame[int(values[1]):int(values[3]), int(values[0]):int(values[2])]
                        cv2.imwrite(output_path, img)
                    else:
                        pass

def run_extraction_thread(key):
    threading.daemon = True
    threading.Thread(target=extract_person, args=(model, video_path, key)).start()                    


@extract_person_blueprint.route('/key1')
def extract_person_key1_route():
    key = 1
    video_path = "rtsp://admin:hik@12345@172.23.16.55/"
    run_extraction_thread(key)
    return Response(response="Extraction for key 1 completed.", status=200)

@extract_person_blueprint.route('/key2')
def extract_person_key2_route():
    key = 2
    video_path = "rtsp://admin:hik@12345@172.23.16.55/"
    run_extraction_thread(key)
    return Response(response="Extraction for key 2 completed.", status=200)

@extract_person_blueprint.route('/key3')
def extract_person_key3_route():
    key = 3
    video_path = "rtsp://admin:hik@12345@172.23.16.55/"
    run_extraction_thread(key)
    return Response(response="Extraction for key 3 completed.", status=200)

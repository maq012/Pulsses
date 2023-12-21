import cv2
import os
import pandas as pd

from flask import Blueprint, Response
from ultralytics import YOLO
from datetime import datetime
from Pulsse.database import db
from Pulsse.models.visits import Visits
from Pulsse import pulsse_app

frames_blueprint = Blueprint('/', __name__, url_prefix='/')

def gen_frames(model, link, key):
    
    results_generator = model.track(source=link, classes=0, stream=True, persist=True, conf=0.5)
    while True:
        results = next(results_generator, None)
        anno_frame = results.plot()
        scale_percent = 20
        width = int(anno_frame.shape[1] * scale_percent / 100)
        height = int(anno_frame.shape[0] * scale_percent / 100)
        dim = (width, height)
        resized = cv2.resize(anno_frame, dim, interpolation=cv2.INTER_AREA)
        _, buffer = cv2.imencode('.jpg', resized)
        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + bytearray(buffer) + b'\r\n')

        #     box = results.boxes.xyxy.tolist()
        #     id = results.boxes.id.tolist()
        #     frame_counting_buffer = dict(zip(id, box))

        #     print(frame_counting_buffer)
        #     frame_counting_buffer = {key: frame_counting_buffer[key] for key in frame_counting_buffer.keys()
        #                                 if str(key) not in exit_list}
        #     frame_counting_buffer = {key: values for key, values in frame_counting_buffer.items() if
        #                                 values[3] > 900}
        #     exit_list = list(set(exit_list))

        #     base_directory = "C:/Users\DL\Downloads\Pulsse-hareem\Pulsse-hareem\Object_Tracking\Images/"
        #     for idx, values in frame_counting_buffer.items():
        #         folder_names = os.listdir(base_directory)
        #         if str(idx) not in folder_names:
        #             if values[3] > 1400:
        #                 exit_list.append(str(idx))
        #                 with pulsse_app().app_context():
        #                     visit = Visits()
        #                     visit.yolo_id = int(idx)
        #                     visit.sitekey = key
        #                     # visit.day = datetime.now().strftime('%Y%m%d')
        #                     visit.time_out = datetime.now().time()
        #                     if len(frame_counting_buffer) > 1:
        #                         visit.group_val=True
        #                     db.session.add(visit)
        #                     db.session.commit()
        #             else:
        #                 os.mkdir(os.path.join(base_directory, str(idx)))
        #                 with pulsse_app().app_context():
        #                     visit = Visits()
        #                     visit.yolo_id = int(idx)
        #                     visit.sitekey = key
        #                     # visit.day = datetime.now().strftime('%Y%m%d')
        #                     visit.time_in = datetime.now().time()
        #                     if len(frame_counting_buffer) > 1:
        #                         visit.group_val=True
        #                     db.session.add(visit)
        #                     db.session.commit()
        #         else:
        #             output_path = os.path.join(base_directory, str(idx),
        #                                         f"{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg")
        #             if len(os.listdir(os.path.join(base_directory, str(idx)))) < 7:
        #                 img = anno_frame[int(values[1]):int(values[3]), int(values[0]):int(values[2])]
        #                 cv2.imwrite(output_path, img)
        #             else:
        #                 pass



@frames_blueprint.route('video_feed/<int:key>', methods=['GET'])
def video_feed(key):
    if key== 1:
        videolink = "rtsp://admin:hik@12345@172.23.16.55/"
    if key==2:
        videolink = "rtsp://admin:hik@12345@172.23.16.55/"
    if key==3:
        videolink = "rtsp://admin:hik@12345@172.23.16.55/"
        #videolink = "C:\\Users\\ahare\\Downloads\\Untitled video - Made with Clipchamp.mp4"
    # cap = cv2.VideoCapture(videolink)
    # print(cap)
    # success, frame = cap.read()
    # print(success)
    # fps = cap.get(5)
    # print(fps)

    model = YOLO('ml_models/yolov8n.pt')

    return Response(gen_frames(model, videolink, key), mimetype='multipart/x-mixed-replace; boundary=frame')
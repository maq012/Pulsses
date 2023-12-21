import os
import numpy as np
import time
import glob
import shutil
import cv2
import pandas as pd

import sqlalchemy
import matplotlib.pyplot as plt

from deepface import DeepFace
from collections import Counter
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import ARRAY
from datetime import date


def analyze_person(key):
    database_url = 'postgresql://postgres:12345@localhost:5432/Pulsse'
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    directory_path = f'C:/Users\92333\PycharmProjects\Pulsses\Object_Tracking\Images{key}/'
    person_list = []
    today_date = date.today()
    GENDER_PROTO = "C:/Users\92333\PycharmProjects\Pulsses\Pulsse/utils\ml_models/deploy_gender.prototxt"
    GENDER_MODEL = "C:/Users\92333\PycharmProjects\Pulsses\Pulsse/utils\ml_models/gender_net.caffemodel"
    GENDER_NET = cv2.dnn.readNet(GENDER_MODEL, GENDER_PROTO)
    MODEL_MEAN_VALUES = (78.4263377603, 87.7689143744, 114.895847746)
    GENDER_LIST = ['Male', 'Female']
    metrics = ["cosine", "euclidean", "euclidean_l2"]
    backends = [
        'opencv',
        'ssd',
        'dlib',
        'mtcnn',
        'retinaface',
        'mediapipe'
    ]
    models = [
        "VGG-Face",
        "Facenet",
        "Facenet512",
        "OpenFace",
        "DeepFace",
        "DeepID",
        "ArcFace",
        "Dlib",
        "SFace",
    ]


    def check_for_folder(directory):
        if os.path.exists(directory) and os.path.isdir(directory):
            return True
        else:
            return False


    def get_images_in_folder(directory_path, folder_path):
        image_files = glob.glob(os.path.join(directory_path, folder_path, '*.jpg'))  # Adjust the pattern if needed
        return image_files


    def predict_gender(male, female, s1):
        # result = DeepFace.analyze(s1, actions=['gender'], enforce_detection=False,
        #                           detector_backend = backends[8])
        blob = cv2.dnn.blobFromImage(s1, 1, (227, 227), MODEL_MEAN_VALUES, swapRB=False)
        # blobb = blob.reshape(blob.shape[2] * blob.shape[1], blob.shape[3], 1)
        # cv2.imshow('Blob', blobb)
        # cv2.waitKey(5000)
        GENDER_NET.setInput(blob)
        gender_predictions = GENDER_NET.forward()
        gender = GENDER_LIST[gender_predictions[0].argmax()]
        print("Gender: {}, conf: {:.3f}".format(gender, gender_predictions[0].max()))
        if str(gender) == 'Male':
            male = male + 1
        elif str(gender) == 'Female':
            female = female + 1
        return male, female


    def get_embeddings(image):
        image_embedding = DeepFace.represent(image, model_name=models[1], enforce_detection=False)
        print("Embedding: ", type(image_embedding[0]['embedding']))
        return image_embedding[0]['embedding']


    def get_facial_match(img_embedding, customers):
        facial_distances = []
        for cust in customers:
            facial_distance = {'id': '', 'distance': ''}
            dist = np.linalg.norm(np.array(img_embedding) - np.array(cust.image))
            facial_distance['id'] = int(cust.id)
            facial_distance['distance'] = dist
            facial_distances.append(facial_distance)

        if facial_distances:
            min_distance_dict = min(facial_distances, key=lambda x: x['distance'])
            return min_distance_dict
        else:
            return None


    while True:
        if check_for_folder(directory_path):
            folder_contents = os.listdir(directory_path)
            folder_contents = sorted(map(float, folder_contents))
            print(folder_contents)
            cust_id = 0
            for id in folder_contents:
                print("Folder id", id)
                # person_list = []
                db_image = None
                male = 0
                female = 0
                list_of_embeddings = []
                id_counts = []
                data = {'yolo_id': int(id), 'customer_id': ''}
                list_of_images = get_images_in_folder(directory_path, str(id))
                # print(id)
                match = []
                first_image_embedding = False
                for img in list_of_images:
                    img = cv2.imread(img)
                    height = img.shape[0]
                    height_cutoff = height // 5
                    img = img[:height_cutoff, :]
                    kernel = np.array([[0, -1, 0],
                                       [-1, 5, -1],
                                       [0, -1, 0]])
                    alt_img = cv2.filter2D(src=img, ddepth=-1, kernel=kernel)
                    male, female = predict_gender(male, female, alt_img)
                    img_embedding = get_embeddings(img)

                    if first_image_embedding is False:
                        db_image = img_embedding
                        first_image_embedding = True

                    list_of_embeddings.append(img_embedding)
                    with engine.connect() as connection:
                        query = text("SELECT * FROM Customers")
                        customers = connection.execute(query)
                        result_set = customers.fetchall()

                        # cust_id = len(result_set)
                        # print("Cust_id",cust_id)
                        # if not match or match['distance'] > 5:

                match = get_facial_match(db_image, result_set)
                print(match)

                gender = None
                if male > female:
                    data['Gender'] = 'Male'
                    gender = 'Male'
                elif female > male:
                    data['Gender'] = 'Female'
                    gender = 'Female'

                if match and match['distance'] <= 5:
                    data['customer_id'] = match['id']
                else:
                    with engine.connect() as connection:
                        db_image_str = ', '.join(map(str, db_image))
                        db_image_str_with_braces = f'{{{db_image_str}}}'
                        query = text(
                            "INSERT INTO customers (gender, image, created_at, modified_at) "
                            f"VALUES ('{gender}', '{db_image_str_with_braces}','{today_date}', '{today_date}') "
                            "RETURNING id"  # Include the column you want to return
                        )

                        result = connection.execute(query)

                        # Fetch the inserted customer_id
                        cust_id_result = result.fetchone()

                        if cust_id_result is not None:
                            cust_id = cust_id_result[0]
                            data['customer_id'] = cust_id
                        else:
                            # Handle the case when there is no result
                            print("No customer_id returned from the query.")

                        connection.commit()

                # id_counts = Counter(id_counts)

                # print("ID COUNT: ",id_counts)
                # if id_counts:
                #     most_common_id, most_common_count = id_counts.most_common(1)[0]
                #     data['customer_id'] = most_common_id

                directory_to_remove = directory_path+str(data['yolo_id'])
                shutil.rmtree(directory_to_remove)
                person_list.append(data)

        print(len(person_list))
        data = pd.DataFrame(person_list)
        print(data)
        for id, val in data.iterrows():
            with engine.connect() as connection:
                query = text(
                    "UPDATE visits SET customer_id = :customer_id WHERE yolo_id = :yolo_id and customer_id is NULL")
                params = {'customer_id': val['customer_id'], 'yolo_id': val['yolo_id']}
                connection.execute(query, params)
                connection.commit()
                # connection.execute(text(f"INSERT INTO visits (day, time_in, time_out) VALUES ('{info_date}', '{time_in}', '{time_out}')"))
        time.sleep(30)

# import os
# import numpy as np
# import time
# import glob
# import shutil
# import cv2
# import pandas as pd

# import sqlalchemy
# import matplotlib.pyplot as plt

# from deepface import DeepFace
# from collections import Counter
# from sqlalchemy import create_engine, text
# from sqlalchemy.orm import sessionmaker
# from sqlalchemy.dialects.postgresql import ARRAY

# database_url = 'postgresql://postgres:serG@localhost:5432/Pulsse'
# engine = create_engine(database_url)
# Session = sessionmaker(bind=engine)
# session = Session()

# directory_path = 'Image_folder/'
# person_list = []
# GENDER_PROTO = "ml_models/deploy_gender.prototxt"
# GENDER_MODEL = "ml_models/gender_net.caffemodel"
# GENDER_NET = cv2.dnn.readNet(GENDER_MODEL, GENDER_PROTO)
# MODEL_MEAN_VALUES = (78.4263377603, 87.7689143744, 114.895847746)
# GENDER_LIST=['Male', 'Female']
# metrics = ["cosine", "euclidean", "euclidean_l2"]
# backends = [
#   'opencv',
#   'ssd',
#   'dlib',
#   'mtcnn',
#   'retinaface',
#   'mediapipe'
# ]
# models = [
#   "VGG-Face",
#   "Facenet",
#   "Facenet512",
#   "OpenFace",
#   "DeepFace",
#   "DeepID",
#   "ArcFace",
#   "Dlib",
#   "SFace",
# ]


# def check_for_folder(directory):
#     if os.path.exists(directory) and os.path.isdir(directory):
#         return True
#     else:
#         return False


# def get_images_in_folder(directory_path, folder_path):
#     image_files = glob.glob(os.path.join(directory_path, folder_path, '*.jpg'))  # Adjust the pattern if needed
#     return image_files


# def predict_gender(male, female, s1):
#     # result = DeepFace.analyze(s1, actions=['gender'], enforce_detection=False,
#     #                           detector_backend = backends[8])
#     blob = cv2.dnn.blobFromImage(s1, 1, (227, 227), MODEL_MEAN_VALUES, swapRB=False)
#     # blobb = blob.reshape(blob.shape[2] * blob.shape[1], blob.shape[3], 1)
#     # cv2.imshow('Blob', blobb)
#     # cv2.waitKey(5000)
#     GENDER_NET.setInput(blob)
#     gender_predictions = GENDER_NET.forward()
#     gender = GENDER_LIST[gender_predictions[0].argmax()]
#     print("Gender: {}, conf: {:.3f}".format(gender, gender_predictions[0].max()))
#     if str(gender) == 'Male':
#         male = male + 1
#     elif str(gender) == 'Female':
#         female = female + 1
#     return male, female


# def get_embeddings(image):
#     image_embedding = DeepFace.represent(image, model_name=models[1], enforce_detection=False)
#     return image_embedding[0]['embedding']


# def get_facial_match(img_embedding, customers):
#     facial_distances = []
#     for cust in customers:
#         # print(len(np.array(img_embedding)))
#         # print(len(np.array(cust.image)))
#         # similarity = DeepFace.verify(np.array(img_embedding), np.array(cust.image), model_name=models[1])
#         # print(similarity)
#         facial_distance = {'id': '', 'distance': ''}
#         dist = np.linalg.norm(np.array(img_embedding) - np.array(cust.image))
#         facial_distance['id'] = int(cust.id)
#         facial_distance['distance'] = dist
#         facial_distances.append(facial_distance)
#     min_distance_dict = min(facial_distances, key=lambda x: x['distance'])
#     return min_distance_dict


# while True:
#     if check_for_folder(directory_path):
#         folder_contents = os.listdir(directory_path)
#         folder_contents = sorted(map(float, folder_contents))
#         print(folder_contents)
#         for id in folder_contents:
#             male = 0
#             female = 0
#             list_of_embeddings = []
#             id_counts = []
#             data = {'yolo_id': int(id), 'customer_id': ''}
#             list_of_images = get_images_in_folder(directory_path, str(id))
#             print(id)
#             for img in list_of_images:
#                 img = cv2.imread(img)
#                 height = img.shape[0]
#                 height_cutoff = height // 5
#                 img = img[:height_cutoff, :]
#                 kernel = np.array([[0, -1, 0],
#                                    [-1, 5, -1],
#                                    [0, -1, 0]])
#                 alt_img = cv2.filter2D(src=img, ddepth=-1, kernel=kernel)
#                 # plt.imshow(alt_img)
#                 # plt.show()
#                 male, female = predict_gender(male, female, alt_img)
#                 img_embedding = get_embeddings(img)
#                 list_of_embeddings.append(img_embedding)
#                 with engine.connect() as connection:
#                     query = text("SELECT * FROM Customers")
#                     customers = connection.execute(query)
#                 match = get_facial_match(img_embedding, customers)
#                 id_counts.append(match['id'])
#             id_counts = Counter(id_counts)
#             most_common_id, most_common_count = id_counts.most_common(1)[0]
#             if male > female:
#                 data['Gender'] = 'Male'
#             elif female > male:
#                 data['Gender'] = 'Female'
#             data['customer_id'] = most_common_id
#     #         # directory_to_remove = directory_path+str(data['ID'])
#     #         # shutil.rmtree(directory_to_remove)
#             person_list.append(data)

#     print(len(person_list))
#     data = pd.DataFrame(person_list)
#     print(data)
#     for id, val in data.iterrows():
#         with engine.connect() as connection:
#             query = text("UPDATE visits SET customer_id = :customer_id WHERE yolo_id = :yolo_id")
#             params = {'customer_id': val['customer_id'], 'yolo_id': val['yolo_id']}
#             connection.execute(query, params)
#             connection.commit()
#             # connection.execute(text(f"INSERT INTO visits (day, time_in, time_out) VALUES ('{info_date}', '{time_in}', '{time_out}')"))
#     connection.close()
#     time.sleep(30)

import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

import cv2 as cv

base_options = python.BaseOptions(model_asset_path='assets/models/hand_landmarker.task')
options = vision.HandLandmarkerOptions(base_options=base_options,
                                      num_hands=2)
detector = vision.HandLandmarker.create_from_options(options)

# Return a dictionary of hand landmark coordinates and annotated image
def obtain_landmarks(shape, img):
  # Image shape
  width, length = shape[0], shape[1]

  # Convert image to correct type
  numpy_image = cv.cvtColor(img, cv.COLOR_BGR2RGB)

  # Load input image
  rgb_frame = mp.Image(image_format=mp.ImageFormat.SRGB, data=numpy_image)
  
  # Detect hand landmarks
  detection_result = detector.detect(rgb_frame)

  # Retrieve hand landmarks coordinates
  landmarks = detection_result.hand_landmarks[0]

  # Iterate through landmarks, store in dictionary
  landmarks_dict = {}
  for index in range(len(landmarks)):
    landmarks_dict[index] = [int(landmarks[index].x * length), 
                             int(landmarks[index].y * width)]

  return landmarks_dict

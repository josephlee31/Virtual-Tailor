""" Helper script that contains all GCP-related functions. """
# Install dependencies
from google.cloud import storage
import cv2 as cv
import numpy as np

# Local helper functions
import helpers.config as config

# Establish GCP connection using Service Account Key.
service_account_key = 'path_to_key'
storage_client = storage.Client.from_service_account_json(service_account_key)
bucket = storage_client.bucket('mediaupload-9b88f.appspot.com')

####################################
### Function definitions
####################################
def download_imgs(ID):
    """ Function for downloading images from GCP.
    Arguments:
        - ID (string): Case ID of current user.
    Returns:
        - backHand_img (OpenCV img): OpenCV-imported image of the Back Hand.
        - frontHand_img (OpenCV img): OpenCV-imported image of the Front Hand.
        - sideHand_img (OpenCV img): OpenCV-imported image of the Side Hand.
    """
    # Download the back hand as a string.
    file_to_download = f"{config.DSP_INPUT}/{ID}/backHand.jpg"
    blob = bucket.blob(file_to_download)
    backHand_img_data = blob.download_as_string()

    # Download the front hand as a string
    file_to_download = f"{config.DSP_INPUT}/{ID}/frontHand.jpg"
    blob = bucket.blob(file_to_download)
    frontHand_img_data = blob.download_as_string()

    # # Download the side hand as a string
    file_to_download = f"{config.DSP_INPUT}/{ID}/sideHand.jpg"
    blob = bucket.blob(file_to_download)
    sideHand_img_data = blob.download_as_string()

    # Import the image using OpenCV.
    backHand_img = cv.imdecode(np.frombuffer(backHand_img_data, np.uint8), cv.IMREAD_COLOR)
    frontHand_img = cv.imdecode(np.frombuffer(frontHand_img_data, np.uint8), cv.IMREAD_COLOR)
    sideHand_img = cv.imdecode(np.frombuffer(sideHand_img_data, np.uint8), cv.IMREAD_COLOR)

    return backHand_img, frontHand_img, sideHand_img

def upload_file(filepath, ID, filename):
    file_to_upload = filepath
    blob = bucket.blob(f"{config.DSP_OUTPUT}/{ID}{filename}")
    blob.upload_from_filename(file_to_upload)

def upload_opencv_img(img, output_blob_name):
    _, image_data = cv.imencode('.jpg', img)
    blob = bucket.blob(config.DSP_OUTPUT + "/" + output_blob_name)
    blob.upload_from_string(image_data.tobytes(), content_type='image/jpeg')

# Function for creating a download link.
def generate_download_link(ID, filename):
    blob = bucket.blob(config.DSP_OUTPUT + "/" + f"{ID}{filename}")

    # Generate signed URL with expiration time (e.g., valid for 1 hour)
    url = blob.generate_signed_url(
        version='v4',
        expiration=3600,  # Expiration time in seconds (1 hour in this case)
        method='GET',
        response_disposition='attachment'
    )
    return url

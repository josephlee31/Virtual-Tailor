from rembg import remove

import helpers.mediapipe_funs as mediapipe_funs
import cv2 as cv
import numpy as np
import pyvista as pv
import bpy
import math

# Function used to segment the hand from background.
def remove_bg(img):
    output = remove(img)
    return output

# Function to compute thickness.
def get_thickness(side_mask):
    # Load Aruco detector
    parameters = cv.aruco.DetectorParameters()
    aruco_dict = cv.aruco.getPredefinedDictionary(cv.aruco.DICT_4X4_250)

    # Convert image to Grayscale
    img = cv.cvtColor(side_mask, cv.COLOR_BGR2GRAY)
    # cv.imwrite('test.png', img)

    # Detect Aruco markers
    corners, ids, _ = cv.aruco.detectMarkers(img, aruco_dict, parameters=parameters)

    # Draw polygon around the marker
    int_corners = np.intp(corners)

    # Compute Aruco perimter, and obtain pixel-per-cm-ratio
    aruco_perimeter = cv.arcLength(corners[0], True)
    # Pixel to cm ratio (Aruco Marker perimeter is 16cm)
    pixel_cm_ratio = aruco_perimeter / 16
    dist = round((abs(corners[0][0][0][0] - corners[1][0][0][0]) * 1)/pixel_cm_ratio, 3)
    print(f"The thickness is {dist} cm.")
    return dist

# Function that performs the entire image processing function.
def process_img(backHand_segmented, backHand_img, frontHand_segmented, frontHand_img, ID):
    # Create a mask of the hand brace.
    backHand_mask = create_mask(backHand_img, backHand_segmented, 0)
    frontHand_mask = create_mask(frontHand_img, frontHand_segmented, 1)

    return backHand_mask, frontHand_mask

def create_mask(img, segmented_img, orientation):
    # Obtain image shape
    img_shape = img.shape

    # Obtain landmarks
    landmarks = mediapipe_funs.obtain_landmarks(img_shape, img)

    # Obtain contour of image
    contour = determine_contour(segmented_img)

    # Create copy of image
    img_cp = segmented_img.copy()

    # Convert contours to Pythonic list
    contour_list = contour[0].tolist()

    # First segmentation stage (Segment between landmark #5 and #17)
    keypoints = []
    for landmark_index in [5, 17]:
        coord = find_min_distance(contour, landmark_index, landmarks)
        keypoints.append(coord)

    # Find where landmark #5 and #17 are located within contour
    crop_kp_indices = []
    for point in keypoints:
        index = contour_list.index([point[0].tolist()])
        crop_kp_indices.append(index)
    
    crop_kp_indices.sort()

    # Second segmentation stage
    thumb_coord = find_min_distance(contour, 2, landmarks)
    thumb_index = contour_list.index([thumb_coord[0].tolist()])

    # Segment contour
    if orientation == 0:
        contour_segmented_1 = contour_list[crop_kp_indices[0]:thumb_index] + [contour_list[crop_kp_indices[1]]]
        contour_segmented_1 = np.array([contour_segmented_1])

    elif orientation == 1:
        contour_segmented_1 = [contour_list[crop_kp_indices[0]]] + contour_list[thumb_index:crop_kp_indices[1]]
        contour_segmented_1 = np.array([contour_segmented_1])

    # Create binarized mask
    mask = np.zeros_like(img_cp[:, :, 0], img_cp.dtype)
    cv.drawContours(mask, contour_segmented_1, -1, (255), thickness=cv.FILLED)

    # Apply mask to image
    masked_img = cv.bitwise_and(segmented_img, segmented_img, mask = mask)
    return masked_img

def determine_contour(img):
    # Convert image to grayscale
    img_gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)

    # Apply binary thresholding
    _ ,thresh = cv.threshold(img_gray, 80, 255, cv.THRESH_BINARY)

    # Apply contour
    contours, _ = cv.findContours(thresh, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

    # Display contour
    mask = np.zeros_like(img_gray)
    cv.drawContours(mask, contours, -1, (255), thickness=3)

    min_contour_area = 1000000  # Adjust this value as needed
    filtered_contours = [cnt for cnt in contours if cv.contourArea(cnt) >= min_contour_area]

    return filtered_contours

def find_min_distance(contour, index, landmarks):
    # Initialize distance and coordinate variables
    min_dist = None
    coord = None

    # Iterate through entire contour
    for point in range(len(contour[0])):
        current_distance = abs(cv.pointPolygonTest(contour[0][point],
                                               (landmarks[index][0],
                                                landmarks[index][1]),
                                                True))
        if point == 0:
                min_dist = current_distance
                coord = contour[0][point]
        else:
            if current_distance < min_dist:
                min_dist = current_distance
                coord = contour[0][point]

    return coord

def compute_cloud(img):
    # Obtain image shape
    img_height = img.shape[0]
    img_width = img.shape[1]

    # Convert image to grayscale
    img_gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)

    # Initialize empty array to store points
    point_cloud = []

    # Iterate through all pixels of image
    for col in range(0, img_width):
        if col%2 == 0:
            continue
        else:
            for row in range(0, img_height):
                pixel = img_gray[row, col]
                if pixel != 0:
                    point_cloud.append([row, col, pixel])

    # Convert point cloud to numpy array
    point_cloud = np.array(point_cloud)

    # Remove outliers
    point_cloud = process_cloud(point_cloud)
    return point_cloud


def process_cloud(point_cloud):
    z_coordinates = point_cloud[:, 2]

    # Compute point outliers using z-score
    outliers = find_outliers(z_coordinates)

    # Remove outliers
    point_cloud = point_cloud[~outliers]

    return point_cloud 

def find_outliers(data, threshold=3):
    z_scores = (data - np.mean(data)) / np.std(data)
    return np.abs(z_scores) > threshold

def compute_mesh(point_cloud, temp_files_path, thickness, name):
    # Normalize point-cloud to be positioned on centroid
    centroid = np.mean(point_cloud, axis=0)
    point_cloud = point_cloud - centroid

    point_cloud = point_cloud*0.0001

    # Reduce point-cloud
    while len(point_cloud) > 100000:
        point_cloud = point_cloud[::2]

    # Compute point-cloud
    cloud = pv.PolyData(point_cloud)

    # Compute mesh
    mesh = cloud.delaunay_2d(progress_bar=True)
    mesh = mesh.smooth(n_iter=2500, progress_bar=True)

    vertices = mesh.points
    faces = mesh.faces.reshape(-1, 4)[:, 1:]

    # Create Blender mesh
    blender_mesh = bpy.data.meshes.new(name)
    blender_mesh.from_pydata(vertices, [], faces)

    # Deselect all
    objs = bpy.data.objects
    try:
        objs.remove(objs["Cube"], do_unlink=True)
    except:
        pass

    # Create Blender object and link the mesh to it
    object = bpy.data.objects.new(name, blender_mesh)
    bpy.context.collection.objects.link(object)

    # # Apply Solidify modifier and thickness of 2mm
    solidify_modifier = object.modifiers.new(name="Solidify", type='SOLIDIFY')
    solidify_modifier.thickness = 0.001  # Adjust the thickness value as needed

    # Scale up the mesh
    ## Get z-dimension of stl
    # print("Dimensions (X, Y, Z):", object.dimensions)
    observed_thickness = object.dimensions[2]*100

    # Determine scale factor, from aruco marker length
    scale_factor = (thickness/2)/observed_thickness
    # scale_factor_z = true_thickness/observed_thickness

    # Set the scale factors
    # scale_factor_z = 2.5  # Adjust the scale factor as needed
    object.scale.z *= scale_factor
    print(object.dimensions[2])

    if name == "frontHand":
        angle = math.radians(180)
        object.location.z -= (object.dimensions[2]*1.3)
        object.rotation_euler.x += angle

        # # Calculate the scaling factor (84% of the original size)
        # scale_factor = 0.84

        # # Get the object's current scale
        # object.scale.x *= scale_factor
        # object.scale.y *= scale_factor
        # object.scale.z *= scale_factor

        bpy.ops.export_mesh.stl(filepath=temp_files_path)

        for obj in bpy.context.scene.objects:
            bpy.data.objects.remove(obj, do_unlink=True)
    
    if name == "backHand":
        object.location.z += (object.dimensions[2]*1.3)

        # # Calculate the scaling factor (84% of the original size)
        # scale_factor = 0.84

        # # Get the object's current scale
        # object.scale.x *= scale_factor
        # object.scale.y *= scale_factor
        # object.scale.z *= scale_factor

    return mesh

def add_thickness(stl_file):
    # Clear workspace
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_by_type(type='MESH')
    bpy.ops.object.delete()

    # Import stl file
    bpy.ops.import_mesh.stl(filepath=stl_file)

    # Select main object
    ListObjects = [ o for o in bpy.context.scene.objects if o.select_get()]
    obj = ListObjects[0]

    # Apply Solidify modifier and thickness of 2mm
    modifier = obj.modifiers.new(name="Solidify", type='SOLIDIFY')
    modifier.thickness = 0.001  # 2mm thickness
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.modifier_apply(modifier="Solidify")

    bpy.ops.export_mesh.stl(filepath=stl_file)

def combine_mesh(backHand_path, frontHand_path):
    stl_file_paths = [backHand_path, frontHand_path]
    for stl_file_path in stl_file_paths:
        bpy.ops.import_mesh.stl(filepath=stl_file_path)

    

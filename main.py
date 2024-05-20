import os
import google.api
import google.api_core
import google.api_core.exceptions
import helpers.gcp_funs as gcp_funs
import helpers.runme_funs as runme_funs
import shutil
import google

from flask import Flask, request, redirect

app = Flask(__name__)

@app.route("/")
def calibrace():
    # Obtain Case ID from URL query.
    caseID = request.args.get('id')

    # Error catching, if caseID is nonexistant
    if caseID is None:
        msg = "No CaseID was entered. Please try again."
        return msg
    
    print(f"Beginning processing for {caseID}.")
    
    ###  Step 0. If Case ID exists, begin processing.
    # Create temporary directory to store temp files.
    temp_files_path = f"temp_files/{caseID}"
    if not os.path.exists(temp_files_path):
        os.makedirs(temp_files_path)
    
    ###  Step 1. Image Retrieval
    try:
        print("Downloading images.")
        # Download the required images.
        backHand_img, frontHand_img, sideHand_img = gcp_funs.download_imgs(caseID)

        # Remove backgrounds of images.
        print("Removing background.")
        backHand_img_segmented = runme_funs.remove_bg(backHand_img)
        frontHand_img_segmented = runme_funs.remove_bg(frontHand_img)

        # Mask of each image is created and saved.
        print("Creating mask.")
        backHand_mask, frontHand_mask = runme_funs.process_img(backHand_img_segmented,
                                                               backHand_img,
                                                               frontHand_img_segmented,
                                                               frontHand_img,
                                                               caseID)

        # Get hand thickness value
        thickness = runme_funs.get_thickness(sideHand_img)

    except google.api_core.exceptions.NotFound:
        message = f"ERROR: Images do not exist for Case ID: {caseID}"
        return message

    ### Step 2. 3D Model Computations
    # Compute point-cloud
    backHand_cloud = runme_funs.compute_cloud(backHand_mask)
    frontHand_cloud = runme_funs.compute_cloud(frontHand_mask)

    # Compute mesh
    print("Computing back-hand mesh.")
    backHand_mesh = runme_funs.compute_mesh(backHand_cloud, temp_files_path + "/backHand.stl", thickness, "backHand")
    print("Computing front-hand mesh.")
    frontHand_mesh = runme_funs.compute_mesh(frontHand_cloud, temp_files_path + "/frontHand.stl", thickness, "frontHand")

    # Downsize model

    # Upload mesh to Google Cloud
    gcp_funs.upload_file(temp_files_path + "/backHand.stl", caseID, "/backHand.stl")
    gcp_funs.upload_file(temp_files_path + "/frontHand.stl", caseID, "/frontHand.stl")

    ### Step 3. Create download link for image/stl.
    url = gcp_funs.generate_download_link(caseID, "/frontHand.stl")

    # After processing is complete, clean up environment
    shutil.rmtree(temp_files_path)

    # Send a 302 status request that redirects browser to the download link.
    return redirect(url, code=302)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

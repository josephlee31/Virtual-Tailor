# Virtual-Tailor
This is the project repository for the **VY01 - Virtual Tailor Capstone Group** (Faculty of Engineering and Architectural Science, Toronto Metropolitan University). Dubbed as **"Calibrace"**, this project consists of an image-guided software algorithm that processes 3 distinct photos of a subject's hand into a 3D-printable, custom, and wearable wrist brace.

Languages/Tools used: `Python`, `React Native`, `OpenCV`, `Mediapipe`, `Flask`, `Docker`, `PyVista` <br />
Cloud Technologies: `Google Cloud Platform (GCP)`, `Cloud Run`, `Firebase` <br />
3D Modeling/CAD Technologies: `Blender`, `SolidWorks`, `Ultimaker Cura`, `MeshLab`

## Project Overview
Current commercial arm braces often follow a one-size fits all approach and customized arm braces can be expensive depending on the technology used to develop them. To allow for a simpler, cost-efficient, and mobile approach, our team developed the Virtual Tailor, which we refer to as CaliBrace. The imaging system consists of a 5-step process to develop an STL file that users can use to print a customized arm brace. A robotic arm is employed to take standardized pictures of the top and bottom view of the hand, and ArUco markers to determine the thickness of the brace. The images are then uploaded using a mobile app that run a web server function to process the images, develop a 3D model of the brace, and provide a download link for the STL file. Our team was successfully able to create 3D models from 3 different participants within an error of ± 1cm. Additionally, we were able to create a prototype of a customized brace worn by a team member on Engineering Day.

## Features
- A 3D printed robotic arm (lovingly named "Rodney") was assembled to automate and standardize the image acquisition process.
- Image-processing backend deployed to a Google Cloud Run server using Flask and Docker, enabling users to trigger the function and retrieve a custom brace in less than 3 minutes.
- Successfully able to create 3D models within an error of ± 1cm.

<p align="center">
  <img src="./assets/images/rodney.jpg" width="360" height="500"/>
</p>

## Future Roadmap
Unfortunately, there is no current, feasiable way of hosting this project for free. The Cloud Run server and FireBase cloud storage used to host the back-end and image/STL files are closed. However, the process looks like the below:

1. Using the mobile app, the user takes a photo of the side-, back-, and front-view of the hand. 
2. The mobile app automatically uploads the images to a Firebase cloud database.
3. The mobile app generates a download URL, which the user can copy-paste to their browser.
4. The URL is similar in the format of `https://calibrace.a.run.app/?id={caseID}`. 
5. The Cloud Run server accepts this HTTPS request, and understands which images to process using the Case ID.
6. The Cloud Run server begins running the backend function, then triggers the user's web browser to download the completed STL file using a 302 status code.
<br />

<p align="center">
  <img src="./assets/images/hands.png" width="376", height="234"/>
</p>




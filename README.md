# Camera Floor Plan Plotter

A Streamlit web application that allows users to upload floor plan images and place camera icons to plan surveillance systems.

## Features

- Upload floor plan images (.jpg, .png)
- Place different camera types with distinct icons:
  - 🎯 PTZ (Pan-Tilt-Zoom) cameras
  - ⚪ Dome cameras  
  - 📹 Bullet cameras
  - 👁️ Facial Recognition cameras
- Number each camera for easy identification
- Interactive placement with coordinate inputs
- Camera management (view list, delete individual cameras)
- Export functionality:
  - Download camera layout as JSON
  - Download floor plan image with placed cameras

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Run the Streamlit app:
```bash
streamlit run app.py
```

## Usage

1. Open the app in your browser (typically http://localhost:8501)
2. Upload a floor plan image using the sidebar file uploader
3. Select camera type and number in the sidebar
4. Enter X,Y coordinates for camera placement
5. Click "Place Camera" to add the camera to your floor plan
6. Manage cameras using the camera list in the sidebar
7. Export your camera layout as JSON or download the annotated floor plan

## Deployment

To deploy on Streamlit Cloud:

1. Push this code to a GitHub repository
2. Go to https://share.streamlit.io
3. Connect your GitHub account and select the repository
4. Set the main file path to `app.py`
5. Deploy the app

The app will be available at your Streamlit Cloud URL.
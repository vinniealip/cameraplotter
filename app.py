import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw
import io
import base64
from dataclasses import dataclass
from typing import List, Optional
import json
import math

@dataclass
class Camera:
    id: int
    x: float
    y: float
    camera_type: str
    number: int
    angle: float = 0.0  # Direction angle in degrees (0 = right, 90 = down)

class CameraPlotter:
    def __init__(self):
        if 'cameras' not in st.session_state:
            st.session_state.cameras = []
        if 'next_camera_id' not in st.session_state:
            st.session_state.next_camera_id = 1
        if 'uploaded_image' not in st.session_state:
            st.session_state.uploaded_image = None
    
    def add_camera(self, x: float, y: float, camera_type: str, number: int, angle: float = 0.0):
        camera = Camera(
            id=st.session_state.next_camera_id,
            x=x, y=y,
            camera_type=camera_type,
            number=number,
            angle=angle
        )
        st.session_state.cameras.append(camera)
        st.session_state.next_camera_id += 1
    
    def remove_camera(self, camera_id: int):
        st.session_state.cameras = [c for c in st.session_state.cameras if c.id != camera_id]
    
    def update_camera_angle(self, camera_id: int, new_angle: float):
        for camera in st.session_state.cameras:
            if camera.id == camera_id:
                camera.angle = new_angle
                break
    
    def get_camera_icon(self, camera_type: str) -> str:
        icons = {
            'PTZ': '🎯',
            'Dome': '⚪',
            'Bullet': '📹',
            'Facial Recognition': '👁️'
        }
        return icons.get(camera_type, '📷')
    
    def render_image_with_cameras(self, image: Image.Image) -> Image.Image:
        img_copy = image.copy()
        draw = ImageDraw.Draw(img_copy)
        
        for camera in st.session_state.cameras:
            x, y = camera.x, camera.y
            angle_rad = math.radians(camera.angle)
            
            # Draw camera viewing cone
            cone_length = 60
            cone_width = 40  # degrees on each side
            
            # Calculate cone points
            cone_points = []
            cone_points.append((x, y))  # Center point
            
            # Left edge of cone
            left_angle = angle_rad - math.radians(cone_width)
            left_x = x + cone_length * math.cos(left_angle)
            left_y = y + cone_length * math.sin(left_angle)
            cone_points.append((left_x, left_y))
            
            # Right edge of cone
            right_angle = angle_rad + math.radians(cone_width)
            right_x = x + cone_length * math.cos(right_angle)
            right_y = y + cone_length * math.sin(right_angle)
            cone_points.append((right_x, right_y))
            
            # Draw cone with transparency effect
            draw.polygon(cone_points, fill=(255, 255, 0, 100), outline=(255, 165, 0, 150))
            
            # Draw center line for direction
            center_x = x + cone_length * 0.8 * math.cos(angle_rad)
            center_y = y + cone_length * 0.8 * math.sin(angle_rad)
            draw.line([(x, y), (center_x, center_y)], fill='orange', width=2)
            
            # Draw circle background for camera
            circle_radius = 15
            draw.ellipse(
                [x - circle_radius, y - circle_radius, x + circle_radius, y + circle_radius],
                fill='red', outline='black', width=2
            )
            
            # Draw camera number
            draw.text((x - 5, y - 8), str(camera.number), fill='white')
        
        return img_copy

def main():
    st.set_page_config(page_title="Camera Floor Plan Plotter", layout="wide")
    
    st.title("📹 Camera Floor Plan Plotter")
    st.markdown("Upload a floor plan image and place camera icons to plan your surveillance system.")
    
    plotter = CameraPlotter()
    
    # Sidebar for controls
    with st.sidebar:
        st.header("Controls")
        
        # File upload
        uploaded_file = st.file_uploader(
            "Upload Floor Plan", 
            type=['png', 'jpg', 'jpeg'],
            help="Upload a floor plan image (.jpg or .png)"
        )
        
        if uploaded_file is not None:
            st.session_state.uploaded_image = Image.open(uploaded_file)
        
        st.divider()
        
        # Camera placement controls
        st.subheader("Add Camera")
        camera_type = st.selectbox(
            "Camera Type",
            ['PTZ', 'Dome', 'Bullet', 'Facial Recognition']
        )
        
        camera_number = st.number_input(
            "Camera Number", 
            min_value=1, 
            max_value=999, 
            value=len(st.session_state.cameras) + 1
        )
        
        camera_angle = st.slider(
            "Camera Direction (degrees)",
            min_value=0,
            max_value=359,
            value=0,
            help="0° = Right, 90° = Down, 180° = Left, 270° = Up"
        )
        
        # Click coordinates input (will be updated by image click)
        if 'click_x' not in st.session_state:
            st.session_state.click_x = 0
        if 'click_y' not in st.session_state:
            st.session_state.click_y = 0
            
        col1, col2 = st.columns(2)
        with col1:
            x_coord = st.number_input("X", value=st.session_state.click_x, key="x_input")
        with col2:
            y_coord = st.number_input("Y", value=st.session_state.click_y, key="y_input")
        
        if st.button("Place Camera", type="primary"):
            if st.session_state.uploaded_image is not None:
                plotter.add_camera(x_coord, y_coord, camera_type, camera_number, camera_angle)
                st.success(f"Added {camera_type} camera #{camera_number} at {camera_angle}°")
                st.rerun()
        
        st.divider()
        
        # Camera list and management
        st.subheader("Placed Cameras")
        if st.session_state.cameras:
            for camera in st.session_state.cameras:
                icon = plotter.get_camera_icon(camera.camera_type)
                
                with st.expander(f"{icon} Camera #{camera.number} ({camera.camera_type})"):
                    st.caption(f"Position: ({int(camera.x)}, {int(camera.y)})")
                    
                    # Angle editing
                    new_angle = st.slider(
                        "Direction",
                        min_value=0,
                        max_value=359,
                        value=int(camera.angle),
                        key=f"angle_{camera.id}",
                        help="0° = Right, 90° = Down, 180° = Left, 270° = Up"
                    )
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Update Angle", key=f"update_{camera.id}"):
                            plotter.update_camera_angle(camera.id, new_angle)
                            st.success(f"Updated camera #{camera.number} angle to {new_angle}°")
                            st.rerun()
                    
                    with col2:
                        if st.button("🗑️ Delete", key=f"delete_{camera.id}"):
                            plotter.remove_camera(camera.id)
                            st.rerun()
        else:
            st.info("No cameras placed yet")
        
        # Clear all cameras
        if st.session_state.cameras:
            if st.button("Clear All Cameras", type="secondary"):
                st.session_state.cameras = []
                st.rerun()
    
    # Main image display area
    if st.session_state.uploaded_image is not None:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Floor Plan")
            
            # Render image with cameras
            display_image = plotter.render_image_with_cameras(st.session_state.uploaded_image)
            
            # Display image with click handling
            st.image(display_image, use_column_width=True)
            
            # Instructions
            st.info("💡 **How to use:** Set camera coordinates in the sidebar and click 'Place Camera', or use the coordinate inputs to manually position cameras.")
        
        with col2:
            st.subheader("Camera Legend")
            camera_types = ['PTZ', 'Dome', 'Bullet', 'Facial Recognition']
            for cam_type in camera_types:
                icon = plotter.get_camera_icon(cam_type)
                st.write(f"{icon} {cam_type}")
            
            # Export functionality
            st.divider()
            st.subheader("Export")
            
            if st.session_state.cameras:
                # Export as JSON
                camera_data = []
                for camera in st.session_state.cameras:
                    camera_data.append({
                        'number': camera.number,
                        'type': camera.camera_type,
                        'x': camera.x,
                        'y': camera.y,
                        'angle': camera.angle
                    })
                
                json_str = json.dumps(camera_data, indent=2)
                st.download_button(
                    label="Download Camera Data (JSON)",
                    data=json_str,
                    file_name="camera_layout.json",
                    mime="application/json"
                )
                
                # Export image with cameras
                img_buffer = io.BytesIO()
                display_image.save(img_buffer, format='PNG')
                st.download_button(
                    label="Download Floor Plan with Cameras",
                    data=img_buffer.getvalue(),
                    file_name="floor_plan_with_cameras.png",
                    mime="image/png"
                )
    else:
        st.info("👆 Please upload a floor plan image to get started")

if __name__ == "__main__":
    main()
import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw
import io
import base64
from dataclasses import dataclass
from typing import List, Optional
import json
import math
from streamlit_image_coordinates import streamlit_image_coordinates

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
        if 'drag_mode' not in st.session_state:
            st.session_state.drag_mode = False
        if 'selected_camera_id' not in st.session_state:
            st.session_state.selected_camera_id = None
    
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
    
    def update_camera_position(self, camera_id: int, new_x: float, new_y: float):
        for camera in st.session_state.cameras:
            if camera.id == camera_id:
                camera.x = new_x
                camera.y = new_y
                break
    
    def find_camera_at_position(self, x: float, y: float, tolerance: int = 20) -> Optional[int]:
        for camera in st.session_state.cameras:
            distance = math.sqrt((camera.x - x)**2 + (camera.y - y)**2)
            if distance <= tolerance:
                return camera.id
        return None
    
    def get_camera_icon(self, camera_type: str) -> str:
        icons = {
            'PTZ': '🎯',
            'Dome': '⚪',
            'Bullet': '📹',
            'Facial Recognition': '👁️'
        }
        return icons.get(camera_type, '📷')
    
    def get_camera_style(self, camera_type: str) -> dict:
        styles = {
            'PTZ': {'fill': (255, 165, 0), 'outline': (255, 100, 0), 'cone_color': (255, 255, 0, 100)},  # Orange
            'Dome': {'fill': (128, 128, 128), 'outline': (64, 64, 64), 'cone_color': (200, 200, 200, 100)},  # Gray
            'Bullet': {'fill': (0, 100, 255), 'outline': (0, 50, 200), 'cone_color': (100, 150, 255, 100)},  # Blue
            'Facial Recognition': {'fill': (255, 50, 150), 'outline': (200, 0, 100), 'cone_color': (255, 100, 200, 100)}  # Pink
        }
        return styles.get(camera_type, {'fill': (255, 0, 0), 'outline': (150, 0, 0), 'cone_color': (255, 255, 0, 100)})
    
    def render_image_with_cameras(self, image: Image.Image) -> Image.Image:
        img_copy = image.copy()
        draw = ImageDraw.Draw(img_copy)
        
        for camera in st.session_state.cameras:
            x, y = camera.x, camera.y
            angle_rad = math.radians(camera.angle)
            style = self.get_camera_style(camera.camera_type)
            
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
            
            # Draw cone with camera-specific color
            draw.polygon(cone_points, fill=style['cone_color'], outline=style['outline'])
            
            # Draw center line for direction
            center_x = x + cone_length * 0.8 * math.cos(angle_rad)
            center_y = y + cone_length * 0.8 * math.sin(angle_rad)
            draw.line([(x, y), (center_x, center_y)], fill=style['outline'], width=2)
            
            # Draw camera shape based on type
            circle_radius = 15
            
            if camera.camera_type == 'PTZ':
                # PTZ: Circle with crosshairs
                draw.ellipse(
                    [x - circle_radius, y - circle_radius, x + circle_radius, y + circle_radius],
                    fill=style['fill'], outline=style['outline'], width=2
                )
                # Crosshairs
                draw.line([(x-8, y), (x+8, y)], fill='white', width=2)
                draw.line([(x, y-8), (x, y+8)], fill='white', width=2)
            
            elif camera.camera_type == 'Dome':
                # Dome: Circle with dome pattern
                draw.ellipse(
                    [x - circle_radius, y - circle_radius, x + circle_radius, y + circle_radius],
                    fill=style['fill'], outline=style['outline'], width=2
                )
                # Dome lines
                draw.arc([x-10, y-10, x+10, y+10], 0, 180, fill='white', width=2)
                draw.arc([x-6, y-6, x+6, y+6], 0, 180, fill='white', width=1)
            
            elif camera.camera_type == 'Bullet':
                # Bullet: Rectangle shape
                draw.rectangle(
                    [x - circle_radius, y - circle_radius//2, x + circle_radius, y + circle_radius//2],
                    fill=style['fill'], outline=style['outline'], width=2
                )
                # Lens circle
                draw.ellipse([x+5, y-5, x+12, y+5], fill='black', outline='white')
            
            else:  # Facial Recognition
                # FR: Hexagon shape
                hex_size = circle_radius - 2
                hex_points = []
                for i in range(6):
                    angle = i * math.pi / 3
                    hex_x = x + hex_size * math.cos(angle)
                    hex_y = y + hex_size * math.sin(angle)
                    hex_points.append((hex_x, hex_y))
                draw.polygon(hex_points, fill=style['fill'], outline=style['outline'], width=2)
                # Eye symbol
                draw.ellipse([x-6, y-3, x+6, y+3], fill='white')
                draw.ellipse([x-2, y-1, x+2, y+1], fill='black')
            
            # Draw camera number
            draw.text((x - 5, y - 22), str(camera.number), fill='black', stroke_width=1, stroke_fill='white')
        
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
        
        # Mode selection
        mode = st.radio(
            "Interaction Mode",
            ["Place New Camera", "Move Existing Camera"],
            help="Choose whether to place new cameras or move existing ones"
        )
        st.session_state.drag_mode = (mode == "Move Existing Camera")
        
        if not st.session_state.drag_mode:
            # Click coordinates input for placing new cameras
            if 'click_x' not in st.session_state:
                st.session_state.click_x = 0
            if 'click_y' not in st.session_state:
                st.session_state.click_y = 0
                
            col1, col2 = st.columns(2)
            with col1:
                x_coord = st.number_input("X", value=st.session_state.click_x, key="x_input")
            with col2:
                y_coord = st.number_input("Y", value=st.session_state.click_y, key="y_input")
        else:
            st.info("Click on a camera in the image to select and move it.")
            if st.session_state.selected_camera_id:
                selected_camera = next((c for c in st.session_state.cameras if c.id == st.session_state.selected_camera_id), None)
                if selected_camera:
                    st.success(f"Selected Camera #{selected_camera.number} - Click anywhere to move it")
        
        if not st.session_state.drag_mode:
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
        
        # Clear all cameras and reset selection
        if st.session_state.cameras:
            if st.button("Clear All Cameras", type="secondary"):
                st.session_state.cameras = []
                st.session_state.selected_camera_id = None
                st.rerun()
        
        # Clear selection button for drag mode
        if st.session_state.drag_mode and st.session_state.selected_camera_id:
            if st.button("Cancel Selection"):
                st.session_state.selected_camera_id = None
                st.rerun()
    
    # Main image display area
    if st.session_state.uploaded_image is not None:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Floor Plan")
            
            # Render image with cameras
            display_image = plotter.render_image_with_cameras(st.session_state.uploaded_image)
            
            # Display image with click handling using streamlit-image-coordinates
            coords = streamlit_image_coordinates(display_image, key="image_coords")
            
            if coords is not None:
                click_x, click_y = coords["x"], coords["y"]
                
                if st.session_state.drag_mode:
                    # Move existing camera mode
                    if st.session_state.selected_camera_id is None:
                        # Select camera to move
                        camera_id = plotter.find_camera_at_position(click_x, click_y)
                        if camera_id:
                            st.session_state.selected_camera_id = camera_id
                            st.rerun()
                    else:
                        # Move selected camera to new position
                        plotter.update_camera_position(st.session_state.selected_camera_id, click_x, click_y)
                        st.session_state.selected_camera_id = None
                        st.success("Camera moved!")
                        st.rerun()
                else:
                    # Place new camera mode - update coordinates
                    st.session_state.click_x = click_x
                    st.session_state.click_y = click_y
                    st.rerun()
            
            # Instructions
            if st.session_state.drag_mode:
                st.info("💡 **Move Mode:** Click on a camera to select it, then click where you want to move it.")
            else:
                st.info("💡 **Place Mode:** Click on the image to set coordinates, then use 'Place Camera' button in sidebar.")
        
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
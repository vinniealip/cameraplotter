# Camera Plotter App - Version 2.0 - Fixed TypeError
import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import base64
from dataclasses import dataclass
from typing import List, Optional
import json
import math
import numpy as np
from streamlit.components.v1 import html

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
        if 'drag_update' not in st.session_state:
            st.session_state.drag_update = None
        if 'move_mode' not in st.session_state:
            st.session_state.move_mode = 'select'  # 'select' or 'place'
        if 'selected_for_move' not in st.session_state:
            st.session_state.selected_for_move = None
    
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
    
    def render_image_with_highlighted_camera(self, image: Image.Image, highlight_camera_id: int) -> Image.Image:
        img_copy = self.render_image_with_cameras(image)
        draw = ImageDraw.Draw(img_copy)
        
        # Find and highlight the selected camera
        for camera in st.session_state.cameras:
            if camera.id == highlight_camera_id:
                x, y = camera.x, camera.y
                # Draw a bright pulsing ring around selected camera
                for radius in [35, 40, 45]:
                    draw.ellipse(
                        [x - radius, y - radius, x + radius, y + radius],
                        outline=(255, 215, 0), width=3  # Gold highlight
                    )
                break
        
        return img_copy
    
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
            
            # Draw camera shape based on type (enlarged)
            circle_radius = 25
            
            if camera.camera_type == 'PTZ':
                # PTZ: Circle with crosshairs (enlarged)
                draw.ellipse(
                    [x - circle_radius, y - circle_radius, x + circle_radius, y + circle_radius],
                    fill=style['fill'], outline=style['outline'], width=3
                )
                # Crosshairs (larger)
                draw.line([(x-15, y), (x+15, y)], fill='white', width=3)
                draw.line([(x, y-15), (x, y+15)], fill='white', width=3)
            
            elif camera.camera_type == 'Dome':
                # Dome: Circle with dome pattern (enlarged)
                draw.ellipse(
                    [x - circle_radius, y - circle_radius, x + circle_radius, y + circle_radius],
                    fill=style['fill'], outline=style['outline'], width=3
                )
                # Dome lines (larger)
                draw.arc([x-18, y-18, x+18, y+18], 0, 180, fill='white', width=3)
                draw.arc([x-12, y-12, x+12, y+12], 0, 180, fill='white', width=2)
                draw.arc([x-6, y-6, x+6, y+6], 0, 180, fill='white', width=1)
            
            elif camera.camera_type == 'Bullet':
                # Bullet: Rectangle shape (enlarged)
                rect_width = circle_radius + 5
                rect_height = circle_radius // 2 + 5
                draw.rectangle(
                    [x - rect_width, y - rect_height, x + rect_width, y + rect_height],
                    fill=style['fill'], outline=style['outline'], width=3
                )
                # Lens circle (larger)
                draw.ellipse([x+8, y-8, x+18, y+8], fill='black', outline='white', width=2)
            
            else:  # Facial Recognition
                # FR: Hexagon shape (enlarged)
                hex_size = circle_radius
                hex_points = []
                for i in range(6):
                    angle = i * math.pi / 3
                    hex_x = x + hex_size * math.cos(angle)
                    hex_y = y + hex_size * math.sin(angle)
                    hex_points.append((hex_x, hex_y))
                draw.polygon(hex_points, fill=style['fill'], outline=style['outline'], width=3)
                # Eye symbol (larger)
                draw.ellipse([x-10, y-5, x+10, y+5], fill='white')
                draw.ellipse([x-4, y-2, x+4, y+2], fill='black')
            
            # Draw camera number (much larger font)
            try:
                # Try to load a font, fall back to default if not available
                font_size = 32  # Much larger font
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", font_size)
            except:
                try:
                    # Try other common system fonts
                    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
                except:
                    # Fall back to default and hope for the best
                    font = ImageFont.load_default()
            
            # Get text size for centering
            text = str(camera.number)
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Draw text with background for better visibility
            text_x = x - text_width // 2
            text_y = y - circle_radius - text_height - 8
            
            # Larger background rectangle for text
            padding = 6
            draw.rectangle(
                [text_x - padding, text_y - padding//2, text_x + text_width + padding, text_y + text_height + padding//2],
                fill='white', outline='black', width=2
            )
            
            # Draw the number with bold effect (draw multiple times slightly offset)
            for offset_x, offset_y in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                draw.text((text_x + offset_x, text_y + offset_y), text, fill='black', font=font)
            # Final text on top
            draw.text((text_x, text_y), text, fill='black', font=font)
        
        return img_copy

def main():
    # VERSION 2.0 - Fixed TypeError - No component dependencies
    st.set_page_config(page_title="Camera Floor Plan Plotter", layout="wide")
    
    st.title("📹 Camera Floor Plan Plotter")
    st.markdown("Upload a floor plan image and place camera icons to plan your surveillance system.")
    
    plotter = CameraPlotter()
    
    # Simple coordinate-based camera movement system
    
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
            ["Place New Camera", "🎯 Click-to-Move Cameras"],
            help="Choose whether to place new cameras or move existing ones"
        )
        st.session_state.drag_mode = (mode == "🎯 Click-to-Move Cameras")
        
        if st.session_state.drag_mode:
            st.info("💡 **How to move cameras:** Select a camera below, then click where you want it on the floor plan!")
            
            # Reset selection button
            if st.session_state.selected_for_move and st.button("🔄 Clear Selection"):
                st.session_state.selected_for_move = None
                st.rerun()
        
        if not st.session_state.drag_mode:
            # Coordinates input for placing new cameras
            if 'click_x' not in st.session_state:
                st.session_state.click_x = 100
            if 'click_y' not in st.session_state:
                st.session_state.click_y = 100
                
            col1, col2 = st.columns(2)
            with col1:
                x_coord = st.number_input("X Position", value=st.session_state.click_x, key="x_input")
            with col2:
                y_coord = st.number_input("Y Position", value=st.session_state.click_y, key="y_input")
        
        if not st.session_state.drag_mode:
            if st.button("Place Camera", type="primary"):
                if st.session_state.uploaded_image is not None:
                    plotter.add_camera(x_coord, y_coord, camera_type, camera_number, camera_angle)
                    st.success(f"Added {camera_type} camera #{camera_number} at {camera_angle}°")
                    st.rerun()
        
        st.divider()
        
        # Camera list and management
        st.subheader("Camera Management")
        if st.session_state.cameras:
            for camera in st.session_state.cameras:
                icon = plotter.get_camera_icon(camera.camera_type)
                
                # Special handling for move mode
                if st.session_state.drag_mode:
                    is_selected = st.session_state.selected_for_move == camera.id
                    
                    # Create a distinctive layout for each camera
                    with st.container():
                        if is_selected:
                            st.success(f"✓ **SELECTED FOR MOVING**")
                            col1, col2 = st.columns([2, 1])
                            with col1:
                                st.write(f"### {icon} Camera #{camera.number}")
                                st.write(f"**Type:** {camera.camera_type}")
                                st.write(f"**Current Position:** ({int(camera.x)}, {int(camera.y)})")
                                st.write(f"**Direction:** {int(camera.angle)}°")
                                st.info("Now click anywhere on the floor plan above to move this camera!")
                            with col2:
                                if st.button("❌ Deselect", key=f"deselect_{camera.id}", type="secondary"):
                                    st.session_state.selected_for_move = None
                                    st.rerun()
                        else:
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.write(f"**{icon} Camera #{camera.number}** ({camera.camera_type})")
                                st.caption(f"Position: ({int(camera.x)}, {int(camera.y)}) | Direction: {int(camera.angle)}°")
                            with col2:
                                if st.button("🎯 Select to Move", key=f"select_{camera.id}", type="primary"):
                                    st.session_state.selected_for_move = camera.id
                                    st.rerun()
                        
                        st.divider()
                else:
                    # Normal mode - full editor
                    with st.expander(f"{icon} Camera #{camera.number} ({camera.camera_type})", expanded=False):
                        st.caption(f"Position: ({int(camera.x)}, {int(camera.y)})")
                        
                        # Angle editing
                        new_angle = st.slider(
                            "Camera Direction (degrees)",
                            min_value=0,
                            max_value=359,
                            value=int(camera.angle),
                            key=f"angle_{camera.id}",
                            help="0° = Right, 90° = Down, 180° = Left, 270° = Up"
                        )
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Update Direction", key=f"update_{camera.id}"):
                                plotter.update_camera_angle(camera.id, new_angle)
                                st.success(f"Updated camera #{camera.number} direction to {new_angle}°")
                                st.rerun()
                        
                        with col2:
                            if st.button("🗑️ Delete", key=f"delete_{camera.id}"):
                                plotter.remove_camera(camera.id)
                                st.rerun()
        else:
            st.info("No cameras placed yet. Use 'Place New Camera' mode to add some!")
        
        # Clear all cameras and reset selection
        if st.session_state.cameras:
            if st.button("Clear All Cameras", type="secondary"):
                st.session_state.cameras = []
                st.session_state.selected_camera_id = None
                st.rerun()
        
    
    # Main image display area
    if st.session_state.uploaded_image is not None:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Floor Plan")
            
            # Render image with cameras (highlight selected camera)
            if st.session_state.drag_mode and st.session_state.selected_for_move:
                # Create a version with highlighted selected camera
                display_image = plotter.render_image_with_highlighted_camera(
                    st.session_state.uploaded_image, 
                    st.session_state.selected_for_move
                )
            else:
                display_image = plotter.render_image_with_cameras(st.session_state.uploaded_image)
            
            if st.session_state.drag_mode:
                st.info("🎯 **Easy Move Mode:** Select a camera from the sidebar, then click where you want to move it!")
                
                # Convert PIL image to base64 for HTML display
                buffered = io.BytesIO()
                display_image.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode()
                
                # Simple click-to-move with session state
                if 'click_coordinates' not in st.session_state:
                    st.session_state.click_coordinates = None
                
                # Enhanced click detection with session state updates
                html_code = f"""
                <div style="position: relative; display: inline-block; border: 3px solid #4CAF50; border-radius: 15px; overflow: hidden; background: #f8f9fa; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                    <img id="floorplan" src="data:image/png;base64,{img_str}" 
                         style="width: 100%; height: auto; display: block; cursor: crosshair;" 
                         onclick="handleClick(event)" />
                    <div id="feedback" style="position: absolute; top: 15px; left: 15px; background: rgba(76, 175, 80, 0.95); color: white; padding: 10px 15px; border-radius: 8px; font-size: 14px; font-weight: bold; display: none; z-index: 1000; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">Click detected!</div>
                </div>
                
                <script>
                function handleClick(event) {{
                    const rect = event.target.getBoundingClientRect();
                    const scaleX = event.target.naturalWidth / rect.width;
                    const scaleY = event.target.naturalHeight / rect.height;
                    const x = Math.round((event.clientX - rect.left) * scaleX);
                    const y = Math.round((event.clientY - rect.top) * scaleY);
                    
                    // Show immediate feedback
                    const feedback = document.getElementById('feedback');
                    feedback.innerHTML = `🎯 Moving camera to (${{x}}, ${{y}})`;
                    feedback.style.display = 'block';
                    
                    // Update URL parameters to trigger Streamlit update
                    const url = new URL(window.location);
                    url.searchParams.set('click_x', x);
                    url.searchParams.set('click_y', y);
                    url.searchParams.set('click_time', Date.now());
                    window.history.replaceState({{}}, '', url);
                    
                    // Immediately refresh to process the move
                    window.location.reload();
                }}
                </script>
                """
                
                # Display the clickable image
                html(html_code, height=500)
                
                # Simple Save Button Approach
                st.subheader("🎯 Move Camera Controls")
                
                if st.session_state.selected_for_move:
                    selected_camera = next((c for c in st.session_state.cameras if c.id == st.session_state.selected_for_move), None)
                    if selected_camera:
                        st.info(f"🎯 **Ready to move Camera #{selected_camera.number}**")
                        st.write(f"Current position: ({int(selected_camera.x)}, {int(selected_camera.y)})")
                        
                        col1, col2, col3 = st.columns([2, 2, 2])
                        
                        with col1:
                            new_x = st.number_input(
                                "New X Position", 
                                value=int(selected_camera.x),
                                min_value=0,
                                key="move_x_input"
                            )
                        
                        with col2:
                            new_y = st.number_input(
                                "New Y Position", 
                                value=int(selected_camera.y),
                                min_value=0,
                                key="move_y_input"
                            )
                        
                        with col3:
                            st.write("")
                            st.write("")
                            if st.button("🎯 Move Camera Here!", type="primary", key="move_camera_btn"):
                                # Move the camera
                                plotter.update_camera_position(st.session_state.selected_for_move, new_x, new_y)
                                st.success(f"✓ Moved Camera #{selected_camera.number} to ({new_x}, {new_y})!")
                                
                                # Reset selection
                                st.session_state.selected_for_move = None
                                st.rerun()
                        
                        st.markdown("---")
                        st.info("💡 **Tip:** You can manually type coordinates above, or click on the floor plan to auto-fill them (coming soon!)")
                
                else:
                    st.warning("👆 Please select a camera from the sidebar first!")
                    
            else:
                st.info("💡 **Place Mode:** Set coordinates in the sidebar and click 'Place Camera' button.")
                st.image(display_image, use_column_width=True)
        
        with col2:
            st.subheader("Camera Legend")
            
            # Create mini images showing actual camera appearance
            legend_size = 80
            
            for cam_type in ['PTZ', 'Dome', 'Bullet', 'Facial Recognition']:
                style = plotter.get_camera_style(cam_type)
                
                # Create a small image showing the camera icon
                legend_img = Image.new('RGBA', (legend_size, legend_size), (255, 255, 255, 0))
                legend_draw = ImageDraw.Draw(legend_img)
                
                center_x, center_y = legend_size // 2, legend_size // 2
                radius = 20
                
                # Draw the same shapes as on the main map
                if cam_type == 'PTZ':
                    legend_draw.ellipse(
                        [center_x - radius, center_y - radius, center_x + radius, center_y + radius],
                        fill=style['fill'], outline=style['outline'], width=2
                    )
                    legend_draw.line([(center_x-12, center_y), (center_x+12, center_y)], fill='white', width=2)
                    legend_draw.line([(center_x, center_y-12), (center_x, center_y+12)], fill='white', width=2)
                
                elif cam_type == 'Dome':
                    legend_draw.ellipse(
                        [center_x - radius, center_y - radius, center_x + radius, center_y + radius],
                        fill=style['fill'], outline=style['outline'], width=2
                    )
                    legend_draw.arc([center_x-15, center_y-15, center_x+15, center_y+15], 0, 180, fill='white', width=2)
                    legend_draw.arc([center_x-8, center_y-8, center_x+8, center_y+8], 0, 180, fill='white', width=1)
                
                elif cam_type == 'Bullet':
                    legend_draw.rectangle(
                        [center_x - radius, center_y - radius//2, center_x + radius, center_y + radius//2],
                        fill=style['fill'], outline=style['outline'], width=2
                    )
                    legend_draw.ellipse([center_x+5, center_y-5, center_x+15, center_y+5], fill='black', outline='white')
                
                else:  # Facial Recognition
                    hex_points = []
                    for i in range(6):
                        angle = i * math.pi / 3
                        hex_x = center_x + radius * math.cos(angle)
                        hex_y = center_y + radius * math.sin(angle)
                        hex_points.append((hex_x, hex_y))
                    legend_draw.polygon(hex_points, fill=style['fill'], outline=style['outline'], width=2)
                    legend_draw.ellipse([center_x-8, center_y-3, center_x+8, center_y+3], fill='white')
                    legend_draw.ellipse([center_x-3, center_y-1, center_x+3, center_y+1], fill='black')
                
                # Display the legend item
                col_icon, col_text = st.columns([1, 2])
                with col_icon:
                    st.image(legend_img, width=60)
                with col_text:
                    st.write(f"**{cam_type}**")
                    st.caption(f"Color: {style['fill']}" if isinstance(style['fill'], str) else "Colored icon")
            
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
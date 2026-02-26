import streamlit.components.v1 as components
import streamlit as st
import base64
import io
from PIL import Image
import json

def draggable_canvas(image, cameras, key=None):
    """
    Create a draggable canvas component for camera movement
    """
    # Convert PIL image to base64
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    # Create cameras data for JavaScript
    cameras_data = [
        {
            'id': cam.id,
            'x': cam.x,
            'y': cam.y,
            'number': cam.number,
            'type': cam.camera_type,
            'angle': cam.angle
        } for cam in cameras
    ]
    
    # HTML component with proper drag functionality
    html_string = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ margin: 0; padding: 20px; font-family: Arial, sans-serif; }}
            #canvas-container {{ 
                position: relative; 
                display: inline-block; 
                border: 3px solid #4CAF50; 
                border-radius: 15px; 
                overflow: hidden; 
                background: #f8f9fa;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }}
            #canvas {{ 
                display: block; 
                cursor: grab; 
                max-width: 100%; 
                height: auto;
                background: white;
            }}
            #canvas:active {{ cursor: grabbing; }}
            .feedback {{ 
                position: absolute; 
                top: 15px; 
                left: 15px; 
                background: rgba(76, 175, 80, 0.95); 
                color: white; 
                padding: 10px 15px; 
                border-radius: 8px; 
                font-size: 14px; 
                font-weight: bold; 
                z-index: 1000;
                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                transition: all 0.3s ease;
            }}
            .feedback.warning {{ background: rgba(255, 152, 0, 0.95); }}
            .feedback.success {{ background: rgba(76, 175, 80, 0.95); }}
            .feedback.info {{ background: rgba(33, 150, 243, 0.95); }}
        </style>
    </head>
    <body>
        <div id="canvas-container">
            <canvas id="canvas"></canvas>
            <div id="feedback" class="feedback" style="display: none;"></div>
        </div>

        <script>
            let canvas, ctx, isDragging = false, dragCamera = null, dragOffset = {{ x: 0, y: 0 }};
            let cameras = {json.dumps(cameras_data)};
            const img = new Image();
            
            function showFeedback(message, type = 'info') {{
                const feedback = document.getElementById('feedback');
                feedback.innerHTML = message;
                feedback.className = `feedback ${{type}}`;
                feedback.style.display = 'block';
                setTimeout(() => feedback.style.display = 'none', 3000);
            }}
            
            function initCanvas() {{
                canvas = document.getElementById('canvas');
                ctx = canvas.getContext('2d');
                
                img.onload = function() {{
                    canvas.width = img.width;
                    canvas.height = img.height;
                    drawScene();
                }};
                img.src = "data:image/png;base64,{img_str}";
            }}
            
            function drawScene() {{
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                ctx.drawImage(img, 0, 0);
                
                // Draw cameras with enhanced visuals
                cameras.forEach(camera => {{
                    drawCamera(camera);
                }});
            }}
            
            function drawCamera(camera) {{
                const x = camera.x;
                const y = camera.y;
                
                // Draw viewing cone
                const coneLength = 60;
                const coneAngle = 40; // degrees
                const angleRad = camera.angle * Math.PI / 180;
                
                ctx.save();
                ctx.globalAlpha = 0.3;
                ctx.fillStyle = getCameraColor(camera.type);
                ctx.beginPath();
                ctx.moveTo(x, y);
                ctx.arc(x, y, coneLength, angleRad - coneAngle * Math.PI / 180, angleRad + coneAngle * Math.PI / 180);
                ctx.closePath();
                ctx.fill();
                ctx.restore();
                
                // Draw camera body
                ctx.save();
                ctx.fillStyle = getCameraColor(camera.type);
                ctx.strokeStyle = '#333';
                ctx.lineWidth = 2;
                
                if (camera.type === 'PTZ') {{
                    // Circle with crosshairs
                    ctx.beginPath();
                    ctx.arc(x, y, 20, 0, 2 * Math.PI);
                    ctx.fill();
                    ctx.stroke();
                    
                    ctx.strokeStyle = 'white';
                    ctx.lineWidth = 3;
                    ctx.beginPath();
                    ctx.moveTo(x - 12, y);
                    ctx.lineTo(x + 12, y);
                    ctx.moveTo(x, y - 12);
                    ctx.lineTo(x, y + 12);
                    ctx.stroke();
                }} else if (camera.type === 'Dome') {{
                    // Circle with dome arcs
                    ctx.beginPath();
                    ctx.arc(x, y, 20, 0, 2 * Math.PI);
                    ctx.fill();
                    ctx.stroke();
                    
                    ctx.strokeStyle = 'white';
                    ctx.lineWidth = 2;
                    ctx.beginPath();
                    ctx.arc(x, y, 15, 0, Math.PI);
                    ctx.arc(x, y, 10, 0, Math.PI);
                    ctx.stroke();
                }} else if (camera.type === 'Bullet') {{
                    // Rectangle with lens
                    ctx.fillRect(x - 20, y - 10, 40, 20);
                    ctx.strokeRect(x - 20, y - 10, 40, 20);
                    
                    ctx.fillStyle = 'black';
                    ctx.beginPath();
                    ctx.arc(x + 10, y, 6, 0, 2 * Math.PI);
                    ctx.fill();
                }} else {{
                    // Hexagon for Facial Recognition
                    ctx.beginPath();
                    for (let i = 0; i < 6; i++) {{
                        const angle = i * Math.PI / 3;
                        const px = x + 18 * Math.cos(angle);
                        const py = y + 18 * Math.sin(angle);
                        if (i === 0) ctx.moveTo(px, py);
                        else ctx.lineTo(px, py);
                    }}
                    ctx.closePath();
                    ctx.fill();
                    ctx.stroke();
                    
                    // Eye
                    ctx.fillStyle = 'white';
                    ctx.fillRect(x - 8, y - 3, 16, 6);
                    ctx.fillStyle = 'black';
                    ctx.fillRect(x - 2, y - 1, 4, 2);
                }}
                
                // Draw number with background
                ctx.fillStyle = 'white';
                ctx.strokeStyle = 'black';
                ctx.lineWidth = 1;
                ctx.font = '16px Arial';
                const text = camera.number.toString();
                const textWidth = ctx.measureText(text).width;
                
                ctx.fillRect(x - textWidth/2 - 4, y - 35, textWidth + 8, 20);
                ctx.strokeRect(x - textWidth/2 - 4, y - 35, textWidth + 8, 20);
                
                ctx.fillStyle = 'black';
                ctx.fillText(text, x - textWidth/2, y - 20);
                
                ctx.restore();
            }}
            
            function getCameraColor(type) {{
                const colors = {{
                    'PTZ': '#FF6B35',
                    'Dome': '#808080', 
                    'Bullet': '#2196F3',
                    'Facial Recognition': '#E91E63'
                }};
                return colors[type] || '#FF0000';
            }}
            
            function getCameraAtPosition(x, y) {{
                for (let camera of cameras) {{
                    const distance = Math.sqrt((camera.x - x) ** 2 + (camera.y - y) ** 2);
                    if (distance <= 25) {{
                        return camera;
                    }}
                }}
                return null;
            }}
            
            function handleMouseDown(event) {{
                const rect = canvas.getBoundingClientRect();
                const x = event.clientX - rect.left;
                const y = event.clientY - rect.top;
                
                dragCamera = getCameraAtPosition(x, y);
                if (dragCamera) {{
                    isDragging = true;
                    dragOffset.x = x - dragCamera.x;
                    dragOffset.y = y - dragCamera.y;
                    canvas.style.cursor = 'grabbing';
                    showFeedback(`🎯 Dragging Camera #${{dragCamera.number}}`, 'info');
                }}
            }}
            
            function handleMouseMove(event) {{
                if (!isDragging || !dragCamera) return;
                
                const rect = canvas.getBoundingClientRect();
                const x = event.clientX - rect.left;
                const y = event.clientY - rect.top;
                
                dragCamera.x = Math.max(25, Math.min(canvas.width - 25, x - dragOffset.x));
                dragCamera.y = Math.max(25, Math.min(canvas.height - 25, y - dragOffset.y));
                
                drawScene();
                showFeedback(`🎯 Moving to (${{Math.round(dragCamera.x)}}, ${{Math.round(dragCamera.y)}})`, 'info');
            }}
            
            function handleMouseUp(event) {{
                if (isDragging && dragCamera) {{
                    // Send data back to Streamlit
                    window.parent.postMessage({{
                        type: 'streamlit:setComponentValue',
                        value: {{
                            camera_id: dragCamera.id,
                            x: Math.round(dragCamera.x),
                            y: Math.round(dragCamera.y)
                        }}
                    }}, '*');
                    
                    showFeedback(`✓ Moved Camera #${{dragCamera.number}}!`, 'success');
                }}
                
                isDragging = false;
                dragCamera = null;
                canvas.style.cursor = 'grab';
            }}
            
            // Event listeners
            canvas.addEventListener('mousedown', handleMouseDown);
            canvas.addEventListener('mousemove', handleMouseMove);
            canvas.addEventListener('mouseup', handleMouseUp);
            canvas.addEventListener('mouseleave', handleMouseUp);
            
            // Initialize
            initCanvas();
        </script>
    </body>
    </html>
    """
    
    # Use Streamlit's HTML component with bidirectional communication
    result = components.html(
        html_string,
        height=600,
        key=key
    )
    
    return result
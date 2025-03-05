import os
import uuid
import random
import string
import math
import base64
from io import BytesIO
import json

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from PIL import Image, ImageDraw, ImageFont, ImageFilter

app = Flask(__name__)
CORS(app)

captchas = {}

def save():
  with open("captchas.json", "w") as f:
    json.dump(captchas, f)
    
def load():
  global captchas
  if os.path.exists("captchas.json"):
    with open("captchas.json", "r") as f:
      captchas = json.load(f)

# Adjust the font path as needed. For many systems, "arial.ttf" might be available.
FONT_PATH = "arial.ttf"

def generate_captcha_text(length=6):
    """Generate a random string of uppercase letters and digits."""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


def vibrant_color(min_val=50, max_val=255):
    """Return a vibrant random colour."""
    return (
        random.randint(min_val, max_val),
        random.randint(min_val, max_val),
        random.randint(min_val, max_val),
    )


def generate_captcha_image(text):
    """Create a high-resolution, colourful CAPTCHA image with text, random lines, arcs, dots, and a sine wave."""
    # Increase the resolution of the image.
    width, height = 400, 160
    image = Image.new("RGB", (width, height), (255, 255, 255))

    # Increase font size proportionally.
    font_size = 80

    try:
        font = ImageFont.truetype(FONT_PATH, font_size)
    except Exception:
        font = ImageFont.load_default()

    draw = ImageDraw.Draw(image)

    # --- Background Noise: colourful dots ---
    for _ in range(300):
        x = random.randint(0, width)
        y = random.randint(0, height)
        dot_color = vibrant_color(0, 255)
        draw.point((x, y), fill=dot_color)

    # --- Draw colourful text with individual character rotation ---
    spacing = width // (len(text) + 1)
    for i, char in enumerate(text):
        x = spacing * (i + 1) - font_size // 2
        y = (height - font_size) // 2 + random.randint(-20, 20)
        # Create an image for each character to allow rotation
        char_image = Image.new("RGBA", (font_size, font_size), (255, 255, 255, 0))
        char_draw = ImageDraw.Draw(char_image)
        # Use vibrant colours for text
        char_color = vibrant_color(0, 255)
        char_draw.text((0, 0), char, font=font, fill=char_color)
        angle = random.randint(-30, 30)
        rotated = char_image.rotate(angle, expand=1)
        image.paste(rotated, (x, y), rotated)

    # --- Add random colourful lines ---
    for _ in range(10):
        start = (random.randint(0, width), random.randint(0, height))
        end = (random.randint(0, width), random.randint(0, height))
        line_color = vibrant_color(0, 255)
        draw.line([start, end], fill=line_color, width=3)

    # --- Add colourful arcs ---
    for _ in range(3):
        # Random bounding box for the arc
        bbox = [
            random.randint(0, width // 2),
            random.randint(0, height // 2),
            random.randint(width // 2, width),
            random.randint(height // 2, height),
        ]
        start_angle = random.randint(0, 180)
        end_angle = start_angle + random.randint(90, 270)
        arc_color = vibrant_color(0, 255)
        draw.arc(bbox, start=start_angle, end=end_angle, fill=arc_color, width=3)

    # --- Draw a sine wave with a vibrant colour ---
    amplitude = random.randint(10, 30)
    frequency = random.uniform(0.02, 0.06)
    phase = random.uniform(0, 2 * math.pi)
    sine_color = vibrant_color(0, 255)
    for x in range(width):
        y = int(amplitude * math.sin(frequency * x + phase)) + height // 2
        if 0 <= y < height:
            draw.point((x, y), fill=sine_color)

    # Optionally, enhance edges
    image = image.filter(ImageFilter.EDGE_ENHANCE_MORE)
    return image


@app.route('/generate_captcha', methods=['GET'])
def generate_captcha():
    """Generate a CAPTCHA image and return its ID and a base64-encoded image."""
    captcha_text = generate_captcha_text()
    captcha_id = str(uuid.uuid4())

    captchas[captcha_id] = captcha_text
    save()

    # Create the CAPTCHA image
    image = generate_captcha_image(captcha_text)
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')

    return jsonify({
        "captcha_id": captcha_id,
        "captcha_image": img_str  # Client can decode this to display the image
    })

@app.route('/verify_captcha', methods=['POST'])
def verify_captcha():
    """Verify a CAPTCHA based on its ID and user input."""
    load()
    
    data = request.get_json()
    captcha_id = data.get('captcha_id')
    user_input = data.get('captcha_input', '')

    expected = captchas.get(captcha_id)
    
    if expected and user_input == expected:
        result = True
    else:
        result = False

    if captcha_id in captchas:
        del captchas[captcha_id]
        
    save()

    return jsonify({"success": result})
  
@app.route('/embed.html')
def widget():
    return send_from_directory('.', 'embed.html')

if __name__ == '__main__':
    # Run the app; set debug=False in production
    app.run(host='0.0.0.0', port=os.environ['PORT'])

import os
import cv2
import json
from flask import Flask, render_template, request, send_file, jsonify
from io import BytesIO
import base64

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
TEMPLATE_FILENAME = "certificate_template.png"
template_path = os.path.join(UPLOAD_FOLDER, TEMPLATE_FILENAME)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload_template", methods=["POST"])
def upload_template():
    if "file" not in request.files:
        return "No file part in the request", 400
    file = request.files["file"]
    if file.filename == "":
        return "No file selected", 400
    if file:
        # Save the uploaded template as `certificate_template.png`
        file.save(template_path)
        return "Template uploaded successfully", 200
    return "Failed to upload the template", 500

def generate_certificate(name, text_color, font_weight, font_style, text_x, text_y):
    if not os.path.exists(template_path):
        raise ValueError("No template uploaded or template file missing.")

    # Load the uploaded template
    template_image = cv2.imread(template_path)
    if template_image is None:
        raise ValueError("Failed to load the template image.")

    r, g, b = tuple(int(text_color[i:i + 2], 16) for i in (1, 3, 5))
    color = (b, g, r)

    font_styles = {
        "HERSHEY_SIMPLEX": cv2.FONT_HERSHEY_SIMPLEX,
        "HERSHEY_SCRIPT_SIMPLEX": cv2.FONT_HERSHEY_SCRIPT_SIMPLEX,
        "HERSHEY_COMPLEX": cv2.FONT_HERSHEY_COMPLEX,
        "HERSHEY_TRIPLEX": cv2.FONT_HERSHEY_TRIPLEX,
    }

    font = font_styles.get(font_style, cv2.FONT_HERSHEY_SIMPLEX)
    font_scale = 1.5

    # Add text to the certificate
    cv2.putText(template_image, name, (text_x, text_y), font, font_scale, color, font_weight, cv2.LINE_AA)

    _, buffer = cv2.imencode(".png", template_image)
    return buffer.tobytes()

@app.route("/generate", methods=["POST"])
def generate():
    try:
        data = request.get_json()
        if not data:
            raise ValueError("No JSON data provided")

        name = data["name"]
        text_color = data["text_color"]
        font_weight = int(data["font_weight"])
        font_style = data["font_style"]
        text_x = int(data["text_x"])
        text_y = int(data["text_y"])

        img_bytes = generate_certificate(name, text_color, font_weight, font_style, text_x, text_y)

        img_io = BytesIO(img_bytes)
        return send_file(img_io, mimetype="image/png", download_name="certificate.png", as_attachment=True)
    except ValueError as e:
        return str(e), 400
    except Exception as e:
        return f"An error occurred: {str(e)}", 500

@app.route("/preview", methods=["POST"])
def preview():
    try:
        data = request.get_json()
        if not data:
            raise ValueError("No JSON data provided")

        name = data["name"]
        text_color = data["text_color"]
        font_weight = int(data["font_weight"])
        font_style = data["font_style"]
        text_x = int(data["text_x"])
        text_y = int(data["text_y"])

        img_bytes = generate_certificate(name, text_color, font_weight, font_style, text_x, text_y)

        # Convert the image to base64 for preview
        base64_img = base64.b64encode(img_bytes).decode("utf-8")
        return jsonify({"image": f"data:image/png;base64,{base64_img}"})
    except ValueError as e:
        return str(e), 400
    except Exception as e:
        return f"An error occurred: {str(e)}", 500

if __name__ == "__main__":
    app.run(debug=True)

from flask import Flask, render_template, request, redirect, jsonify
import face_recognition
import cv2
import pickle
import numpy as np
import os
import base64
from io import BytesIO
from PIL import Image

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads' # Though not used in webcam flow, good to keep if switching
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Load or initialize face_db
face_db_path = "face_db.pkl"
if os.path.exists(face_db_path):
    with open(face_db_path, "rb") as f:
        face_db = pickle.load(f)
else:
    face_db = [] # Initialize as a list of dictionaries
    with open(face_db_path, "wb") as f:
        pickle.dump(face_db, f)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        amount = request.form.get("amount")
        # Instead of redirecting to /scan with amount in query,
        # let's make /scan also a POST route or handle differently
        # For simplicity with current structure, we'll keep query param for /scan
        return redirect(f"/scan_page?amount={amount}") # Redirect to a new page that hosts webcam for scanning
    return render_template("index.html")

@app.route("/scan_page")
def scan_page():
    amount = request.args.get("amount", default="1")
    return render_template("scan.html", amount=amount) # New HTML for scanning

@app.route("/scan_face_for_payment", methods=["POST"]) # Called by JavaScript from scan.html
def scan_face_for_payment():
    data = request.json
    image_data = data["image"].split(",")[1]
    amount = data.get("amount", "1") # Get amount from JS
    image_bytes = base64.b64decode(image_data)
    
    try:
        image = Image.open(BytesIO(image_bytes)).convert('RGB')
        np_image = np.array(image)
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error processing image: {str(e)}"})

    face_locations = face_recognition.face_locations(np_image)
    face_encodings = face_recognition.face_encodings(np_image, face_locations)

    if not face_encodings:
        return jsonify({"status": "no_match", "message": "No face detected in the scanned image."})

    found_match = False
    user_name = ""
    upi_link_val = ""

    for face_encoding in face_encodings: # Should ideally only be one face for payment
        for entry in face_db:
            if "encoding" in entry and entry["encoding"] is not None:
                match = face_recognition.compare_faces([entry["encoding"]], face_encoding, tolerance=0.5)
                if match[0]:
                    user_name = entry["name"]
                    upi_id = entry["upi"]
                    upi_link_val = f"upi://pay?pa={upi_id}&pn={user_name}&am={amount}&cu=INR"
                    found_match = True
                    break
        if found_match:
            break
            
    if found_match:
        return jsonify({"status": "success", "name": user_name, "upi_link": upi_link_val, "amount": amount})
    else:
        return jsonify({"status": "no_match", "message": "No match found in the database."})


@app.route("/register")
def register_route(): # Renamed to avoid conflict with internal 'register'
    return render_template("register.html")

@app.route("/register-face", methods=["POST"])
def register_face():
    data = request.json
    name = data.get("name")
    upi = data.get("upi")
    image_data_url = data.get("image")

    if not all([name, upi, image_data_url]):
        return jsonify({"status": "error", "message": "Missing name, UPI ID, or image data."})

    try:
        image_data = image_data_url.split(",")[1]  # remove base64 header
        image_bytes = base64.b64decode(image_data)
        image = Image.open(BytesIO(image_bytes)).convert('RGB')
        np_image = np.array(image)
    except Exception as e:
        return jsonify({"status": "error", "message": f"Invalid image data: {str(e)}"})

    face_locations = face_recognition.face_locations(np_image)
    face_encodings = face_recognition.face_encodings(np_image, face_locations)

    if face_encodings:
        # Check if user already exists by name or UPI to avoid duplicates if desired
        # For simplicity, we add directly
        face_db.append({"name": name, "upi": upi, "encoding": face_encodings[0]})
        with open(face_db_path, "wb") as f:
            pickle.dump(face_db, f)
        return jsonify({"status": "success", "message": f"User {name} registered successfully."})
    else:
        return jsonify({"status": "error", "message": "No face detected in the provided image."})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
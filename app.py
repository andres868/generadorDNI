
from flask import Flask, render_template, request, send_file, Response
from fpdf import FPDF
from PIL import Image
import io, os
from functools import wraps
from cryptography.fernet import Fernet

app = Flask(__name__)
key = Fernet.generate_key()
cipher = Fernet(key)

# Autenticación básica
def check_auth(username, password):
    return username == 'Personal Pay' and password == 'Requerimientos2025'

def authenticate():
    return Response(
        'Acceso restringido. Ingrese usuario y contraseña.', 401,
        {'WWW-Authenticate': 'Basic realm="Login requerido"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

@app.route("/", methods=["GET", "POST"])
@requires_auth
def index():
    if request.method == "POST":
        dni = request.form.get("dni", "").strip()
        initiated_at = request.form.get("initiated_at", "").strip()
        ip = request.form.get("ip", "").strip()

        def convertir_y_encriptar_img(uploaded_file):
            data = uploaded_file.read()
            encrypted_data = cipher.encrypt(data)
            return encrypted_data

        img_frente_enc = convertir_y_encriptar_img(request.files["img_frente"])
        img_dorso_enc = convertir_y_encriptar_img(request.files["img_dorso"])
        img_selfie_enc = convertir_y_encriptar_img(request.files["img_selfie"])

        pdf = FPDF()
        pdf.add_page()

        logo_path = "personalPay_alt_negro.jpg"
        if os.path.exists(logo_path):
            pdf.image(logo_path, x=65, y=10, w=80)
            pdf.ln(40)

        pdf.set_font("Arial", "B", 14)
        pdf.set_text_color(90, 80, 249)
        pdf.cell(200, 10, f"DNI: {dni.upper()}", ln=True)

        pdf.set_font("Arial", "", 12)
        pdf.cell(200, 10, f"INITIATED AT: {initiated_at.upper()}", ln=True)
        pdf.cell(200, 10, f"IP: {ip.upper()}", ln=True)
        pdf.set_text_color(0, 0, 0)

        def add_image(pdf, encrypted_data, label):
            pdf.ln(10)
            pdf.set_font("Arial", "B", 12)
            pdf.set_text_color(90, 80, 249)
            pdf.cell(200, 10, label.upper(), ln=True)
            pdf.set_text_color(0, 0, 0)
            decrypted_data = cipher.decrypt(encrypted_data)
            image = Image.open(io.BytesIO(decrypted_data)).convert("RGB")
            img_io = io.BytesIO()
            image.save(img_io, format="JPEG")
            img_io.seek(0)
            temp_filename = f"temp_{label.replace(' ', '_')}.jpg"
            with open(temp_filename, "wb") as f:
                f.write(img_io.read())
            pdf.image(temp_filename, x=10, y=None, w=180)
            os.remove(temp_filename)

        add_image(pdf, img_frente_enc, "DNI Frente")
        add_image(pdf, img_dorso_enc, "DNI Dorso")
        add_image(pdf, img_selfie_enc, "Selfie")

        output_path = f"{dni}_DNI.pdf"
        pdf.output(output_path)

        return send_file(output_path, as_attachment=True)

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")

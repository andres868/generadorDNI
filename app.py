
from flask import Flask, render_template, request, send_file, Response
from fpdf import FPDF
from PIL import Image
import os
from functools import wraps

app = Flask(__name__)

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

        temp_folder = "temp"
        os.makedirs(temp_folder, exist_ok=True)

        def convertir_y_guardar_img(uploaded_file, nombre_archivo):
            ruta = os.path.join(temp_folder, nombre_archivo)
            imagen = Image.open(uploaded_file)
            imagen = imagen.convert("RGB")
            imagen.save(ruta, "JPEG")
            return ruta

        img_frente_path = convertir_y_guardar_img(request.files["img_frente"], "frente.jpg")
        img_dorso_path = convertir_y_guardar_img(request.files["img_dorso"], "dorso.jpg")
        img_selfie_path = convertir_y_guardar_img(request.files["img_selfie"], "selfie.jpg")

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

        def add_image(pdf, image_path, label):
            pdf.ln(10)
            pdf.set_font("Arial", "B", 12)
            pdf.set_text_color(90, 80, 249)
            pdf.cell(200, 10, label.upper(), ln=True)
            pdf.set_text_color(0, 0, 0)
            pdf.image(image_path, x=10, y=None, w=180)

        add_image(pdf, img_frente_path, "DNI Frente")
        add_image(pdf, img_dorso_path, "DNI Dorso")
        add_image(pdf, img_selfie_path, "Selfie")

        output_path = f"{dni}_DNI.pdf"
        pdf.output(output_path)

        os.remove(img_frente_path)
        os.remove(img_dorso_path)
        os.remove(img_selfie_path)

        return send_file(output_path, as_attachment=True)

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")

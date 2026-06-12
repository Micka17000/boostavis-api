from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, quote_plus
import json
import base64
import io
import qrcode
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        def g(key, default=""):
            value = params.get(key, [default])
            return value[0] if value else default

        commerce = g("commerce", "Votre Commerce")
        google = g("google", "https://search.google.com/local/writereview")


        lots = []
        for i in range(1, 9):
            lot = g(f"l{i}")
            if lot:
                lots.append(lot)

        if not lots:
            lots = ["Café offert", "-10%", "Dessert offert", "Boisson offerte"]

        roue_params = f"commerce={quote_plus(commerce)}&google={quote_plus(google)}"

        for i, lot in enumerate(lots, 1):
            roue_params += f"&l{i}={quote_plus(lot)}"

        

https://boostavis-client.vercel.app
        buffer = io.BytesIO()
        width, height = A4
        pdf = canvas.Canvas(buffer, pagesize=A4)

        pdf.setFillColorRGB(0.04, 0.04, 0.09)
        pdf.rect(0, 0, width, height, fill=1, stroke=0)

        pdf.setFillColorRGB(0.27, 0.24, 0.55)
        pdf.roundRect(90, height - 75, width - 180, 32, 16, fill=1, stroke=0)

        pdf.setFillColorRGB(1, 1, 1)
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawCentredString(width / 2, height - 63, "BoostAvis · Origin Play Studio")

        pdf.setFont("Helvetica-Bold", 36)
        pdf.drawCentredString(width / 2, height - 125, "Tentez votre chance !")

        pdf.setFillColorRGB(1, 0.82, 0.22)
        pdf.setFont("Helvetica-Bold", 18)
        pdf.drawCentredString(width / 2, height - 165, "Gagnez un cadeau offert par")

        pdf.setFillColorRGB(0.55, 0.49, 1)
        pdf.setFont("Helvetica-Bold", 28)
        pdf.drawCentredString(width / 2, height - 205, commerce)

        steps = [
            ("1", "Laissez un avis Google"),
            ("2", "Tournez la roue"),
            ("3", "Gagnez votre cadeau"),
        ]

        y = height - 270
        for num, text in steps:
            pdf.setFillColorRGB(0.39, 0.40, 0.95)
            pdf.circle(85, y, 15, fill=1, stroke=0)
            pdf.setFillColorRGB(1, 1, 1)
            pdf.setFont("Helvetica-Bold", 13)
            pdf.drawCentredString(85, y - 4, num)
            pdf.setFont("Helvetica-Bold", 17)
            pdf.drawString(120, y - 6, text)
            y -= 50

        qr = qrcode.QRCode(version=1, box_size=7, border=2)
        qr.add_data(roue_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        qr_buffer = io.BytesIO()
        img.save(qr_buffer, format="PNG")
        qr_buffer.seek(0)

        qr_size = 200
        qr_x = (width - qr_size) / 2
        qr_y = height - 625

        pdf.setFillColorRGB(1, 1, 1)
        pdf.roundRect(qr_x - 14, qr_y - 14, qr_size + 28, qr_size + 28, 12, fill=1, stroke=0)
        pdf.drawImage(ImageReader(qr_buffer), qr_x, qr_y, qr_size, qr_size)

        pdf.setFillColorRGB(0.8, 0.8, 0.8)
        pdf.setFont("Helvetica", 12)
        pdf.drawCentredString(width / 2, qr_y - 35, "Scannez ce QR code avec votre téléphone")

        pdf.setFillColorRGB(0.42, 0.39, 0.95)
        pdf.roundRect(110, qr_y - 100, width - 220, 48, 12, fill=1, stroke=0)

        pdf.setFillColorRGB(1, 1, 1)
        pdf.setFont("Helvetica-Bold", 17)
        pdf.drawCentredString(width / 2, qr_y - 82, "Tournez la roue et gagnez !")

        pdf.setFillColorRGB(0.45, 0.45, 0.45)
        pdf.setFont("Helvetica", 9)
        pdf.drawCentredString(width / 2, 35, "BoostAvis · Agents IA pour commerçants")

        pdf.save()
        buffer.seek(0)

        pdf_base64 = base64.b64encode(buffer.read()).decode("utf-8")

        result = {
            "roue_url": roue_url,
            "pdf_base64": pdf_base64,
            "commerce": commerce,
        }

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(result).encode("utf-8"))

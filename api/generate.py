import json
import base64
import io
import qrcode
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

def handler(request):
    # Récupérer les paramètres
    params = request.args if hasattr(request, 'args') else {}
    
    commerce = params.get('commerce', 'Votre Commerce')
    google   = params.get('google', 'https://search.google.com/local/writereview')
    c1       = params.get('c1', '4f46e5')
    c2       = params.get('c2', '7c3aed')
    lots     = []
    for i in range(1, 9):
        l = params.get(f'l{i}')
        if l:
            lots.append(l)
    if not lots:
        lots = ['Cafe offert', '-10%', 'Dessert offert', 'Boisson offerte']

    # Construire l'URL de la roue
    roue_params = f"commerce={commerce.replace(' ', '+')}&google={google}"
    for i, lot in enumerate(lots, 1):
        roue_params += f"&l{i}={lot.replace(' ', '+')}"
    roue_params += f"&c1=%23{c1}&c2=%23{c2}"
    roue_url = f"https://boostavis-demo.vercel.app?{roue_params}"

    # Générer le PDF
    buf = io.BytesIO()
    W, H = A4
    c = canvas.Canvas(buf, pagesize=A4)

    # FOND NOIR
    c.setFillColorRGB(0.04, 0.04, 0.09)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    # BADGE HAUT
    c.setFillColorRGB(0.27, 0.24, 0.55)
    c.roundRect(107, H - 68, 380, 26, 13, fill=1, stroke=0)
    c.setFillColorRGB(0.78, 0.76, 1.0)
    c.setFont("Helvetica", 10)
    c.drawCentredString(W/2, H - 59, "Agent IA pour commercants  .  Origin Play Studio")

    # TITRE
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 36)
    c.drawCentredString(W/2, H - 115, "Tentez votre chance !")

    # SOUS-TITRE
    c.setFillColorRGB(1, 0.82, 0.22)
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(W/2, H - 155, "Gagnez un cadeau offert par")

    # NOM DU COMMERCE
    c.setFillColorRGB(0.55, 0.49, 1.0)
    c.setFont("Helvetica-Bold", 30)
    c.drawCentredString(W/2, H - 200, commerce)

    # LIGNE
    c.setStrokeColorRGB(0.3, 0.3, 0.3)
    c.setLineWidth(1)
    c.line(50, H - 220, W - 50, H - 220)

    # ÉTAPES
    steps = [
        ("1", (0.39, 0.40, 0.95), "Laissez un avis Google"),
        ("2", (1.0,  0.72, 0.0),  "Tournez la roue"),
        ("3", (0.13, 0.77, 0.37), "Gagnez votre cadeau !"),
    ]
    sy = H - 270
    for num, col, text in steps:
        c.setFillColorRGB(*col)
        c.circle(75, sy, 14, fill=1, stroke=0)
        c.setFillColorRGB(1, 1, 1)
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(75, sy - 4, num)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(105, sy - 6, text)
        sy -= 48

    # QR CODE
    qr = qrcode.QRCode(version=1, box_size=7, border=2)
    qr.add_data(roue_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    qr_buf = io.BytesIO()
    img.save(qr_buf, format='PNG')
    qr_buf.seek(0)

    qr_size = 190
    qr_x = (W - qr_size) / 2
    qr_y = H - 620
    c.setFillColorRGB(1, 1, 1)
    c.roundRect(qr_x - 12, qr_y - 12, qr_size + 24, qr_size + 24, 10, fill=1, stroke=0)
    c.drawImage(ImageReader(qr_buf), qr_x, qr_y, qr_size, qr_size)

    c.setFillColorRGB(0.7, 0.7, 0.7)
    c.setFont("Helvetica", 12)
    c.drawCentredString(W/2, qr_y - 28, "Scannez ce QR code avec votre telephone")

    # BOUTON CTA
    btn_w = 370
    btn_x = (W - btn_w) / 2
    btn_y = qr_y - 88
    c.setFillColorRGB(0.42, 0.39, 0.95)
    c.roundRect(btn_x, btn_y, btn_w, 46, 10, fill=1, stroke=0)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 17)
    c.drawCentredString(W/2, btn_y + 15, "Tournez la roue et gagnez !")

    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.setFont("Helvetica", 10)
    c.drawCentredString(W/2, btn_y - 20, "Offre reservee aux clients ayant laisse un avis Google")

    # FOOTER
    c.setStrokeColorRGB(0.2, 0.2, 0.2)
    c.line(50, 58, W - 50, 58)
    c.setFillColorRGB(0.42, 0.39, 0.95)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(W/2, 40, "BoostAvis  .  Origin Play Studio")
    c.setFillColorRGB(0.4, 0.4, 0.4)
    c.setFont("Helvetica", 9)
    c.drawCentredString(W/2, 26, "Agents IA pour commercants")

    c.save()
    buf.seek(0)
    pdf_base64 = base64.b64encode(buf.read()).decode('utf-8')

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps({
            "roue_url": roue_url,
            "pdf_base64": pdf_base64,
            "commerce": commerce
        })
    }

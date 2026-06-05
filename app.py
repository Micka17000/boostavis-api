from flask import Flask, request, jsonify
import base64
import io
import qrcode
import requests
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import os

app = Flask(__name__)

COULEURS = {
    "violet (par défaut)": "4f46e5",
    "violet": "4f46e5",
    "bleu": "3b82f6",
    "rouge": "ef4444",
    "vert": "22c55e",
    "orange": "f97316",
    "rose": "ec4899",
    "noir": "1a1a2e",
    "or/jaune": "f59e0b",
    "jaune": "f59e0b",
}

COULEURS2 = {
    "violet (par défaut)": "7c3aed",
    "violet": "7c3aed",
    "bleu": "1d4ed8",
    "rouge": "b91c1c",
    "vert": "15803d",
    "orange": "c2410c",
    "rose": "be185d",
    "noir": "0f172a",
    "or/jaune": "d97706",
    "jaune": "d97706",
}

def resolve_color(val, secondary=False, default="4f46e5"):
    if not val:
        return default
    v = val.strip().lower()
    table = COULEURS2 if secondary else COULEURS
    if v in table:
        return table[v]
    if v.startswith("#"):
        return v[1:]
    return v if len(v) == 6 else default

def get_field(data, *keys):
    for k in keys:
        for dk in data:
            if dk.strip().lower() == k.strip().lower():
                val = data[dk]
                if val and str(val).strip():
                    return str(val).strip()
    return None

def generate_pdf(commerce, google, c1, c2, lots, roue_url):
    buf = io.BytesIO()
    W, H = A4
    c = canvas.Canvas(buf, pagesize=A4)
    c.setFillColorRGB(0.04, 0.04, 0.09)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColorRGB(0.27, 0.24, 0.55)
    c.roundRect(107, H-68, 380, 26, 13, fill=1, stroke=0)
    c.setFillColorRGB(0.78, 0.76, 1.0)
    c.setFont("Helvetica", 10)
    c.drawCentredString(W/2, H-59, "Agent IA pour commercants  .  Origin Play Studio")
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 36)
    c.drawCentredString(W/2, H-115, "Tentez votre chance !")
    c.setFillColorRGB(1, 0.82, 0.22)
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(W/2, H-155, "Gagnez un cadeau offert par")
    c.setFillColorRGB(0.55, 0.49, 1.0)
    c.setFont("Helvetica-Bold", 30)
    c.drawCentredString(W/2, H-200, commerce)
    c.setStrokeColorRGB(0.3, 0.3, 0.3)
    c.setLineWidth(1)
    c.line(50, H-220, W-50, H-220)
    steps = [
        ("1", (0.39,0.40,0.95), "Laissez un avis Google"),
        ("2", (1.0,0.72,0.0),   "Tournez la roue"),
        ("3", (0.13,0.77,0.37), "Gagnez votre cadeau !"),
    ]
    sy = H-270
    for num, col, text in steps:
        c.setFillColorRGB(*col)
        c.circle(75, sy, 14, fill=1, stroke=0)
        c.setFillColorRGB(1,1,1)
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(75, sy-4, num)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(105, sy-6, text)
        sy -= 48
    qr = qrcode.QRCode(version=1, box_size=7, border=2)
    qr.add_data(roue_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    qr_buf = io.BytesIO()
    img.save(qr_buf, format='PNG')
    qr_buf.seek(0)
    qr_size = 190
    qr_x = (W-qr_size)/2
    qr_y = H-620
    c.setFillColorRGB(1,1,1)
    c.roundRect(qr_x-12, qr_y-12, qr_size+24, qr_size+24, 10, fill=1, stroke=0)
    c.drawImage(ImageReader(qr_buf), qr_x, qr_y, qr_size, qr_size)
    c.setFillColorRGB(0.7,0.7,0.7)
    c.setFont("Helvetica", 12)
    c.drawCentredString(W/2, qr_y-28, "Scannez ce QR code avec votre telephone")
    btn_w = 370
    btn_x = (W-btn_w)/2
    btn_y = qr_y-88
    c.setFillColorRGB(0.42,0.39,0.95)
    c.roundRect(btn_x, btn_y, btn_w, 46, 10, fill=1, stroke=0)
    c.setFillColorRGB(1,1,1)
    c.setFont("Helvetica-Bold", 17)
    c.drawCentredString(W/2, btn_y+15, "Tournez la roue et gagnez !")
    c.setFillColorRGB(0.5,0.5,0.5)
    c.setFont("Helvetica", 10)
    c.drawCentredString(W/2, btn_y-20, "Offre reservee aux clients ayant laisse un avis Google")
    c.setStrokeColorRGB(0.2,0.2,0.2)
    c.line(50, 58, W-50, 58)
    c.setFillColorRGB(0.42,0.39,0.95)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(W/2, 40, "BoostAvis  .  Origin Play Studio")
    c.setFillColorRGB(0.4,0.4,0.4)
    c.setFont("Helvetica", 9)
    c.drawCentredString(W/2, 26, "Agents IA pour commercants")
    c.save()
    buf.seek(0)
    return buf

@app.route('/generate', methods=['GET', 'POST'])
def generate():
    if request.method == 'POST':
        data = request.get_json() or {}
        commerce = get_field(data, 'commerce', 'Nom de votre commerce') or 'Votre Commerce'
        google   = get_field(data, 'google', 'Lien Google Maps de votre commerce') or 'https://search.google.com/local/writereview'
        c1_raw   = get_field(data, 'c1', 'Couleur principale de votre roue') or 'violet'
        c2_raw   = get_field(data, 'c2', 'Couleur secondaire de votre roue') or 'violet'
        lots = []
        for i in range(1, 9):
            l = get_field(data, f'l{i}', f'Cadeau {i}')
            if l:
                lots.append(l)
        if not lots:
            lots = ['Cafe offert', '-10%', 'Dessert offert', 'Boisson offerte']
    else:
        commerce = request.args.get('commerce', 'Votre Commerce')
        google   = request.args.get('google', 'https://search.google.com/local/writereview')
        c1_raw   = request.args.get('c1', 'violet')
        c2_raw   = request.args.get('c2', 'violet')
        lots = []
        for i in range(1, 9):
            l = request.args.get(f'l{i}')
            if l:
                lots.append(l)
        if not lots:
            lots = ['Cafe offert', '-10%', 'Dessert offert', 'Boisson offerte']

    c1 = resolve_color(c1_raw, secondary=False)
    c2 = resolve_color(c2_raw, secondary=True, default="7c3aed")

    roue_params = f"commerce={commerce.replace(' ', '+')}&google={google}"
    for i, lot in enumerate(lots, 1):
        roue_params += f"&l{i}={lot.replace(' ', '+')}"
    roue_params += f"&c1=%23{c1}&c2=%23{c2}"
    roue_url = f"https://boostavis-demo.vercel.app?{roue_params}"

    pdf_buf = generate_pdf(commerce, google, c1, c2, lots, roue_url)
    pdf_bytes = pdf_buf.read()

    try:
        resp = requests.post(
            'https://tmpfiles.org/api/v1/upload',
            files={'file': ('boostavis.pdf', pdf_bytes, 'application/pdf')}
        )
        result = resp.json()
        tmp_url = result['data']['url'].replace('tmpfiles.org/', 'tmpfiles.org/dl/')
    except:
        tmp_url = None

    pdf_b64 = base64.b64encode(pdf_bytes).decode('utf-8')

    return jsonify({
        "roue_url": roue_url,
        "pdf_base64": pdf_b64,
        "pdf_url": tmp_url,
        "commerce": commerce
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

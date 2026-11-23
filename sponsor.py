"""
sponsor.py
Informazioni e utility per il supporto del progetto (donazioni).
"""

PAYPAL_URL = "https://paypal.me/3dmega"
MONERO_ADDRESS = (
    "47Jc6MC47WJVFhiQFYwHyBNQP5BEsjUPG6tc8R37FwcTY8K5Y3LvFzveSXoGiaDQSx"
    "DrnCUBJ5WBj6Fgmsfix8VPD4w3gXF"
)
GITHUB_URL = "https://github.com/Nsfr750"
WEBSITE_URL = "https://www.tuxxle.org"


def get_sponsor_info() -> dict:
    """Dati di sponsorizzazione: link PayPal, indirizzo Monero, contatti."""
    return {
        "paypal": PAYPAL_URL,
        "monero": MONERO_ADDRESS,
        "github": GITHUB_URL,
        "website": WEBSITE_URL,
    }


def make_qr_png(data: str, size: int = 200) -> bytes | None:
    """Genera un QR code PNG per il dato fornito.

    La matrice QR è calcolata dalla libreria qrcode e il rendering PNG
    è fatto con wand (ImageMagick): nessuna dipendenza da PIL/pillow.
    Restituisce i byte del PNG, oppure None se qrcode o wand mancano.
    """
    try:
        import qrcode
        from wand.color import Color
        from wand.drawing import Drawing
        from wand.image import Image
    except ImportError:
        return None

    qr = qrcode.QRCode(border=4)
    qr.add_data(data)
    qr.make(fit=True)
    matrix = qr.get_matrix()
    n = len(matrix)
    cell = size / n

    with Drawing() as draw:
        draw.fill_color = Color("black")
        for r, row in enumerate(matrix):
            for c, val in enumerate(row):
                if val:
                    draw.rectangle(
                        left=int(c * cell),
                        top=int(r * cell),
                        right=int((c + 1) * cell),
                        bottom=int((r + 1) * cell),
                    )
        with Image(width=size, height=size, background=Color("white")) as img:
            draw(img)
            img.format = "png"
            return img.make_blob()

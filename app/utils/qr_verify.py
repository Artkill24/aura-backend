import qrcode
from io import BytesIO
import base64
import os


def generate_verify_qr(job_id: str, sha256: str, base_url: str = "https://artkill24-aura-backend.hf.space"):
    verify_url = f"{base_url}/verify/{job_id}?h={sha256[:16]}"
    qr = qrcode.QRCode(version=2, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=4, border=2)
    qr.add_data(verify_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#00ffcc", back_color="#0D0D1A")
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8"), verify_url


def save_qr_png(job_id: str, sha256: str, output_dir: str, base_url: str = "https://artkill24-aura-backend.hf.space"):
    b64, verify_url = generate_verify_qr(job_id, sha256, base_url)
    path = os.path.join(output_dir, f"{job_id}_qr.png")
    with open(path, "wb") as f:
        f.write(base64.b64decode(b64))
    return path, verify_url

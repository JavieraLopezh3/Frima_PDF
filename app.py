import os
import pymupdf as fitz
from flask import Flask, render_template, request, send_file, redirect, url_for, flash, jsonify, session
import zipfile
from shutil import rmtree
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'clave_secreta_para_mensajes'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SESSIONS_ROOT = os.path.join(BASE_DIR, 'sessions')

os.makedirs(SESSIONS_ROOT, exist_ok=True)

def get_user_paths():
    user_id = session.get('user_id')
    if not user_id:
        return None, None, None
    user_dir = os.path.join(SESSIONS_ROOT, user_id)
    uploads = os.path.join(user_dir, 'uploads')
    processed = os.path.join(user_dir, 'processed')
    return user_dir, uploads, processed

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    pdfs = request.files.getlist('pdfs')
    signatures = request.files.getlist('signatures')

    if not signatures or len(signatures) == 0 or signatures[0].filename == '':
        return "Error: Por favor, selecciona al menos una imagen de firma (PNG).", 400
    
    if not pdfs or len(pdfs) == 0:
        return "Error: Por favor, selecciona al menos un archivo PDF.", 400

    # Crear sesión única para el usuario
    user_id = str(uuid.uuid4())
    session['user_id'] = user_id
    
    user_dir = os.path.join(SESSIONS_ROOT, user_id)
    uploads = os.path.join(user_dir, 'uploads')
    processed = os.path.join(user_dir, 'processed')
    
    os.makedirs(uploads, exist_ok=True)
    os.makedirs(processed, exist_ok=True)

    # Guardar firmas (máximo 5)
    sig_count = 0
    for sig in signatures[:5]:
        if sig.filename == '': continue
        sig_filename = f'signature_{sig_count}.png'
        sig_path = os.path.join(uploads, sig_filename)
        sig.save(sig_path)
        sig_count += 1

    pdf_files = []
    for pdf in pdfs:
        if pdf.filename == '': continue
        filename = secure_filename(pdf.filename)
        path = os.path.join(uploads, filename)
        pdf.save(path)
        pdf_files.append(filename)

    try:
        first_pdf_path = os.path.join(uploads, pdf_files[0])
        doc = fitz.open(first_pdf_path)
        page = doc[0]
        pix = page.get_pixmap()
        img_path = os.path.join(uploads, 'preview.png')
        pix.save(img_path)
        doc.close()
    except Exception as e:
        return f"Error al generar la vista previa: {e}", 500

    return render_template('preview.html', pdf_count=len(pdf_files), sig_count=sig_count)

@app.route('/preview_img')
def preview_img():
    _, uploads, _ = get_user_paths()
    if not uploads: return "Sesión expirada", 403
    return send_file(os.path.join(uploads, 'preview.png'), mimetype='image/png')

@app.route('/preview_sig/<int:index>')
def preview_sig(index):
    _, uploads, _ = get_user_paths()
    if not uploads: return "Sesión expirada", 403
    sig_path = os.path.join(uploads, f'signature_{index}.png')
    if not os.path.exists(sig_path):
        return "Firma no encontrada", 404
    return send_file(sig_path, mimetype='image/png')

@app.route('/process', methods=['POST'])
def process():
    try:
        user_dir, uploads, processed = get_user_paths()
        if not user_dir: 
            return jsonify({"status": "error", "message": "Sesión expirada"}), 403

        data = request.json
        if not data or 'placements' not in data:
            return jsonify({"status": "error", "message": "No se recibieron datos de posicionamiento"}), 400
            
        placements = data.get('placements', [])
        
        # Seguridad en el nombre del archivo
        raw_filename = data.get('filename', 'firmados').replace(" ", "_")
        custom_name = secure_filename(raw_filename)
        if not custom_name.endswith('.zip'):
            custom_name += '.zip'

        if not os.path.exists(uploads):
            return jsonify({"status": "error", "message": "Carpeta de uploads no encontrada"}), 500

        pdf_files = [f for f in os.listdir(uploads) if f.endswith('.pdf')]
        if not pdf_files:
            return jsonify({"status": "error", "message": "No hay archivos PDF para procesar"}), 400

        # Pre-cargar dimensiones de todas las firmas disponibles
        sig_dims = {}
        for i in range(5):
            sig_path = os.path.join(uploads, f'signature_{i}.png')
            if os.path.exists(sig_path):
                try:
                    img_sig = fitz.open(sig_path)
                    sig_dims[i] = (img_sig[0].rect.width, img_sig[0].rect.height)
                    img_sig.close()
                except Exception as e:
                    print(f"Error cargando firma {i}: {e}")

        for filename in pdf_files:
            file_path = os.path.join(uploads, filename)
            try:
                doc = fitz.open(file_path)
                page = doc[0]
                
                for p in placements:
                    sig_idx = p.get('sig_index')
                    if sig_idx is None or sig_idx not in sig_dims: 
                        continue
                    
                    sig_w, sig_h = sig_dims[sig_idx]
                    sig_path = os.path.join(uploads, f'signature_{sig_idx}.png')
                    
                    # Validar que existan coordenadas y escala
                    try:
                        x_p = float(p.get('x', 0))
                        y_p = float(p.get('y', 0))
                        scale = float(p.get('scale', 1.0))
                    except (ValueError, TypeError):
                        continue
                    
                    x = (x_p / 100) * page.rect.width
                    y = (y_p / 100) * page.rect.height
                    
                    final_w = 100 * scale
                    final_h = (sig_h / sig_w) * final_w
                    
                    rect = fitz.Rect(x, y, x + final_w, y + final_h)
                    page.insert_image(rect, filename=sig_path)
                
                doc.save(os.path.join(processed, filename))
                doc.close()
            except Exception as e:
                print(f"Error procesando archivo {filename}: {e}")
                # Continuamos con los demás archivos si uno falla

        zip_path = os.path.join(user_dir, custom_name)
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for root, dirs, files in os.walk(processed):
                for file in files:
                    zipf.write(os.path.join(root, file), file)

        return jsonify({"status": "success", "download_url": url_for('download', filename=custom_name)})
    except Exception as e:
        print(f"Error crítico en process: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/download/<filename>')
def download(filename):
    user_dir, _, _ = get_user_paths()
    if not user_dir: return "Sesión expirada", 403
    
    # Asegurar que el archivo solicitado esté en la carpeta del usuario
    safe_filename = secure_filename(filename)
    file_path = os.path.join(user_dir, safe_filename)
    
    if not os.path.exists(file_path):
        return "Archivo no encontrado", 404

    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)

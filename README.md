# 🖋️ Firma Digital Pro

Una aplicación web ligera desarrollada con **Python** y **Flask** que permite firmar múltiples documentos PDF de forma masiva y eficiente.

## ✨ Características
- **Firma Masiva:** Sube múltiples PDFs y aplica la misma configuración de firma a todos simultáneamente.
- **Múltiples Firmas:** Soporta la carga de hasta 5 firmas diferentes por sesión.
- **Posicionamiento Interactivo:** Interfaz visual para colocar las firmas mediante arrastrar y soltar (Drag & Drop).
- **Control de Escala:** Ajusta el tamaño de cada firma individualmente.
- **Privacidad Total:** El procesamiento se realiza localmente; los archivos no se almacenan permanentemente en la nube.

## 🚀 Instalación y Uso

### Requisitos previos
- Python 3.8 o superior
- `pip` (instalador de paquetes de Python)

### Pasos para ejecutar
1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/TU_USUARIO/firma_pdf.git
   cd firma_pdf
   ```

2. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Ejecutar la aplicación:**
   ```bash
   python app.py
   ```

4. **Acceder a la web:**
   Abre tu navegador y entra en `http://127.0.0.1:5000`

## 🛠️ Tecnologías utilizadas
- **Backend:** Flask, PyMuPDF (fitz)
- **Frontend:** HTML5, CSS3 (Modern UI), JavaScript
- **Iconos:** FontAwesome

from flask import Flask, request, jsonify
from flask_cors import CORS  # Importar CORS
from multiprocessing import Process, Queue
import os

app = Flask(__name__)
CORS(app)  # Habilitar CORS para todas las rutas

# Importar el analizador léxico
from analizador_html import process_sources_concurrently

# Endpoint para recibir y procesar archivos
@app.route("/analyze", methods=["POST"])
def analyze_files():
    if "files" not in request.files:
        return jsonify({"error": "No se enviaron archivos"}), 400

    files = request.files.getlist("files")
    file_paths = []

    # Guardar los archivos temporalmente
    for file in files:
        file_path = os.path.join("uploads", file.filename)
        file.save(file_path)
        file_paths.append(file_path)

    # Procesar los archivos utilizando el analizador léxico
    results = process_sources_concurrently(file_paths)

    # Eliminar los archivos temporales
    for file_path in file_paths:
        os.remove(file_path)

    # Devolver los resultados al frontend
    return jsonify(results)

if __name__ == "__main__":
    # Crear la carpeta "uploads" si no existe
    if not os.path.exists("uploads"):
        os.makedirs("uploads")

    app.run(port=5000)
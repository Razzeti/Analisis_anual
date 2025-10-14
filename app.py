from flask import Flask, jsonify, render_template
import pandas as pd
import os

# Importar las funciones de los scripts de procesamiento.
# Esto es mucho más limpio que llamar a los scripts como procesos separados.
from procesador_anual import procesar_carpeta_de_pdfs
from unificador import unificar_y_conciliar_reportes

# Crear una instancia de la aplicación Flask
app = Flask(__name__, template_folder='templates')

# --- Constantes de Configuración ---
# Se definen aquí para que sea fácil cambiarlas en el futuro.
CARPETA_YAPE_PDFS = "yape"
CARPETA_AHORRO_PDFS = "ahorros"
CSV_YAPE_CONSOLIDADO = "reporte_anual_consolidado.csv"
CSV_AHORRO_CONSOLIDADO = "reporte_anual_consolidado_AHORRO.csv"
REPORTE_FINAL = "reporte_maestro_limpio.csv"

@app.route('/')
def home():
    """
    Sirve la página principal del dashboard (graf1.html).
    """
    return render_template('graf1.html')

@app.route('/api/data')
def get_data():
    """
    Punto de API que ejecuta todo el pipeline de procesamiento de datos:
    1. Procesa los PDFs de Yape.
    2. Procesa los PDFs de Ahorro.
    3. Unifica y limpia los datos.
    4. Devuelve el resultado como JSON.
    """
    print("🚀 Petición recibida en /api/data. Iniciando pipeline de datos...")

    # --- Paso 1: Procesar PDFs de la cuenta Yape ---
    print(f"   -> Procesando PDFs de '{CARPETA_YAPE_PDFS}'...")
    procesar_carpeta_de_pdfs(CARPETA_YAPE_PDFS, CSV_YAPE_CONSOLIDADO)

    # --- Paso 2: Procesar PDFs de la cuenta de Ahorros ---
    print(f"   -> Procesando PDFs de '{CARPETA_AHORRO_PDFS}'...")
    procesar_carpeta_de_pdfs(CARPETA_AHORRO_PDFS, CSV_AHORRO_CONSOLIDADO)

    # --- Paso 3: Unificar y conciliar ambos reportes ---
    print("   -> Unificando y conciliando reportes...")
    unificar_y_conciliar_reportes(CSV_YAPE_CONSOLIDADO, CSV_AHORRO_CONSOLIDADO, REPORTE_FINAL)

    # --- Paso 4: Leer el reporte final y enviarlo como JSON ---
    print(f"   -> Leyendo reporte final '{REPORTE_FINAL}' para la respuesta.")
    if not os.path.exists(REPORTE_FINAL):
        print(f"   -> ❌ Error: No se encontró el archivo '{REPORTE_FINAL}'.")
        return jsonify({"error": "El archivo de reporte final no fue encontrado."}), 500

    try:
        df = pd.read_csv(REPORTE_FINAL, sep=';')
        # Convertir el DataFrame a una lista de diccionarios (formato JSON)
        data = df.to_dict(orient='records')
        print("   -> ✅ Datos procesados y listos para enviar.")
        return jsonify(data)
    except Exception as e:
        print(f"   -> ❌ Error: Ocurrió un error al leer o convertir el CSV final: {e}")
        return jsonify({"error": f"Error al leer el archivo CSV: {e}"}), 500

if __name__ == '__main__':
    # Se especifica el puerto 5001 para evitar conflictos con otros servicios
    app.run(debug=True, port=5001)
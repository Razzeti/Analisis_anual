from flask import Flask, jsonify, render_template
import pandas as pd
import os

# Importar las funciones de los scripts de procesamiento
from procesador_anual import procesar_carpeta_de_pdfs
from unificador import unificar_y_conciliar_reportes

# Crear una instancia de la aplicación Flask
app = Flask(__name__, template_folder='templates')

# --- Configuración por Defecto ---
# Se establecen valores predeterminados que pueden ser sobreescritos
# durante las pruebas o en diferentes entornos.
app.config.from_mapping(
    CARPETA_YAPE_PDFS="yape",
    CARPETA_AHORRO_PDFS="ahorros",
    CSV_YAPE_CONSOLIDADO="reporte_anual_consolidado.csv",
    CSV_AHORRO_CONSOLIDADO="reporte_anual_consolidado_AHORRO.csv",
    REPORTE_FINAL="reporte_maestro_limpio.csv"
)

@app.route('/')
def home():
    """Sirve la página principal del dashboard (graf1.html)."""
    return render_template('graf1.html')

def run_data_pipeline():
    """
    Ejecuta el pipeline completo de procesamiento de datos, utilizando la
    configuración de la aplicación actual.
    """
    print("🚀 Iniciando pipeline de datos...")

    # Usar la configuración de la app en lugar de constantes globales
    procesar_carpeta_de_pdfs(
        app.config['CARPETA_YAPE_PDFS'],
        app.config['CSV_YAPE_CONSOLIDADO']
    )
    procesar_carpeta_de_pdfs(
        app.config['CARPETA_AHORRO_PDFS'],
        app.config['CSV_AHORRO_CONSOLIDADO']
    )
    unificar_y_conciliar_reportes(
        app.config['CSV_YAPE_CONSOLIDADO'],
        app.config['CSV_AHORRO_CONSOLIDADO'],
        app.config['REPORTE_FINAL']
    )

    print("✅ Pipeline de datos completado.")

@app.route('/api/data')
def get_data():
    """
    Devuelve los datos financieros. Si el reporte no existe, ejecuta el pipeline.
    """
    print("Petición recibida en /api/data.")
    reporte_final = app.config['REPORTE_FINAL']

    if not os.path.exists(reporte_final):
        print(f"   -> No se encontró '{reporte_final}'. Ejecutando el pipeline...")
        run_data_pipeline()

    print(f"   -> Leyendo reporte final '{reporte_final}' para la respuesta.")
    try:
        df = pd.read_csv(reporte_final, sep=';')
        data = df.to_dict(orient='records')
        print("   -> Datos listos para enviar.")
        return jsonify(data)
    except FileNotFoundError:
        msg = f"El archivo '{reporte_final}' no se encontró incluso después de ejecutar el pipeline."
        print(f"   -> ❌ Error: {msg}")
        return jsonify({"error": msg}), 500
    except Exception as e:
        print(f"   -> ❌ Error: Ocurrió un error al leer o convertir el CSV final: {e}")
        return jsonify({"error": f"Error al leer el archivo CSV: {e}"}), 500

@app.route('/api/data/refresh', methods=['POST'])
def refresh_data():
    """Forza la re-ejecución de todo el pipeline de datos."""
    print("Petición recibida en /api/data/refresh. Forzando actualización...")
    run_data_pipeline()
    return jsonify({"status": "success", "message": "Los datos han sido actualizados."})

if __name__ == '__main__':
    app.run(debug=True, port=5001)
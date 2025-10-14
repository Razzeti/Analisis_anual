import pytest
from app import app as flask_app
import os
import json

# --- Configuración del Entorno de Prueba ---

@pytest.fixture
def client():
    """
    Crea y configura un cliente de prueba para la aplicación Flask.
    Este es un 'fixture' de Pytest, lo que significa que se puede pasar a
    cualquier función de prueba para darle acceso al cliente de la app.
    """
    # Asegurarse de que los archivos de prueba existen antes de ejecutar.
    # Creamos archivos CSV de entrada falsos para que las pruebas no dependan
    # de los archivos reales del proyecto.
    test_yape_csv = "test_yape.csv"
    test_ahorro_csv = "test_ahorro.csv"

    with open(test_yape_csv, "w") as f:
        f.write("FECHA;DESCRIPCION;CARGOS / DEBE;ABONOS / HABER\n")
        f.write("01ENE;Ingreso Yape;0;100\n")

    with open(test_ahorro_csv, "w") as f:
        f.write("FECHA;DESCRIPCION;CARGOS / DEBE;ABONOS / HABER\n")
        f.write("01ENE;Gasto Ahorro;50;0\n")

    # Modificamos la configuración de la app para que use nuestros archivos de prueba.
    flask_app.config['TESTING'] = True
    flask_app.config['CSV_YAPE_CONSOLIDADO'] = test_yape_csv
    flask_app.config['CSV_AHORRO_CONSOLIDADO'] = test_ahorro_csv
    flask_app.config['REPORTE_FINAL'] = "test_reporte_final.csv"

    with flask_app.test_client() as client:
        yield client

    # --- Limpieza después de la prueba ---
    # Es una buena práctica eliminar los archivos creados para la prueba.
    os.remove(test_yape_csv)
    os.remove(test_ahorro_csv)
    if os.path.exists("test_reporte_final.csv"):
        os.remove("test_reporte_final.csv")

# --- Pruebas de la API ---

def test_api_data_endpoint(client):
    """
    Prueba el endpoint /api/data para asegurar que responde correctamente.
    """
    print("🧪 Ejecutando prueba para el endpoint /api/data...")

    # Realizamos una petición GET al endpoint /api/data
    response = client.get('/api/data')

    # 1. Verificar que la respuesta es exitosa (código 200)
    assert response.status_code == 200, f"Se esperaba el código 200 pero se recibió {response.status_code}"
    print("   -> ✅ Código de estado 200 OK.")

    # 2. Verificar que la respuesta es de tipo JSON
    assert response.content_type == 'application/json', f"Se esperaba 'application/json' pero se recibió '{response.content_type}'"
    print("   -> ✅ Content-Type es application/json.")

    # 3. Cargar los datos y verificar que no están vacíos
    data = json.loads(response.data)
    assert isinstance(data, list), "La respuesta JSON debería ser una lista."
    assert len(data) > 0, "La lista de transacciones no debería estar vacía."
    print(f"   -> ✅ La API devolvió {len(data)} transacciones.")

    # 4. Verificar la estructura del primer elemento
    #    Esto nos asegura que los datos tienen el formato que el frontend espera.
    first_transaction = data[0]
    expected_keys = ['FECHA', 'DESCRIPCION', 'CARGOS / DEBE', 'ABONOS / HABER', 'CUENTA_ORIGEN']
    for key in expected_keys:
        assert key in first_transaction, f"La clave esperada '{key}' no se encontró en la transacción."
    print("   -> ✅ La estructura de datos es correcta.")

def test_home_page_endpoint(client):
    """
    Prueba que la página principal (/) se carga correctamente.
    """
    print("\n🧪 Ejecutando prueba para el endpoint / (página principal)...")
    response = client.get('/')

    # Verificar que la página principal responde con éxito
    assert response.status_code == 200, f"Se esperaba el código 200 pero se recibió {response.status_code}"

    # Verificar que el contenido parece ser HTML
    assert b'Panel de Control Financiero Anual' in response.data, "El título no se encontró en la página principal."
    print("   -> ✅ Página principal cargada correctamente.")
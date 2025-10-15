import pytest
from app import app as flask_app
import os
import json
from unittest.mock import patch

# --- Fixtures de Pytest ---

@pytest.fixture
def client():
    """
    Configura la aplicación Flask para pruebas y proporciona un cliente de prueba.
    Este fixture se ejecuta antes de cada prueba que lo solicita.
    """
    # Usar un archivo de reporte final específico para las pruebas
    reporte_final_prueba = "test_reporte_maestro.csv"

    # Configuración de la app para el entorno de prueba
    flask_app.config['TESTING'] = True
    flask_app.config['REPORTE_FINAL'] = reporte_final_prueba

    # Limpiar cualquier archivo de prueba residual antes de empezar
    if os.path.exists(reporte_final_prueba):
        os.remove(reporte_final_prueba)

    # El 'yield' pasa el control al código de la prueba
    with flask_app.test_client() as client:
        yield client

    # --- Limpieza post-prueba ---
    # Este código se ejecuta después de que la prueba ha terminado
    if os.path.exists(reporte_final_prueba):
        os.remove(reporte_final_prueba)

def create_dummy_report(path):
    """Función de ayuda para crear un archivo de reporte falso."""
    with open(path, "w") as f:
        f.write("FECHA;DESCRIPCION;CARGOS / DEBE;ABONOS / HABER;CUENTA_ORIGEN\n")
        f.write("15JUL;Compra online;150.0;0.0;Ahorro\n")
        f.write("16JUL;Salario;0.0;3500.0;Ahorro\n")

# --- Pruebas de la API ---

@patch('app.run_data_pipeline')
def test_get_data_when_file_exists(mock_run_pipeline, client):
    """
    Prueba el endpoint GET /api/data cuando el archivo de reporte ya existe.
    El pipeline de datos NO debería ejecutarse.
    """
    print("\n🧪 Prueba: /api/data con archivo existente")

    # Preparación: Crear un reporte falso
    create_dummy_report(flask_app.config['REPORTE_FINAL'])

    # Ejecución: Llamar al endpoint
    response = client.get('/api/data')

    # Verificación
    assert response.status_code == 200
    mock_run_pipeline.assert_not_called() # El pipeline no debe ser llamado
    data = json.loads(response.data)
    assert len(data) == 2
    assert data[0]['DESCRIPCION'] == 'Compra online'
    print("   -> ✅ Éxito: Devuelve datos sin ejecutar el pipeline.")

@patch('app.run_data_pipeline')
def test_get_data_when_file_does_not_exist(mock_run_pipeline, client):
    """
    Prueba el endpoint GET /api/data cuando el archivo de reporte NO existe.
    El pipeline de datos SÍ debería ejecutarse.
    """
    print("\n🧪 Prueba: /api/data sin archivo existente")

    # Configurar el mock para que "cree" el archivo cuando se llame
    def side_effect():
        print("   -> Mock de run_data_pipeline llamado. Creando archivo...")
        create_dummy_report(flask_app.config['REPORTE_FINAL'])
    mock_run_pipeline.side_effect = side_effect

    # Ejecución: Llamar al endpoint
    response = client.get('/api/data')

    # Verificación
    assert response.status_code == 200
    mock_run_pipeline.assert_called_once() # El pipeline debe ser llamado una vez
    data = json.loads(response.data)
    assert len(data) == 2
    assert data[1]['DESCRIPCION'] == 'Salario'
    print("   -> ✅ Éxito: Ejecuta el pipeline y devuelve los datos.")

@patch('app.run_data_pipeline')
def test_refresh_data_endpoint(mock_run_pipeline, client):
    """
    Prueba el endpoint POST /api/data/refresh.
    Debe forzar la ejecución del pipeline de datos.
    """
    print("\n🧪 Prueba: /api/data/refresh")

    # Ejecución: Llamar al endpoint de actualización
    response = client.post('/api/data/refresh')

    # Verificación
    assert response.status_code == 200
    mock_run_pipeline.assert_called_once() # El pipeline debe ser llamado
    data = json.loads(response.data)
    assert data['status'] == 'success'
    print("   -> ✅ Éxito: Endpoint de actualización funciona correctamente.")

def test_home_page_loads_correctly(client):
    """
    Prueba que la página de inicio se carga sin errores.
    """
    print("\n🧪 Prueba: Carga de la página de inicio (/)")
    response = client.get('/')
    assert response.status_code == 200
    assert 'Análisis Financiero Anual'.encode('utf-8') in response.data
    print("   -> ✅ Éxito: La página de inicio se carga.")

@patch('app.pd.read_csv')
def test_get_data_handles_read_error(mock_read_csv, client):
    """
    Prueba cómo maneja el endpoint /api/data un error al leer el CSV.
    """
    print("\n🧪 Prueba: Manejo de errores en /api/data")

    # Preparación: Crear el archivo, pero hacer que la lectura falle
    create_dummy_report(flask_app.config['REPORTE_FINAL'])
    mock_read_csv.side_effect = Exception("Fallo de lectura simulado")

    # Ejecución
    response = client.get('/api/data')

    # Verificación
    assert response.status_code == 500
    data = json.loads(response.data)
    assert 'error' in data
    assert 'Fallo de lectura simulado' in data['error']
    print("   -> ✅ Éxito: La API maneja correctamente los errores de lectura.")
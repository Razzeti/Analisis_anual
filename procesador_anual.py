import os
import pandas as pd
# Importamos las funciones de nuestro otro archivo
from extractor import extraer_transacciones, analizar_reporte_consolidado
def procesar_carpeta_de_pdfs(carpeta_entrada, archivo_salida_final):
    """
    Función principal que orquesta el proceso completo:
    1. Busca todos los PDFs en una carpeta.
    2. Usa el extractor para procesar cada uno.
    3. Une todos los resultados en un único CSV.
    4. Limpia los archivos temporales.
    """
    print("🚀 Iniciando el Procesador Anual de Estados de Cuenta 🚀")
    
    # Lista para guardar los datos de todos los PDFs
    lista_de_datos = []
    
    # Buscamos todos los archivos en la carpeta de entrada
    for nombre_archivo in os.listdir(carpeta_entrada):
        if nombre_archivo.lower().endswith('.pdf'):
            ruta_pdf_completa = os.path.join(carpeta_entrada, nombre_archivo)
            
            # Creamos un nombre de archivo temporal para el CSV de este PDF
            ruta_csv_temporal = os.path.join(carpeta_entrada, f"temp_{nombre_archivo}.csv")
            
            # Usamos nuestra función importada para extraer los datos
            exito = extraer_transacciones(ruta_pdf_completa, ruta_csv_temporal)
            
            if exito:
                # Si la extracción fue exitosa, leemos el CSV temporal y lo añadimos a nuestra lista
                try:
                    df_temporal = pd.read_csv(ruta_csv_temporal, sep=';')
                    lista_de_datos.append(df_temporal)
                except pd.errors.EmptyDataError:
                    print(f"   -> El archivo temporal para '{nombre_archivo}' está vacío, se ignora.")
                
                # --- Limpieza ---
                # Eliminamos el archivo CSV temporal para mantener la carpeta limpia
                os.remove(ruta_csv_temporal)
                print(f"   -> 🧹 Archivo temporal '{os.path.basename(ruta_csv_temporal)}' eliminado.")

    # --- Consolidación ---
    if not lista_de_datos:
        print("\n❌ No se pudo extraer datos de ningún PDF. Proceso terminado.")
        return

    print(f"\n consolidating Consolidando los datos de {len(lista_de_datos)} archivo(s)...")
    
    # Unimos todos los DataFrames de la lista en uno solo
    df_consolidado = pd.concat(lista_de_datos, ignore_index=True)
    
    # Guardamos el resultado final en el archivo CSV conglomerado
    df_consolidado.to_csv(archivo_salida_final, index=False, sep=';', decimal='.')
    
    print(f"🎉 ¡Proceso completado! Todas las transacciones han sido guardadas en '{archivo_salida_final}' 🎉")
    
    # Finalmente, ejecutamos el análisis sobre el gran archivo consolidado
    analizar_reporte_consolidado(archivo_salida_final)


if __name__ == "__main__":
    # --- CONFIGURACIÓN PRINCIPAL ---
    
    # 1. Nombre de la carpeta donde tienes TODOS tus estados de cuenta en PDF.
    #    (Asegúrate de que esta carpeta exista dentro de tu proyecto).
    CARPETA_CON_PDFS = "yape"
    
    # 2. Nombre que tendrá el archivo CSV final con todas las transacciones unidas.
    REPORTE_CONSOLIDADO_CSV = "reporte_anual_consolidado.csv"
    
    # --- EJECUCIÓN ---
    procesar_carpeta_de_pdfs(CARPETA_CON_PDFS, REPORTE_CONSOLIDADO_CSV)
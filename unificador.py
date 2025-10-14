import pandas as pd
import os

try:
    from extractor import analizar_reporte_consolidado
except ImportError:
    print("⚠️  Advertencia: No se pudo encontrar el archivo 'extractor.py'. Se continuará sin el análisis detallado.")
    def analizar_reporte_consolidado(csv_path):
        print(f"-> El análisis detallado no se ejecutó porque falta 'extractor.py', pero el archivo consolidado '{csv_path}' ha sido creado.")

def unificar_y_conciliar_reportes(csv_yape, csv_ahorro, archivo_salida_final):
    """
    Carga reportes de dos cuentas, realiza una conciliación de las transferencias
    entre ellas, muestra un resumen y consolida las transacciones externas en un único archivo.
    """
    print("🚀 Iniciando el Conciliador de Cuentas 🚀")
    
    try:
        df_yape = pd.read_csv(csv_yape, sep=';')
        df_ahorro = pd.read_csv(csv_ahorro, sep=';')
        print("   -> Archivos CSV cargados correctamente.")
    except FileNotFoundError as e:
        print(f"❌ Error: No se pudo encontrar uno de los archivos CSV. Detalle: {e}")
        return

    # --- 1. PREPARACIÓN Y ESTANDARIZACIÓN DE DATOS ---
    df_yape['CUENTA_ORIGEN'] = 'Yape'
    df_ahorro['CUENTA_ORIGEN'] = 'Ahorro'
    df_total = pd.concat([df_yape, df_ahorro], ignore_index=True)
    
    # --- CORRECCIÓN CLAVE ---
    # Se añade 'SET': 'SEP' para manejar la abreviatura de Septiembre de tus archivos.
    meses_es = {
        'ENE': 'JAN', 'FEB': 'FEB', 'MAR': 'MAR', 'ABR': 'APR', 'MAY': 'MAY', 'JUN': 'JUN',
        'JUL': 'JUL', 'AGO': 'AUG', 'SET': 'SEP', 'SEP': 'SEP', 'OCT': 'OCT', 'NOV': 'NOV', 'DIC': 'DEC'
    }
    df_total['FECHA_TEMP'] = df_total['FECHA'].str.strip() + '2025'
    for mes_es, mes_en in meses_es.items():
        df_total['FECHA_TEMP'] = df_total['FECHA_TEMP'].str.replace(mes_es, mes_en, regex=False)
    df_total['Fecha_Completa'] = pd.to_datetime(df_total['FECHA_TEMP'], format='%d%b%Y', errors='coerce')

    # --- 2. AISLAR Y CONCILIAR TRANSFERENCIAS INTERNAS ---
    print("\n" + "="*50)
    print("🔍      INICIANDO CONCILIACIÓN DE TRANSFERENCIAS      🔍")
    print("="*50)
    
    transferencias = df_total[df_total['DESCRIPCION'].str.contains('TRAN.CTAS.PROP.BM', na=False)].copy()
    
    yape_transfers = transferencias[transferencias['CUENTA_ORIGEN'] == 'Yape'].copy()
    ahorro_transfers = transferencias[transferencias['CUENTA_ORIGEN'] == 'Ahorro'].copy()

    print(f"\nTotal de transferencias candidatas en 'Yape': {len(yape_transfers)}")
    print(f"Total de transferencias candidatas en 'Ahorro': {len(ahorro_transfers)}")
    
    enlazadas = []
    indices_enlazados_yape = set()
    indices_enlazados_ahorro = set()

    for idx_y, yape_row in yape_transfers.iterrows():
        for idx_a, ahorro_row in ahorro_transfers.iterrows():
            if idx_y in indices_enlazados_yape or idx_a in indices_enlazados_ahorro: continue
            
            if yape_row['Fecha_Completa'] == ahorro_row['Fecha_Completa'] and pd.notnull(yape_row['Fecha_Completa']):
                if yape_row['CARGOS / DEBE'] == ahorro_row['ABONOS / HABER'] and yape_row['CARGOS / DEBE'] > 0:
                    enlazadas.append(f"   - [Yape -> Ahorro] de S/ {yape_row['CARGOS / DEBE']:.2f} el {yape_row['Fecha_Completa'].strftime('%d/%m/%Y')}")
                    indices_enlazados_yape.add(idx_y)
                    indices_enlazados_ahorro.add(idx_a)
                    break
                elif yape_row['ABONOS / HABER'] == ahorro_row['CARGOS / DEBE'] and yape_row['ABONOS / HABER'] > 0:
                    enlazadas.append(f"   - [Ahorro -> Yape] de S/ {yape_row['ABONOS / HABER']:.2f} el {yape_row['Fecha_Completa'].strftime('%d/%m/%Y')}")
                    indices_enlazados_yape.add(idx_y)
                    indices_enlazados_ahorro.add(idx_a)
                    break

    # --- 3. MOSTRAR REPORTE DE CONCILIACIÓN EN PANTALLA ---
    print("\n✅ Transferencias Enlazadas Correctamente:")
    if enlazadas:
        for e in sorted(enlazadas): print(e)
    else:
        print("   - Ninguna.")

    print("\n❌ Transferencias 'Huérfanas' (sin par encontrado):")
    
    huerfanas_yape = yape_transfers.drop(list(indices_enlazados_yape))
    if not huerfanas_yape.empty:
        print("   En Cuenta Yape:")
        for _, row in huerfanas_yape.iterrows():
            tipo = "Salida" if row['CARGOS / DEBE'] > 0 else "Entrada"
            monto = row['CARGOS / DEBE'] if tipo == "Salida" else row['ABONOS / HABER']
            fecha_str = row['Fecha_Completa'].strftime('%d/%m/%Y') if pd.notnull(row['Fecha_Completa']) else "Fecha Inválida"
            print(f"     - {tipo} de S/ {monto:.2f} el {fecha_str} (Descripción: {row['DESCRIPCION']})")
            
    huerfanas_ahorro = ahorro_transfers.drop(list(indices_enlazados_ahorro))
    if not huerfanas_ahorro.empty:
        print("   En Cuenta de Ahorro:")
        for _, row in huerfanas_ahorro.iterrows():
            tipo = "Salida" if row['CARGOS / DEBE'] > 0 else "Entrada"
            monto = row['CARGOS / DEBE'] if tipo == "Salida" else row['ABONOS / HABER']
            fecha_str = row['Fecha_Completa'].strftime('%d/%m/%Y') if pd.notnull(row['Fecha_Completa']) else "Fecha Inválida"
            print(f"     - {tipo} de S/ {monto:.2f} el {fecha_str} (Descripción: {row['DESCRIPCION']})")
    
    if huerfanas_yape.empty and huerfanas_ahorro.empty:
        print("   - Ninguna. ¡Conciliación perfecta!")
        
    print("="*50)
    
    # --- 4. LIMPIEZA Y CREACIÓN DEL REPORTE FINAL ---
    indices_a_eliminar = transferencias.index
    df_limpio = df_total.drop(indices_a_eliminar).copy()
    df_limpio.dropna(subset=['Fecha_Completa'], inplace=True)
    
    print(f"\n🧹 Total de {len(indices_a_eliminar)} transferencias internas excluidas del reporte final.")
    
    df_limpio_ordenado = df_limpio.sort_values(by='Fecha_Completa').reset_index(drop=True)
    
    columnas_finales = ['FECHA', 'DESCRIPCION', 'CARGOS / DEBE', 'ABONOS / HABER', 'CUENTA_ORIGEN']
    df_final = df_limpio_ordenado[columnas_finales]

    df_final.to_csv(archivo_salida_final, index=False, sep=';', decimal='.')
    print(f"\n🎉 ¡Proceso completado! Reporte maestro limpio guardado en '{archivo_salida_final}' 🎉")
    
    analizar_reporte_consolidado(archivo_salida_final)

if __name__ == "__main__":
    CSV_YAPE = "reporte_anual_consolidado.csv"
    CSV_AHORRO = "reporte_anual_consolidado_AHORRO.csv"
    REPORTE_FINAL_UNIFICADO = "reporte_maestro_limpio.csv"
    
    unificar_y_conciliar_reportes(CSV_YAPE, CSV_AHORRO, REPORTE_FINAL_UNIFICADO)
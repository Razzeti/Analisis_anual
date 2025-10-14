import pdfplumber
import pandas as pd
import os
import re
import locale

def extraer_transacciones(pdf_path, csv_path):
    """
    Función definitiva que extrae transacciones de un PDF "aprendiendo" la posición
    visual de las columnas, en lugar de adivinar la estructura del texto.
    """
    print(f"📄 Procesando: '{os.path.basename(pdf_path)}' con el motor de análisis visual...")
    all_transactions = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            column_positions = {}
            
            for page in pdf.pages:
                # --- 1. APRENDER LA MAQUETACIÓN DE LA PÁGINA ---
                words = page.extract_words(x_tolerance=3, y_tolerance=3, keep_blank_chars=False)
                
                header_found = False
                for word in words:
                    text = word['text'].upper()
                    if 'DESCRIPCION' in text:
                        column_positions['descripcion'] = word['x0']
                    elif 'CARGOS' in text:
                        column_positions['cargos'] = word['x0']
                    elif 'ABONOS' in text:
                        column_positions['abonos'] = word['x0']
                        header_found = True
                
                # Si no se encuentra la cabecera en una página, asumimos que es una continuación
                if not header_found and not column_positions:
                    print(f"   -> ⚠️ No se encontró la cabecera en la página {page.page_number}. Saltando.")
                    continue

                # --- 2. RECONSTRUIR FILAS Y ASIGNAR PALABRAS A COLUMNAS ---
                lines = {}
                for word in words:
                    # Agrupar palabras por su posición vertical (línea)
                    line_top = round(word['top'])
                    if line_top not in lines:
                        lines[line_top] = []
                    lines[line_top].append(word)

                for top_pos in sorted(lines.keys()):
                    line_words = sorted(lines[top_pos], key=lambda w: w['x0'])
                    line_text = " ".join([w['text'] for w in line_words])
                    
                    # Verificar si la línea parece una transacción
                    if re.match(r'^\d{2}\w{3}', line_text):
                        fecha = line_words[0]['text']
                        descripcion, cargo_str, abono_str = "", "", ""
                        
                        for word in line_words[2:]: # Empezamos después de las dos fechas
                            if word['x0'] < column_positions.get('cargos', 999):
                                descripcion += f" {word['text']}"
                            elif word['x0'] < column_positions.get('abonos', 999):
                                cargo_str += word['text']
                            else:
                                abono_str += word['text']
                        
                        cargo = pd.to_numeric(cargo_str.replace(',', ''), errors='coerce') or 0.0
                        abono = pd.to_numeric(abono_str.replace(',', ''), errors='coerce') or 0.0

                        if cargo > 0 or abono > 0:
                            all_transactions.append({
                                'FECHA': fecha,
                                'DESCRIPCION': descripcion.strip(),
                                'CARGOS / DEBE': cargo,
                                'ABONOS / HABER': abono
                            })
                            
    except Exception as e:
        print(f"   -> ❌ Error crítico al leer el PDF: {e}")
        return False

    if not all_transactions:
        print("   -> ⚠️ No se encontraron transacciones en este PDF con el motor visual.")
        return False

    df = pd.DataFrame(all_transactions).fillna(0)
    df.to_csv(csv_path, index=False, sep=';', decimal='.')
    print(f"   -> ✅ ¡Éxito! {len(df)} transacciones extraídas correctamente.")
    return True

def analizar_reporte_consolidado(csv_path):
    """
    Lee el CSV consolidado y muestra el resumen. No necesita cambios.
    """
    print("\n" + "="*50)
    print("📊   ANÁLISIS CONSOLIDADO DEL REPORTE ANUAL   📊")
    print("="*50)

    try:
        df = pd.read_csv(csv_path, sep=';')
    except pd.errors.EmptyDataError:
        print("El archivo consolidado está vacío.")
        return

    if df.empty:
        print("No hay transacciones para analizar.")
        return
    
    meses_es = {
        'ENE': 'JAN', 'FEB': 'FEB', 'MAR': 'MAR', 'ABR': 'APR', 'MAY': 'MAY', 'JUN': 'JUN',
        'JUL': 'JUL', 'AGO': 'AUG', 'SEP': 'SEP', 'OCT': 'OCT', 'NOV': 'NOV', 'DIC': 'DEC'
    }
    df['Fecha_Traducida'] = df['FECHA'].str.strip().str[:2] + df['FECHA'].str.strip().str[2:5].map(meses_es)
    df['Fecha_Completa'] = pd.to_datetime(df['Fecha_Traducida'], format='%d%b', errors='coerce').apply(lambda dt: dt.replace(year=2025))
    df.dropna(subset=['Fecha_Completa'], inplace=True)
    df = df.sort_values(by='Fecha_Completa').reset_index(drop=True)

    if df.empty:
        print("No se encontraron transacciones con fechas válidas para analizar.")
        return

    try: locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
    except: locale.setlocale(locale.LC_TIME, '')
    
    total_entradas = df['ABONOS / HABER'].sum()
    total_salidas = df['CARGOS / DEBE'].sum()
    total_balance = total_entradas - total_salidas
    
    max_entrada = df.loc[df['ABONOS / HABER'].idxmax()]
    max_salida = df.loc[df['CARGOS / DEBE'].idxmax()]
    
    print("\n" + "─"*20 + " RESUMEN GENERAL " + "─"*20)
    print(f"🗓️ Periodo Analizado: {df['Fecha_Completa'].min().strftime('%d de %B de %Y')} al {df['Fecha_Completa'].max().strftime('%d de %B de %Y')}")
    print(f"📈 Total Entradas (Abonos): S/ {total_entradas:,.2f}")
    print(f"📉 Total Salidas (Cargos):   S/ {total_salidas:,.2f}")
    print(f"💰 Balance Neto del Periodo: S/ {total_balance:,.2f}")
    
    print("\n" + "─"*15 + " TRANSACCIONES DESTACADAS " + "─"*14)
    print("\n✅ Mayor Entrada (Abono):")
    print(f"   - Fecha: {max_entrada['Fecha_Completa'].strftime('%d/%m/%Y')}, Monto: S/ {max_entrada['ABONOS / HABER']:,.2f}")
    print(f"   - Desc: {max_entrada['DESCRIPCION']}")
    print("\n❌ Mayor Salida (Cargo):")
    print(f"   - Fecha: {max_salida['Fecha_Completa'].strftime('%d/%m/%Y')}, Monto: S/ {max_salida['CARGOS / DEBE']:,.2f}")
    print(f"   - Desc: {max_salida['DESCRIPCION']}")
    print("\n" + "="*50)
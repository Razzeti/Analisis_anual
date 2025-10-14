# Panel de Control Financiero Automatizado

Este proyecto proporciona una solución completa para visualizar tus finanzas personales a partir de estados de cuenta en formato PDF. La aplicación extrae automáticamente las transacciones, las consolida y las presenta en un dashboard interactivo y fácil de usar.

## ¿Cómo usar la aplicación?

1.  **Coloca tus PDFs:** Asegúrate de que tus estados de cuenta en formato PDF estén en las carpetas `yape/` y `ahorros/`.
2.  **Instala las dependencias:** Ejecuta `pip install -r requirements.txt` para instalar todo lo necesario (Flask, Pandas, etc.).
3.  **Inicia el servidor:** Corre el comando `python app.py`.
4.  **Abre tu navegador:** Ve a `http://127.0.0.1:5001` para ver tu dashboard financiero. La aplicación procesará los PDFs automáticamente al cargar la página.

## Mejoras Implementadas

Este proyecto ha transformado un proceso manual y propenso a errores en una aplicación web totalmente automatizada y dinámica.

1.  **Automatización Completa (End-to-End):** Se eliminó la necesidad de ejecutar scripts manualmente y de copiar y pegar datos. Ahora, la aplicación procesa los PDFs y actualiza la visualización con solo cargar la página.
2.  **Servidor Web Centralizado (Flask):** Se implementó un backend con Flask que actúa como el cerebro de la aplicación, orquestando el procesamiento de datos y sirviendo la interfaz de usuario.
3.  **API de Datos Dinámica:** Se creó un endpoint (`/api/data`) que proporciona los datos financieros en formato JSON, desacoplando completamente el frontend del backend. Esto hace que la aplicación sea más robusta y fácil de mantener.
4.  **Experiencia de Usuario Mejorada:** Se añadió un indicador de carga para informar al usuario que los datos se están procesando, mejorando la experiencia en lugar de mostrar una página en blanco.
5.  **Calidad de Código y Pruebas:**
    - Se han añadido **pruebas de backend** (`test_app.py`) para garantizar que la API funcione correctamente.
    - Se ha realizado una **verificación de frontend de extremo a extremo** con Playwright para asegurar que la interfaz visualice los datos como se espera.

## Propuestas de Mejora y Valor a Futuro

La plataforma actual es una base sólida. Aquí hay algunas ideas para llevarla al siguiente nivel:

*   **Carga de Archivos Interactiva:** Permitir al usuario subir los archivos PDF directamente desde la interfaz web, en lugar de tener que moverlos a una carpeta.
*   **Selección de Rango de Fechas:** Añadir un selector de fechas en el frontend para que el usuario pueda filtrar las visualizaciones y analizar periodos específicos (por ejemplo, el último mes, el último trimestre).
*   **Categorización de Gastos Inteligente:** Implementar una lógica (posiblemente con reglas o machine learning simple) para categorizar automáticamente los gastos (por ejemplo, "Comida", "Transporte", "Suscripciones"). Esto permitiría gráficos de gastos por categoría.
*   **Base de Datos Persistente:** En lugar de procesar los PDFs cada vez, se podría guardar el resultado en una base de datos (como SQLite). Esto haría que las cargas posteriores fueran instantáneas y abriría la puerta a análisis históricos más complejos.
*   **Seguridad y Autenticación:** Si la aplicación se va a desplegar en línea, añadir un sistema de inicio de sesión para proteger la información financiera.
*   **Exportación de Datos:** Añadir botones para exportar los datos procesados o los gráficos a formatos como CSV, Excel o PNG.

Este proyecto no solo resuelve el problema original, sino que sienta las bases para una herramienta de gestión financiera personal muy potente y escalable.
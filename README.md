# Generador de CV

Aplicación web para convertir los datos de una persona candidata en un currículum en PDF. Permite revisar y editar la información en un formulario, ver una vista previa y descargar el resultado con un diseño de dos columnas.

## Cómo usarla

1. Genera el JSON de la persona candidata con el notebook **«Sistema de selección estratégica de talento con IA»**.
2. Copia el JSON completo.
3. Abre la app, pulsa **Importar JSON**, pega el contenido y selecciona **Actualizar CV**.
4. Revisa la vista previa y, si hace falta, ajusta los datos desde el formulario.
5. Pulsa **Descargar CV** para guardar el PDF en tu equipo.

La app incluye datos de ejemplo para mostrar cómo se verá el CV antes de importar un JSON. El archivo se genera en memoria cuando se solicita y se envía directamente al navegador para su descarga: **el PDF no se guarda en Vercel, en una base de datos ni en otro almacenamiento remoto**. El JSON recibido tampoco se guarda en el servidor.

## Cómo funciona

La interfaz envía los datos a una API creada con FastAPI. La API genera el PDF con ReportLab y lo devuelve como respuesta. La vista previa se muestra en el navegador; al pulsar **Descargar CV**, el navegador descarga una copia local. `plantilla_cv.html` se conserva únicamente como referencia del diseño original.

## Desarrollo local

Con Python 3.12 o posterior:

```powershell
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload
```

Abre `http://127.0.0.1:8000`. La vista previa inicial y la importación de JSON no descargan archivos automáticamente.



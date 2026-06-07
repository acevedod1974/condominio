# Condominio

Portal de vecinos para gestionar y consultar residentes, inquilinos y vehículos
de forma sencilla. Proporciona una interfaz estática (`index.html`) que consume
una función serverless (`functions/obtener-vecinos.js`) y un pequeño script
Python (`app.py`) para preparar o transformar datos si es necesario.

Descripción corta: Portal de Vecinos — tablero web ligero para administración
de residentes e información de contacto en condominios.

Características

- Interfaz web responsive en `index.html`.
- Función serverless que expone los datos en `functions/obtener-vecinos.js`.
- Script Python `app.py` para procesar hojas de cálculo / preparar datos.

Requisitos

- Python 3.8+ (si vas a ejecutar `app.py`).
- Node.js + Netlify CLI (opcional, para ejecutar funciones serverless en local).

Instalación y ejecución (local)

1. Crear y activar un entorno virtual (opcional, para Python):

```bash
python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

2. Instalar dependencias Python (si vas a usar `app.py`):

```bash
pip install -r requirements.txt
```

3. Ejecutar el backend Python (si aplica):

```bash
python app.py
```

4. Servir la interfaz estática localmente (ej. Python simple HTTP):

```bash
# desde la raíz del proyecto
python -m http.server 8000
# abrir http://localhost:8000/index.html
```

5. (Opcional) Ejecutar funciones Netlify localmente:

```bash
# instalar netlify CLI si no lo tienes
npm install -g netlify-cli
# ejecutar en modo desarrollo
netlify dev
```

Estructura del proyecto

- `index.html` — Interfaz web cliente.
- `app.py` — Script Python para preparación / transformación de datos.
- `requirements.txt` — Dependencias Python.
- `functions/obtener-vecinos.js` — Función serverless que devuelve datos de vecinos.

Contribuir

- Abre un issue o PR en la rama `main`.
- Sigue el mismo estilo de código del proyecto y añade tests si corresponde.

Despliegue a Netlify (opcional)

1. Crear una cuenta en Netlify y conectar el repositorio (GitHub/GitLab).
2. Asegúrate de que el build command (si no hay compilación) esté vacío y que
   la carpeta de publicación sea la raíz del proyecto `/`.
3. Si usas las funciones serverless incluidas en `functions/`, Netlify las
   detectará automáticamente; en local puedes probar con:

```bash
npm install -g netlify-cli
netlify dev
```

4. Variables de entorno: configura cualquier secreto desde la interfaz de
   Netlify en Site settings → Build & deploy → Environment.

Nota: si tu sitio es puramente estático y usa `functions/` para la API,
Netlify desplegará ambas partes sin configuración adicional.

Licencia

- MIT

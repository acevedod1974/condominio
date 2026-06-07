const { getStore } = require("@netlify/blobs");

exports.handler = async function (event, context) {
  const SHEET_ID = "19q47kSS6G8Ho5v7vhj0OSzcTyfARD7kTwzTgh0MWjtg";
  const GOOGLE_CSV_URL = `https://docs.google.com/spreadsheets/d/${SHEET_ID}/export?format=csv&gid=0`;

  try {
    // Inicialización explícita del almacén de Blobs inyectando el contexto de Netlify
    const store = getStore({
      name: "censo_villa_icabaru",
      siteID: context.siteID,
      token:
        process.env.NETLIFY_PURPOSE === "build"
          ? undefined
          : context.clientContext?.custom?.netlify,
    });

    // Intentar extraer datos rápidos de la caché
    let cachedData = null;
    let metadata = { lastUpdated: 0 };

    try {
      cachedData = await store.get("lista_vecinos", { type: "json" });
      metadata = (await store.get("metadata_cache", { type: "json" })) || {
        lastUpdated: 0,
      };
    } catch (e) {
      console.log("Caché vacía o inicializándose por primera vez");
    }

    const cincoMinutos = 5 * 60 * 1000;
    const ahora = Date.now();

    // Si la caché está fresca, servirla de inmediato
    if (cachedData && ahora - metadata.lastUpdated < cincoMinutos) {
      return {
        statusCode: 200,
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*",
        },
        body: JSON.stringify({
          fuente: "netlify_blobs_cache",
          datos: cachedData,
        }),
      };
    }

    // Descargar datos vivos de Google Sheets
    const response = await fetch(GOOGLE_CSV_URL);
    if (!response.ok)
      throw new Error(
        `Google Sheets respondió con estatus: ${response.status}`,
      );

    const csvTexto = await response.text();

    // Separar filas de forma segura tolerando saltos de línea estándar
    const lineas = csvTexto.split(/\r?\n/);
    if (lineas.length < 2)
      throw new Error("El CSV no contiene suficientes filas de datos.");

    // Limpiar comillas iniciales y finales de una cabecera
    const cabeceras = lineas[0]
      .split(",")
      .map((h) => h.replace(/^"|"$/g, "").trim());

    // Mapeo flexible por palabras clave para blindar contra cambios menores en las etiquetas
    const mapaColumnas = {
      unidad: "apartamento",
      tipo_residente: "tipo_residente",
      propietario: "nombre_propietario",
      tel_prop: "telefono_propietario",
      inquilino: "nombre_inquilino",
      tel_inq: "telefono_inquilino",
      mascotas: "mascotas",
      tipomascotas: "tipos_mascotas",
      placa1: "placa_vehiculo_1",
      vehiculo1: "marca_modelo_1",
      color1: "color_vehiculo_1",
      placa2: "placa_vehiculo_2",
      vehiculo2: "marca_modelo_2",
      color2: "color_vehiculo_2",
      placa3: "placa_vehiculo_3",
      vehiculo3: "marca_modelo_3",
      color3: "color_vehiculo_3",
      emergencia: "contacto_emergencia",
      telemergencia: "telefono_emergencia",
    };

    const indices = {};
    Object.keys(mapaColumnas).forEach((clave) => {
      indices[clave] = cabeceras.findIndex((h) =>
        h
          .toLowerCase()
          .normalize("NFD")
          .replace(/[\u0300-\u036f]/g, "")
          .includes(mapaColumnas[clave]),
      );
    });

    const listadoProcesado = [];

    // Expresión regular veloz para dividir celdas respetando comas dentro de comillas
    const regexCSV = /(".*?"|[^",\s]+)(?=\s*,|\s*$)/g;

    for (let i = 1; i < lineas.length; i++) {
      const linea = lineas[i].trim();
      if (!linea) continue;

      const celdas = linea.match(regexCSV) || linea.split(",");

      const extraer = (clave) => {
        const idx = indices[clave];
        if (idx === undefined || idx === -1 || idx >= celdas.length) return "";
        let texto = celdas[idx].replace(/^"|"$/g, "").trim();

        if (["tel_prop", "tel_inq", "telemergencia"].includes(clave)) {
          if (texto.endsWith(".0")) texto = texto.slice(0, -2);
          if (texto.toLowerCase() === "nan" || texto === "0") texto = "";
        }
        return texto;
      };

      const unidad = extraer("unidad");
      if (!unidad || unidad.toLowerCase() === "nan" || unidad === "") continue;

      const registro = {
        unidad,
        tipo_residente: extraer("tipo_residente"),
        propietario: extraer("propietario"),
        tel_prop: extraer("tel_prop"),
        inquilino: extraer("inquilino"),
        tel_inq: extraer("tel_inq"),
        mascotas: extraer("mascotas"),
        tipomascotas: extraer("tipomascotas"),
        placa1: extraer("placa1"),
        vehiculo1: extraer("vehiculo1"),
        color1: extraer("color1"),
        placa2: extraer("placa2"),
        vehiculo2: extraer("vehiculo2"),
        color2: extraer("color2"),
        placa3: extraer("placa3"),
        vehiculo3: extraer("vehiculo3"),
        color3: extraer("color3"),
        emergencia: extraer("emergencia"),
        telemergencia: extraer("telemergencia"),
      };

      registro.search_index =
        `${registro.unidad} ${registro.propietario} ${registro.inquilino} ${registro.placa1} ${registro.placa2} ${registro.placa3} ${registro.vehiculo1} ${registro.vehiculo2} ${registro.vehiculo3}`.toLowerCase();

      listadoProcesado.push(registro);
    }

    // Intentar guardar en la caché de Blobs de forma asíncrona segura
    try {
      await store.set("lista_vecinos", JSON.stringify(listadoProcesado));
      await store.set("metadata_cache", JSON.stringify({ lastUpdated: ahora }));
    } catch (blobError) {
      console.log("Error escribiendo en Netlify Blobs:", blobError.message);
    }

    return {
      statusCode: 200,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
      },
      body: JSON.stringify({
        fuente: "google_sheets_fresco",
        datos: listadoProcesado,
      }),
    };
  } catch (error) {
    return {
      statusCode: 500,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
      },
      body: JSON.stringify({
        error: "Fallo crítico en el procesamiento del censo",
        detalle: error.message,
      }),
    };
  }
};

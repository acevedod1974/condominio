const { getStore } = require("@netlify/blobs");

exports.handler = async function (event, context) {
  const SHEET_ID = "19q47kSS6G8Ho5v7vhj0OSzcTyfARD7kTwzTgh0MWjtg";
  const GOOGLE_CSV_URL = `https://docs.google.com/spreadsheets/d/${SHEET_ID}/export?format=csv`;

  try {
    // 1. Conectar con el almacenamiento de Netlify Blobs
    const store = getStore("censo_villa_icabaru");

    // Intentar obtener la data de la caché
    let cachedData = await store.get("lista_vecinos", { type: "json" });
    let metadata = (await store.get("metadata_cache", { type: "json" })) || {
      lastUpdated: 0,
    };

    const cincoMinutos = 5 * 60 * 1000;
    const ahora = Date.now();

    // Si tenemos datos en caché y son recientes, los servimos de inmediato
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

    // 2. Si no hay caché o expiró, descargamos de Google Sheets
    const response = await fetch(GOOGLE_CSV_URL);
    if (!response.ok) throw new Error("Fallo al conectar con Google Sheets");

    const csvTexto = await response.text();

    // Parseador básico de CSV a JSON robusto
    const lineas = csvTexto.split(/\r?\n/);
    if (lineas.length < 2) throw new Error("El archivo CSV está vacío");

    const cabeceras = lineas[0]
      .split(",")
      .map((h) => h.replace(/"/g, "").trim());

    // Mapeo exacto de las columnas de tu formulario
    const mapa = {
      "Número de Unidad / Apartamento": "unidad",
      "Tipo de Residente": "tipo_residente",
      "Nombre Completo del Propietario": "propietario",
      "Número de Teléfono Celular Propietario": "tel_prop",
      "Nombre Completo del Inquilino / Residente": "inquilino",
      "Número de Teléfono Celular Inquilino / Residente": "tel_inq",
      "¿ Residen mascotas en el Apartamento?": "mascotas",
      "Tipos de Mascotas (Marque todas las que apliquen)": "tipomascotas",
      "Placa del Vehiculo 1": "placa1",
      "Marca / Modelo del Vehiculo 1": "vehiculo1",
      "Color del Vehiculo 1": "color1",
      "Placa del Vehiculo 2": "placa2",
      "Marca / Modelo del Vehiculo 2": "vehiculo2",
      "Color del Vehiculo 2": "color2",
      "Placa del Vehiculo 3": "placa3",
      "Marca / Modelo del Vehiculo 3": "vehiculo3",
      "Color del Vehiculo 3": "color3",
      "En caso de emergencia (médica, incendio, fuga, etc.), ¿a quién debemos contactar si no logramos comunicarnos con el titular?":
        "emergencia",
      "Número de Teléfono de Contacto de Emergencia": "telemergencia",
    };

    const indicesColumnas = {};
    cabeceras.forEach((cabecera, idx) => {
      if (mapa[cabecera]) indicesColumnas[mapa[cabecera]] = idx;
    });

    const listadoProcesado = [];

    // Procesar cada fila del CSV de forma segura
    for (let i = 1; i < lineas.length; i++) {
      if (!lineas[i].trim()) continue;

      // Manejo de comas internas usando expresiones regulares para evitar rupturas de celdas
      const celdas =
        lineas[i].match(/(".*?"|[^",\s]+)(?=\s*,|\s*$)/g) ||
        lineas[i].split(",");
      const limpio = (val) => (val || "").replace(/"/g, "").trim();

      const extraerCampo = (clave) => {
        const idx = indicesColumnas[clave];
        let texto = idx !== undefined ? limpio(celdas[idx]) : "";
        if (["tel_prop", "tel_inq", "telemergencia"].includes(clave)) {
          if (texto.endsWith(".0")) texto = texto.slice(0, -2);
          if (texto.toLowerCase() === "nan") texto = "";
        }
        return texto;
      };

      const unidad = extraerCampo("unidad");
      if (!unidad || unidad.toLowerCase() === "nan") continue;

      const registro = {
        unidad,
        tipo_residente: extraerCampo("tipo_residente"),
        propietario: extraerCampo("propietario"),
        tel_prop: extraerCampo("tel_prop"),
        inquilino: extraerCampo("inquilino"),
        tel_inq: extraerCampo("tel_inq"),
        mascotas: extraerCampo("mascotas"),
        tipomascotas: extraerCampo("tipomascotas"),
        placa1: extraerCampo("placa1"),
        vehiculo1: extraerCampo("vehiculo1"),
        color1: extraerCampo("color1"),
        placa2: extraerCampo("placa2"),
        vehiculo2: extraerCampo("vehiculo2"),
        color2: extraerCampo("color2"),
        placa3: extraerCampo("placa3"),
        vehiculo3: extraerCampo("vehiculo3"),
        color3: extraerCampo("color3"),
        emergencia: extraerCampo("emergencia"),
        telemergencia: extraerCampo("telemergencia"),
      };

      // Generación del índice de búsqueda en minúsculas para macheo instantáneo en JS
      registro.search_index =
        `${registro.unidad} ${registro.propietario} ${registro.inquilino} ${registro.placa1} ${registro.placa2} ${registro.placa3} ${registro.vehiculo1} ${registro.vehiculo2} ${registro.vehiculo3}`.toLowerCase();

      listadoProcesado.push(registro);
    }

    // 3. Guardar la nueva data procesada en Netlify Blobs para las próximas llamadas
    await store.set("lista_vecinos", JSON.stringify(listadoProcesado));
    await store.set("metadata_cache", JSON.stringify({ lastUpdated: ahora }));

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
    // Si todo falla catastróficamente, intentar servir la última caché disponible como salvavidas
    try {
      const store = getStore("censo_villa_icabaru");
      let cachedData = await store.get("lista_vecinos", { type: "json" });
      if (cachedData) {
        return {
          statusCode: 200,
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            fuente: "netlify_blobs_failover",
            datos: cachedData,
            error: error.message,
          }),
        };
      }
    } catch (e) {}

    return {
      statusCode: 500,
      body: JSON.stringify({
        error: "Error procesando el censo",
        detalle: error.message,
      }),
    };
  }
};

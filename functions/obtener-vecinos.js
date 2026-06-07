const { getStore } = require("@netlify/blobs");

exports.handler = async function (event, context) {
  const SHEET_ID = "19q47kSS6G8Ho5v7vhj0OSzcTyfARD7kTwzTgh0MWjtg";
  // Exportamos directamente por el ID de la hoja de respuestas (gid=0 suele ser la principal)
  const GOOGLE_CSV_URL = `https://docs.google.com/spreadsheets/d/${SHEET_ID}/export?format=csv&gid=0`;

  try {
    const store = getStore("censo_villa_icabaru");

    // Intentar extraer datos rápidos de la caché de Netlify Blobs
    let cachedData = await store.get("lista_vecinos", { type: "json" });
    let metadata = (await store.get("metadata_cache", { type: "json" })) || {
      lastUpdated: 0,
    };

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

    // Parseador robusto de CSV que tolera saltos de línea y comas internas en las celdas
    const filas = [];
    let filaActual = [];
    let celdaActual = "";
    let dentroDeComillas = false;

    for (let i = 0; i < csvTexto.length; i++) {
      const char = csvTexto[i];
      const siguienteChar = csvTexto[i + 1];

      if (char === '"') {
        if (dentroDeComillas && siguienteChar === '"') {
          celdaActual += '"';
          i++;
        } else {
          dentroDeComillas = !dentroDeComillas;
        }
      } else if (char === "," && !dentroDeComillas) {
        filaActual.push(celdaActual.trim());
        celdaActual = "";
      } else if ((char === "\r" || char === "\n") && !dentroDeComillas) {
        if (char === "\r" && siguienteChar === "\n") i++;
        filaActual.push(celdaActual.trim());
        if (filaActual.some((c) => c !== "")) filas.push(filaActual);
        filaActual = [];
        celdaActual = "";
      } else {
        celdaActual += char;
      }
    }
    if (celdaActual || filaActual.length > 0) {
      filaActual.push(celdaActual.trim());
      filas.push(filaActual);
    }

    if (filas.length < 2)
      throw new Error("El CSV no contiene suficientes filas de datos.");

    // Mapeo flexible: Busca coincidencias tanto por el nombre interno como por la etiqueta visible
    const cabeceras = filas[0];
    const mapaColumnas = {
      unidad: ["Número de Unidad / Apartamento", "numero_unidad"],
      tipo_residente: ["Tipo de Residente", "tipo_residente"],
      propietario: ["Nombre Completo del Propietario", "nombre_propietario"],
      tel_prop: [
        "Número de Teléfono Celular Propietario",
        "telefono_propietario",
      ],
      inquilino: [
        "Nombre Completo del Inquilino / Residente",
        "nombre_inquilino",
      ],
      tel_inq: [
        "Número de Teléfono Celular Inquilino / Residente",
        "telefono_inquilino",
      ],
      mascotas: ["¿ Residen mascotas en el Apartamento?", "residen_mascotas"],
      tipomascotas: [
        "Tipos de Mascotas (Marque todas las que apliquen)",
        "tipos_mascotas",
      ],
      placa1: ["Placa del Vehiculo 1", "placa_vehiculo_1"],
      vehiculo1: ["Marca / Modelo del Vehiculo 1", "marca_modelo_1"],
      color1: ["Color del Vehiculo 1", "color_vehiculo_1"],
      placa2: ["Placa del Vehiculo 2", "placa_vehiculo_2"],
      vehiculo2: ["Marca / Modelo del Vehiculo 2", "marca_modelo_2"],
      color2: ["Color del Vehiculo 2", "color_vehiculo_2"],
      placa3: ["Placa del Vehiculo 3", "placa_vehiculo_3"],
      vehiculo3: ["Marca / Modelo del Vehiculo 3", "marca_modelo_3"],
      color3: ["Color del Vehiculo 3", "color_vehiculo_3"],
      emergencia: [
        "En caso de emergencia (médica, incendio, fuga, etc.), ¿a quién debemos contactar si no logramos comunicarnos con el titular?",
        "contacto_emergencia",
      ],
      telemergencia: [
        "Número de Teléfono de Contacto de Emergencia",
        "telefono_emergencia",
      ],
    };

    const indices = {};
    Object.keys(mapaColumnas).forEach((clave) => {
      indices[clave] = cabeceras.findIndex((h) =>
        mapaColumnas[clave].some((opcion) =>
          h.toLowerCase().includes(opcion.toLowerCase()),
        ),
      );
    });

    const listadoProcesado = [];

    // Procesar las filas de respuestas
    for (let i = 1; i < filas.length; i++) {
      const r = filas[i];

      const extraer = (clave) => {
        const idx = indices[clave];
        if (idx === undefined || idx === -1 || idx >= r.length) return "";
        let texto = r[idx].replace(/^"|"$/g, "").trim(); // Remover comillas remanentes

        // Limpieza de sufijos flotantes .0 en teléfonos
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

      // Mapeo estético de etiquetas internas de ODK/XLSForm a texto legible
      if (registro.tipo_residente === "propietario_residente")
        registro.tipo_residente = "Propietario Residente";
      if (registro.tipo_residente === "inquilino_arrendatario")
        registro.tipo_residente = "Inquilino / Arrendatario";

      // Generar índice de búsqueda completo
      registro.search_index =
        `${registro.unidad} ${registro.propietario} ${registro.inquilino} ${registro.placa1} ${registro.placa2} ${registro.placa3} ${registro.vehiculo1} ${registro.vehiculo2} ${registro.vehiculo3}`.toLowerCase();

      listadoProcesado.push(registro);
    }

    // Actualizar caché en Netlify Blobs
    if (listadoProcesado.length > 0) {
      await store.set("lista_vecinos", JSON.stringify(listadoProcesado));
      await store.set("metadata_cache", JSON.stringify({ lastUpdated: ahora }));
    }

    return {
      statusCode: 200,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type",
      },
      body: JSON.stringify({
        fuente: "google_sheets_fresco",
        datos: listadoProcesado,
      }),
    };
  } catch (error) {
    // Mecanismo de emergencia: Si Google Sheets falla o el parseo se interrumpe, servir la última caché guardada
    try {
      const store = getStore("censo_villa_icabaru");
      let cachedData = await store.get("lista_vecinos", { type: "json" });
      if (cachedData) {
        return {
          statusCode: 200,
          headers: {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
          },
          body: JSON.stringify({
            fuente: "netlify_blobs_failover",
            datos: cachedData,
            aviso: error.message,
          }),
        };
      }
    } catch (e) {}

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

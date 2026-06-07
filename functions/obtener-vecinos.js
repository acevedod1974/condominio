exports.handler = async function (event, context) {
  const SHEET_ID = "19q47kSS6G8Ho5v7vhj0OSzcTyfARD7kTwzTgh0MWjtg";
  // Prefer a published CSV URL (public), or fall back to the Sheets export URL.
  // You can override by setting the env var GOOGLE_PUBLISHED_CSV_URL
  const PUBLISHED_CSV =
    process.env.GOOGLE_PUBLISHED_CSV_URL ||
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vS5UhDyEqzkr97IY4o2ubhudvKcl4v5l_sR6VqNhoSLM2FrttTVHxVHSr5eIOE-3Sk8f7sJ086oKIgF/pub?gid=2131621513&single=true&output=csv";
  const GOOGLE_CSV_URL =
    PUBLISHED_CSV ||
    `https://docs.google.com/spreadsheets/d/${SHEET_ID}/export?format=csv&gid=0`;
  console.log("Using CSV URL:", GOOGLE_CSV_URL);

  try {
    const https = require("https");
    const http = require("http");

    // Fetch wrapper that follows redirects (needed for Google Sheets export)
    const doFetch = (url, redirects = 0) => {
      if (typeof fetch === "function") return fetch(url);
      return new Promise((resolve, reject) => {
        if (redirects > 5) return reject(new Error("Too many redirects"));
        try {
          const u = new URL(url);
          const lib = u.protocol === "https:" ? https : http;
          const opts = {
            method: "GET",
            headers: {
              "User-Agent": "node-fetch/1.0",
              Accept: "*/*",
            },
          };

          const req = lib.request(u, opts, (res) => {
            const { statusCode, headers } = res;
            if (statusCode >= 300 && statusCode < 400 && headers.location) {
              // follow redirect
              res.resume();
              const loc = headers.location.startsWith("http")
                ? headers.location
                : `${u.protocol}//${u.host}${headers.location}`;
              return resolve(doFetch(loc, redirects + 1));
            }

            let data = "";
            res.on("data", (chunk) => (data += chunk));
            res.on("end", () => {
              resolve({
                ok: statusCode >= 200 && statusCode < 300,
                status: statusCode,
                text: async () => data,
                headers,
              });
            });
          });

          req.on("error", (err) => reject(err));
          req.end();
        } catch (err) {
          reject(err);
        }
      });
    };
    // 1. Intentar usar Netlify Blobs si está disponible nativamente
    let store = null;
    let cachedData = null;

    try {
      const { getStore } = require("@netlify/blobs");
      store = getStore({
        name: "censo_villa_icabaru",
        siteID: context.siteID,
        token:
          context.clientContext?.custom?.netlify ||
          process.env.NETLIFY_AUTH_TOKEN,
      });

      if (store) {
        cachedData = await store.get("lista_vecinos", { type: "json" });
        let metadata = (await store.get("metadata_cache", {
          type: "json",
        })) || { lastUpdated: 0 };
        const cincoMinutos = 5 * 60 * 1000;

        if (cachedData && Date.now() - metadata.lastUpdated < cincoMinutos) {
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
      }
    } catch (e) {
      console.log(
        "Aviso: Modo Directo Activo (Saltando caché de Blobs):",
        e.message,
      );
    }

    // 2. Descarga directa desde Google Sheets (Failover)
    const response = await doFetch(GOOGLE_CSV_URL);
    if (!response.ok)
      throw new Error(
        `Google Sheets respondió con estatus: ${response.status}`,
      );

    const csvTexto = await response.text();

    // Split into lines (keep empty lines trimmed later)
    const lineas = csvTexto.split(/\r?\n/);
    if (lineas.length < 2)
      throw new Error("El archivo CSV está vacío o corrupto");

    // Robust CSV line parser: handles quoted fields, escaped quotes, and commas inside quotes
    const parseCSVLine = (line) => {
      const out = [];
      let cur = "";
      let inQuotes = false;
      for (let i = 0; i < line.length; i++) {
        const ch = line[i];
        if (inQuotes) {
          if (ch === '"') {
            if (i + 1 < line.length && line[i + 1] === '"') {
              cur += '"';
              i++;
            } else {
              inQuotes = false;
            }
          } else {
            cur += ch;
          }
        } else {
          if (ch === '"') {
            inQuotes = true;
          } else if (ch === ",") {
            out.push(cur);
            cur = "";
          } else {
            cur += ch;
          }
        }
      }
      out.push(cur);
      return out.map((s) => (s === undefined || s === null ? "" : String(s)));
    };

    // Parse headers using robust parser
    const cabecerasRaw = parseCSVLine(lineas[0] || "");
    const cabeceras = cabecerasRaw.map((h) => String(h || "").trim());

    // MAPEO EXACTO: Debe coincidir con las cabeceras literales del CSV exportado desde Google Sheets
    const mapaColumnas = {
      unidad: "Número de Unidad / Apartamento",
      tipo_residente: "Tipo de Residente",
      propietario: "Nombre Completo del Propietario",
      tel_prop: "Número de Teléfono Celular Propietario",
      inquilino: "Nombre Completo del Inquilino / Residente",
      tel_inq: "Número de Teléfono Celular Inquilino / Residente",
      mascotas: "¿ Residen mascotas en el Apartamento?",
      tipomascotas: "Tipos de Mascotas (Marque todas las que apliquen)",
      placa1: "Placa del Vehiculo 1",
      vehiculo1: "Marca / Modelo del Vehiculo 1",
      color1: "Color del Vehiculo 1",
      placa2: "Placa del Vehiculo 2",
      vehiculo2: "Marca / Modelo del Vehiculo 2",
      color2: "Color del Vehiculo 2",
      placa3: "Placa del Vehiculo 3",
      vehiculo3: "Marca / Modelo del Vehiculo 3",
      color3: "Color del Vehiculo 3",
      emergencia:
        "En caso de emergencia (médica, incendio, fuga, etc.), ¿a quién debemos contactar si no logramos comunicarnos con el titular?",
      telemergencia: "Número de Teléfono de Contacto de Emergencia",
    };

    const normalize = (s) =>
      String(s || "")
        .toLowerCase()
        .normalize("NFD")
        .replace(/\p{Diacritic}/gu, "");

    // Helpers ported from the old Streamlit app for consistent sanitization and UI-ready fields
    const sanitizePhone = (raw) => {
      if (!raw && raw !== 0) return "";
      let t = String(raw).trim();
      if (t.endsWith(".0")) t = t.slice(0, -2);
      t = t.replace(/\s+/g, "");
      if (t.toLowerCase() === "nan" || t === "0") return "";
      return t;
    };

    const chooseTitular = (r) => {
      const hasInq =
        r.inquilino &&
        String(r.inquilino).trim() !== "" &&
        String(r.inquilino).toLowerCase() !== "nan";
      if (hasInq) {
        const telefono = r.tel_inq || r.tel_prop || "";
        return {
          nombreTitular: r.inquilino,
          telefono: telefono || "",
          sublinea: `Inquilino / Residente (Propietario: ${r.propietario || "No registrado"})`,
        };
      }
      return {
        nombreTitular: r.propietario || "No registrado",
        telefono: r.tel_prop || "",
        sublinea: "Propietario Residente",
      };
    };

    // Tolerant mapping: try exact match, then keyword-based match, then substring match
    const keywordMap = {
      unidad: ["unidad"],
      tipo_residente: ["tipo", "residente"],
      propietario: ["propietario", "nombre"],
      tel_prop: ["telefono", "propietario"],
      inquilino: ["inquilino", "nombre"],
      tel_inq: ["telefono", "inquilino"],
      mascotas: ["mascotas"],
      tipomascotas: ["tipos", "mascotas"],
      placa1: ["placa", "1"],
      vehiculo1: ["marca", "1"],
      color1: ["color", "1"],
      placa2: ["placa", "2"],
      vehiculo2: ["marca", "2"],
      color2: ["color", "2"],
      placa3: ["placa", "3"],
      vehiculo3: ["marca", "3"],
      color3: ["color", "3"],
      emergencia: ["emergencia"],
      telemergencia: ["telefono", "emergencia"],
    };

    const matchesKeywords = (h, keys) => {
      const hn = normalize(h);
      return keys.every((k) => hn.includes(k));
    };

    const indices = {};
    Object.keys(mapaColumnas).forEach((clave) => {
      const expected = mapaColumnas[clave];
      // 1) exact
      let idx = cabeceras.findIndex((h) => h === expected);
      // 2) keyword match
      if (idx === -1 && keywordMap[clave]) {
        idx = cabeceras.findIndex((h) => matchesKeywords(h, keywordMap[clave]));
      }
      // 3) fallback substring normalized
      if (idx === -1) {
        const expectedNorm = normalize(expected);
        idx = cabeceras.findIndex(
          (h) =>
            normalize(h).includes(expectedNorm) ||
            expectedNorm.includes(normalize(h)),
        );
      }
      indices[clave] = idx;
      if (idx === -1)
        console.log(
          `Warning: header not found for ${clave} (expected: ${expected})`,
        );
    });

    // Log para diagnóstico; útil cuando se activa ?debug=1 en la petición local
    console.log("Cabeceras detectadas:", cabeceras);
    console.log("Indices mapeados:", indices);

    const listadoProcesado = [];

    for (let i = 1; i < lineas.length; i++) {
      const linea = lineas[i];
      if (!linea || String(linea).trim() === "") continue;

      // Dividir celdas respetando comas internas encerradas en comillas
      let celdas = parseCSVLine(linea);

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
      if (!unidad || unidad.toLowerCase() === "nan") continue;

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

      // Aplicar sanitización de teléfonos
      registro.tel_prop = sanitizePhone(registro.tel_prop);
      registro.tel_inq = sanitizePhone(registro.tel_inq);
      registro.telemergencia = sanitizePhone(registro.telemergencia);

      // Computar titular unificado y teléfono preferente para facilitar frontend
      const titular = chooseTitular(registro);
      registro.nombreTitular = titular.nombreTitular;
      registro.telefono = titular.telefono;
      registro.sublinea = titular.sublinea;

      // Limpieza cosmética de etiquetas del formulario para el UI
      if (registro.tipo_residente === "propietario_residente")
        registro.tipo_residente = "Propietario Residente";
      if (registro.tipo_residente === "inquilino_arrendatario")
        registro.tipo_residente = "Inquilino / Arrendatario";

      // Índice unificado de coincidencia para búsquedas
      registro.search_index =
        `${registro.unidad} ${registro.propietario} ${registro.inquilino} ${registro.placa1} ${registro.placa2} ${registro.placa3} ${registro.vehiculo1} ${registro.vehiculo2} ${registro.vehiculo3}`.toLowerCase();

      listadoProcesado.push(registro);
    }

    // Si se solicita debug en la query string, devolver cabeceras e índices junto con los datos
    const debugMode = event?.queryStringParameters?.debug === "1";

    // Guardar asíncronamente en caché si la tienda de Blobs está activa
    if (store && listadoProcesado.length > 0) {
      try {
        await store.set("lista_vecinos", JSON.stringify(listadoProcesado));
        await store.set(
          "metadata_cache",
          JSON.stringify({ lastUpdated: Date.now() }),
        );
      } catch (e) {}
    }

    return {
      statusCode: 200,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
      },
      body: JSON.stringify({
        fuente: "google_sheets_vivos",
        datos: listadoProcesado,
        debug: debugMode ? { cabeceras, indices } : undefined,
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
        error: "Fallo procesando censo",
        detalle: error.message,
      }),
    };
  }
};

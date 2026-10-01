/*
  api.js
  --------
  Pequeño wrapper sobre fetch para hablar con el backend. Centraliza:
    - la URL base de la API
    - el guardado/lectura del token JWT en localStorage
    - el manejo de errores HTTP básicos

  Todo lo demás (auth.js, dashboard.js, admin.js) usa estas funciones en
  vez de llamar a fetch directamente, para no repetir esta lógica.
*/

const API_URL = "http://localhost:8000";

function obtenerToken() {
  return localStorage.getItem("token");
}

function guardarToken(token) {
  localStorage.setItem("token", token);
}

function borrarToken() {
  localStorage.removeItem("token");
}

async function apiFetch(path, { method = "GET", body = null, auth = true } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (auth) {
    const token = obtenerToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  const resp = await fetch(`${API_URL}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : null,
  });

  if (resp.status === 401) {
    borrarToken();
    window.location.href = "index.html";
    throw new Error("Sesión expirada");
  }

  if (!resp.ok) {
    let detalle = "Error en la solicitud";
    try {
      const data = await resp.json();
      detalle = data.detail || detalle;
    } catch (e) {}
    throw new Error(detalle);
  }

  if (resp.status === 204) return null;
  return resp.json();
}

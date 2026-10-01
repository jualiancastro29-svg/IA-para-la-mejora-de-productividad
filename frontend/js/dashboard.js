/*
  dashboard.js
  --------------
  Lógica del panel principal: navegación por pestañas, inicio/fin de
  sesión de estudio, y actualización en vivo de los contadores por
  estado mientras la sesión está activa (polling simple cada 3s).

  NOTA DE INTEGRACIÓN CON IA: este frontend NO corre el modelo de
  detección directamente (eso vive en ai_detection/, aparte). Lo que
  este panel hace es: 1) avisar al backend que una sesión empezó/terminó,
  y 2) mostrar en vivo lo que el backend ya tiene registrado (los
  eventos que el script de IA vaya enviando por su cuenta a
  POST /sesiones/{id}/eventos). Si deciden correr la detección dentro
  del navegador en el futuro, aquí es donde se conectaría.
*/

const ESTADOS = [
  "Concentrado", "Distraido", "Dormido", "Somnoliento",
  "RevisandoTelefono", "Escribiendo", "Leyendo",
  "HablandoConOtraPersona", "Ausente",
];

let sesionActivaId = null;
let intervaloPolling = null;

document.addEventListener("DOMContentLoaded", async () => {
  if (!obtenerToken()) {
    window.location.href = "index.html";
    return;
  }

  await cargarUsuarioActual();
  configurarTabs();
  configurarBotonesSesion();
  await revisarSesionActiva();

  document.getElementById("btn-cerrar-sesion").addEventListener("click", () => {
    borrarToken();
    window.location.href = "index.html";
  });
});

async function cargarUsuarioActual() {
  const usuario = await apiFetch("/auth/me");
  document.getElementById("nombre-usuario").textContent = usuario.nombre_completo;

  if (usuario.rol === "admin") {
    document.getElementById("tab-admin-boton").classList.remove("oculto");
    cargarPanelAdmin();
  }
}

function configurarTabs() {
  const botones = document.querySelectorAll(".tab-boton");
  botones.forEach((btn) => {
    btn.addEventListener("click", () => {
      botones.forEach((b) => b.classList.remove("activo"));
      document.querySelectorAll(".tab-contenido").forEach((c) => c.classList.add("oculto"));
      btn.classList.add("activo");
      document.getElementById(btn.dataset.tab).classList.remove("oculto");
    });
  });
}

function configurarBotonesSesion() {
  document.getElementById("btn-iniciar-sesion-estudio").addEventListener("click", iniciarSesionEstudio);
  document.getElementById("btn-terminar-sesion-estudio").addEventListener("click", terminarSesionEstudio);
}

async function revisarSesionActiva() {
  const activa = await apiFetch("/sesiones/activa");
  if (activa) {
    sesionActivaId = activa.id;
    mostrarEstadoSesion(true);
    iniciarPolling();
  }
}

async function iniciarSesionEstudio() {
  try {
    const sesion = await apiFetch("/sesiones/iniciar", { method: "POST" });
    sesionActivaId = sesion.id;
    mostrarEstadoSesion(true);
    renderizarContadores({});
    iniciarPolling();
  } catch (err) {
    alert(err.message);
  }
}

async function terminarSesionEstudio() {
  if (!sesionActivaId) return;
  detenerPolling();

  const resumen = await apiFetch(`/sesiones/${sesionActivaId}/finalizar`, { method: "POST" });
  sesionActivaId = null;
  mostrarEstadoSesion(false);
  mostrarResumen(resumen);
}

function mostrarEstadoSesion(activa) {
  document.getElementById("btn-iniciar-sesion-estudio").classList.toggle("oculto", activa);
  document.getElementById("btn-terminar-sesion-estudio").classList.toggle("oculto", !activa);
  document.getElementById("panel-contadores").classList.toggle("oculto", !activa);
  document.getElementById("panel-resumen").classList.add("oculto");
}

function iniciarPolling() {
  actualizarContadores();
  intervaloPolling = setInterval(actualizarContadores, 3000);
}

function detenerPolling() {
  if (intervaloPolling) clearInterval(intervaloPolling);
  intervaloPolling = null;
}

async function actualizarContadores() {
  if (!sesionActivaId) return;
  try {
    const resumen = await apiFetch(`/sesiones/${sesionActivaId}/resumen`);
    renderizarContadores(resumen.conteo_por_estado);
  } catch (err) {
    console.error(err);
  }
}

function renderizarContadores(conteo) {
  const contenedor = document.getElementById("panel-contadores");
  contenedor.innerHTML = "<h3>Detecciones en esta sesión</h3><div class='contador-estados' id='grid-contadores'></div>";
  const grid = document.getElementById("grid-contadores");

  ESTADOS.forEach((estado) => {
    const div = document.createElement("div");
    div.className = "contador-item";
    div.innerHTML = `<div class="numero">${conteo[estado] ?? 0}</div><div>${estado}</div>`;
    grid.appendChild(div);
  });
}

function mostrarResumen(resumen) {
  const panel = document.getElementById("panel-resumen");
  panel.classList.remove("oculto");

  const minutos = resumen.duracion_segundos ? Math.round(resumen.duracion_segundos / 60) : 0;

  let html = `<h3>Resumen de la sesión</h3><p>Duración: ${minutos} minutos</p>`;
  html += "<div class='contador-estados'>";
  ESTADOS.forEach((estado) => {
    html += `<div class="contador-item"><div class="numero">${resumen.conteo_por_estado[estado] ?? 0}</div><div>${estado}</div></div>`;
  });
  html += "</div>";

  html += "<h3>Recomendaciones</h3><ul>";
  resumen.recomendaciones.forEach((r) => (html += `<li>${r}</li>`));
  html += "</ul>";

  panel.innerHTML = html;
}

// ---------------- Panel de administración de usuarios ----------------

async function cargarPanelAdmin() {
  await refrescarListaUsuarios();

  document.getElementById("form-crear-usuario").addEventListener("submit", async (e) => {
    e.preventDefault();
    const username = document.getElementById("admin-username").value.trim();
    const password = document.getElementById("admin-password").value;
    const nombre_completo = document.getElementById("admin-nombre").value.trim();
    const rol = document.getElementById("admin-rol").value;

    try {
      await apiFetch("/admin/usuarios", {
        method: "POST",
        body: { username, password, nombre_completo, rol },
      });
      document.getElementById("form-crear-usuario").reset();
      await refrescarListaUsuarios();
    } catch (err) {
      alert(err.message);
    }
  });
}

async function refrescarListaUsuarios() {
  const usuarios = await apiFetch("/admin/usuarios");
  const tbody = document.getElementById("tabla-usuarios-body");
  tbody.innerHTML = "";

  usuarios.forEach((u) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${u.username}</td>
      <td>${u.nombre_completo}</td>
      <td><span class="etiqueta-rol">${u.rol}</span></td>
      <td>${u.activo ? "Activo" : "Inactivo"}</td>
      <td>
        <button class="secundario" data-accion="toggle-activo" data-id="${u.id}" data-activo="${u.activo}">
          ${u.activo ? "Desactivar" : "Activar"}
        </button>
        <button class="secundario" data-accion="toggle-rol" data-id="${u.id}" data-rol="${u.rol}">
          Hacer ${u.rol === "admin" ? "usuario" : "admin"}
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });

  tbody.querySelectorAll("button[data-accion='toggle-activo']").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const activo = btn.dataset.activo === "true";
      await apiFetch(`/admin/usuarios/${btn.dataset.id}/estado`, {
        method: "PATCH",
        body: { activo: !activo },
      });
      await refrescarListaUsuarios();
    });
  });

  tbody.querySelectorAll("button[data-accion='toggle-rol']").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const nuevoRol = btn.dataset.rol === "admin" ? "usuario" : "admin";
      await apiFetch(`/admin/usuarios/${btn.dataset.id}/rol`, {
        method: "PATCH",
        body: { rol: nuevoRol },
      });
      await refrescarListaUsuarios();
    });
  });
}

/*
  auth.js
  ---------
  Lógica de la página de login/registro (index.html).
*/

document.addEventListener("DOMContentLoaded", () => {
  if (obtenerToken()) {
    window.location.href = "dashboard.html";
    return;
  }

  const formLogin = document.getElementById("form-login");
  const formRegistro = document.getElementById("form-registro");
  const errorLogin = document.getElementById("error-login");
  const errorRegistro = document.getElementById("error-registro");

  document.getElementById("mostrar-registro").addEventListener("click", (e) => {
    e.preventDefault();
    document.getElementById("seccion-login").classList.add("oculto");
    document.getElementById("seccion-registro").classList.remove("oculto");
  });

  document.getElementById("mostrar-login").addEventListener("click", (e) => {
    e.preventDefault();
    document.getElementById("seccion-registro").classList.add("oculto");
    document.getElementById("seccion-login").classList.remove("oculto");
  });

  formLogin.addEventListener("submit", async (e) => {
    e.preventDefault();
    errorLogin.textContent = "";
    const username = document.getElementById("login-username").value.trim();
    const password = document.getElementById("login-password").value;

    try {
      const data = await apiFetch("/auth/login", {
        method: "POST",
        body: { username, password },
        auth: false,
      });
      guardarToken(data.access_token);
      window.location.href = "dashboard.html";
    } catch (err) {
      errorLogin.textContent = err.message;
    }
  });

  formRegistro.addEventListener("submit", async (e) => {
    e.preventDefault();
    errorRegistro.textContent = "";
    const username = document.getElementById("reg-username").value.trim();
    const password = document.getElementById("reg-password").value;
    const nombre_completo = document.getElementById("reg-nombre").value.trim();

    try {
      await apiFetch("/auth/register", {
        method: "POST",
        body: { username, password, nombre_completo },
        auth: false,
      });
      alert("Cuenta creada. Ahora puedes iniciar sesión.");
      document.getElementById("mostrar-login").click();
      formRegistro.reset();
    } catch (err) {
      errorRegistro.textContent = err.message;
    }
  });
});

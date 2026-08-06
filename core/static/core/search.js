/* static/core/search.js
   Busca expansível da topbar — usada na lista de leitura e nas telas de cadastro.
   Fica separado do app.js porque as telas de cadastro têm o próprio closeModal(). */

document.addEventListener("DOMContentLoaded", () => {
    const toggleBtn = document.getElementById("searchToggleBtn");
    const form = document.getElementById("searchForm");
    const input = document.getElementById("searchInput");
    if (!toggleBtn || !form || !input) return;

    toggleBtn.addEventListener("click", () => {
        form.classList.add("search-open");
        input.focus();
    });

    input.addEventListener("blur", () => {
        if (!input.value) form.classList.remove("search-open");
    });
});

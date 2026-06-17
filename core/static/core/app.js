/* static/core/app.js */

// ── Sidebar mobile ────────────────────────────────────────────────────────
function toggleSidebar() {
    document.getElementById("sidebar").classList.toggle("open");
    document.getElementById("overlay").classList.toggle("open");
}

// ── Init: ajusta estado visual de cada card ao carregar ──────────────────
document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".issue-card").forEach(card => {
        initCard(card);
    });
});

function initCard(card) {
    const inCollection = card.dataset.inCollection === "true";
    const isRead = card.dataset.isRead === "true";

    const colBtn = card.querySelector(".collection-btn");
    const readBtn = card.querySelector(".read-btn");

    if (colBtn) setCollectionState(colBtn, inCollection);
    if (readBtn) setReadState(readBtn, isRead);
}

function setCollectionState(btn, inCollection) {
    const icon = btn.querySelector(".btn-icon");
    const label = btn.querySelector(".btn-label");

    if (inCollection) {
        btn.classList.add("in-collection");
        icon.textContent = "check_circle";
        label.textContent = "Na coleção";
    } else {
        btn.classList.remove("in-collection");
        icon.textContent = "add_circle";
        label.textContent = "Colecionar";
    }
}

function setReadState(btn, isRead) {
    const icon = btn.querySelector(".btn-icon");
    const label = btn.querySelector(".btn-label");

    if (isRead) {
        btn.classList.add("is-read");
        icon.textContent = "done_all";
        label.textContent = "Lido";
    } else {
        btn.classList.remove("is-read");
        icon.textContent = "bookmark_add";
        label.textContent = "Marcar lido";
    }
}

// ── Helpers HTTP ─────────────────────────────────────────────────────────
async function postJSON(url, body = {}) {
    const res = await fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": CSRF_TOKEN,
        },
        body: JSON.stringify(body),
    });
    return res.json();
}

// ── Toggle Coleção ────────────────────────────────────────────────────────
function handleCollection(event, btn) {
    event.stopPropagation();
    const card = btn.closest(".issue-card");
    const issueId = card.dataset.issueId;
    const url = TOGGLE_COLLECTION_URL + issueId + "/";

    if (btn.classList.contains("in-collection")) {
        openModal(
            "Remover esta edição da sua coleção?",
            async () => {
                const data = await postJSON(url, { confirm: true });
                if (data.status === "removed") {
                    card.dataset.inCollection = "false";
                    setCollectionState(btn, false);
                    // Remove badge se existir
                    const badge = card.querySelector(".card-collection-badge");
                    if (badge) badge.remove();
                }
            }
        );
    } else {
        postJSON(url).then(data => {
            if (data.status === "added") {
                card.dataset.inCollection = "true";
                setCollectionState(btn, true);
                // Adiciona badge de coleção
                const wrap = card.querySelector(".card-cover-wrap");
                if (wrap && !wrap.querySelector(".card-collection-badge")) {
                    const badge = document.createElement("div");
                    badge.className = "card-collection-badge";
                    badge.title = "Na coleção";
                    wrap.prepend(badge);
                }
            }
        });
    }
}

// ── Toggle Lido ───────────────────────────────────────────────────────────
function handleRead(event, btn) {
    event.stopPropagation();
    const card = btn.closest(".issue-card");
    const issueId = card.dataset.issueId;
    const url = TOGGLE_READ_URL + issueId + "/";

    if (btn.classList.contains("is-read")) {
        openModal(
            "Desmarcar esta edição como lida?",
            async () => {
                const data = await postJSON(url, { confirm: true });
                if (data.status === "removed") {
                    card.dataset.isRead = "false";
                    setReadState(btn, false);
                    // Remove badge se existir
                    const badge = card.querySelector(".card-read-badge");
                    if (badge) badge.remove();
                }
            }
        );
    } else {
        postJSON(url).then(data => {
            if (data.status === "added") {

                const inTitleDetail = typeof TITLE_DETAIL_MODE !== "undefined" && TITLE_DETAIL_MODE;

                if (inTitleDetail) {
                    // Na title_detail: só atualiza badge e botão, sem substituir card
                    card.dataset.isRead = "true";
                    setReadState(btn, true);
                    const wrap = card.querySelector(".card-cover-wrap");
                    if (wrap && !wrap.querySelector(".card-read-badge")) {
                        const badge = document.createElement("div");
                        badge.className = "card-read-badge";
                        badge.title = "Lido";
                        wrap.prepend(badge);
                    }
                } else {
                    // Na lista de leitura: anima saída e substitui/remove card
                    card.style.transition = "opacity .35s ease, transform .35s ease";
                    card.style.opacity = "0";
                    card.style.transform = "scale(.92)";

                    setTimeout(() => {
                        if (data.next) {
                            _replaceCard(card, data.next);
                        } else {
                            card.remove();
                            const grid = document.querySelector(".issue-grid");
                            if (grid && grid.children.length === 0) {
                                grid.insertAdjacentHTML("afterend",
                                    `<div class="empty-state">
                                        <span class="material-symbols-outlined empty-icon">check_circle</span>
                                        <p>Tudo lido por aqui!</p>
                                    </div>`
                                );
                                grid.remove();
                            }
                        }
                    }, 350);
                }
            }
        });
    }
}

// ── Constrói um card novo a partir dos dados JSON da próxima issue ────────
function _buildCard(next) {
    const inCollection = next.in_collection;
    const typeId = next.type_id;

    const coverHtml = next.image_url
        ? `<img src="${next.image_url}" alt="${_esc(next.name)}" class="card-cover" loading="lazy" />`
        : `<div class="card-cover card-cover--placeholder">
               <span class="material-symbols-outlined">image_not_supported</span>
           </div>`;

    let infoHtml;
    if (typeId === 2) {
        infoHtml = `
            <p class="card-title">${_esc(next.name)}</p>
            ${next.issue_number
                ? `<p class="card-subtitle">${_esc(next.title_name)} <span class="card-number">vol. ${_esc(next.issue_number)}</span></p>`
                : ""}
            <p class="card-meta">${_esc(next.publisher)}</p>`;
    } else {
        infoHtml = `
            <p class="card-title">
                ${_esc(next.title_name)}
                ${next.issue_number ? `<span class="card-number">#${_esc(next.issue_number)}</span>` : ""}
            </p>
            ${next.name && next.name !== next.title_name
                ? `<p class="card-subtitle">${_esc(next.name)}</p>`
                : ""}
            <p class="card-meta">
                ${_esc(next.publisher)}${next.date ? " · " + _esc(next.date) : ""}
            </p>`;
    }

    const colClass = inCollection ? "in-collection" : "";
    const colIcon = inCollection ? "check_circle" : "add_circle";
    const colLabel = inCollection ? "Na coleção" : "Colecionar";

    const card = document.createElement("article");
    card.className = "issue-card";
    card.dataset.issueId = next.id;
    card.dataset.inCollection = inCollection ? "true" : "false";
    card.dataset.isRead = "false";
    card.style.opacity = "0";
    card.style.transform = "scale(.92)";
    card.style.transition = "opacity .35s ease, transform .35s ease";
    card.setAttribute("onclick", `goToDetail(${next.id})`);

    card.innerHTML = `
        <div class="card-cover-wrap">
            ${coverHtml}
            <div class="card-actions">
                <button class="action-btn collection-btn ${colClass}" title="Coleção" onclick="handleCollection(event, this)">
                    <span class="material-symbols-outlined btn-icon">${colIcon}</span>
                    <span class="btn-label">${colLabel}</span>
                </button>
                <button class="action-btn read-btn" title="Lido" onclick="handleRead(event, this)">
                    <span class="material-symbols-outlined btn-icon">bookmark_add</span>
                    <span class="btn-label">Marcar lido</span>
                </button>
            </div>
        </div>
        <div class="card-info">${infoHtml}</div>`;

    return card;
}

// ── Substitui oldCard pelo novo card com animação de entrada ──────────────
function _replaceCard(oldCard, next) {
    const newCard = _buildCard(next);
    oldCard.replaceWith(newCard);
    requestAnimationFrame(() => {
        requestAnimationFrame(() => {
            newCard.style.opacity = "1";
            newCard.style.transform = "scale(1)";
        });
    });
}

// ── Escapa HTML para evitar XSS ──────────────────────────────────────────
function _esc(str) {
    if (!str) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}

// ── Modal genérico ────────────────────────────────────────────────────────
let _confirmCallback = null;

function openModal(msg, callback) {
    document.getElementById("confirmMsg").textContent = msg;
    document.getElementById("confirmModal").style.display = "flex";
    _confirmCallback = callback;
}

function closeModal() {
    document.getElementById("confirmModal").style.display = "none";
    _confirmCallback = null;
}

document.addEventListener("DOMContentLoaded", () => {
    const confirmBtn = document.getElementById("confirmBtn");
    if (confirmBtn) {
        confirmBtn.addEventListener("click", async () => {
            if (_confirmCallback) await _confirmCallback();
            closeModal();
        });
    }

    document.addEventListener("keydown", e => {
        if (e.key === "Escape") closeModal();
    });
});
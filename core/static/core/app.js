/* static/core/app.js */

function initCard(card) {
    const inCollection = card.dataset.inCollection === "true";
    const isRead = card.dataset.isRead === "true";
    setCollectionState(card.querySelector(".slj-collection-btn"), inCollection);
    setReadState(card.querySelector(".slj-read-btn"), isRead);
}

function setCollectionState(btn, inCollection) {
    const icon = btn.querySelector(".slj-btn-icon");
    const label = btn.querySelector(".slj-btn-label");
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
    const icon = btn.querySelector(".slj-btn-icon");
    const label = btn.querySelector(".slj-btn-label");
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

function sljInit() {
    document.querySelectorAll(".slj-issue-card").forEach(card => initCard(card));

    const confirmBtn = document.getElementById("confirmBtn");
    if (confirmBtn && !confirmBtn._sljBound) {
        confirmBtn._sljBound = true;
        confirmBtn.addEventListener("click", async () => {
            if (_confirmCallback) await _confirmCallback();
            closeModal();
        });
    }
    document.addEventListener("keydown", e => {
        if (e.key === "Escape") closeModal();
    });
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", sljInit);
} else {
    sljInit();
}

// ── HTTP ─────────────────────────────────────────────────────────────────
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

async function getJSON(url) {
    const res = await fetch(url);
    return res.json();
}

// ── Toggle Coleção ────────────────────────────────────────────────────────
function handleCollection(btn) {
    event.stopPropagation();
    const card = btn.closest(".slj-issue-card");
    const issueId = card.dataset.issueId;
    const url = TOGGLE_COLLECTION_URL + issueId + "/";

    if (btn.classList.contains("in-collection")) {
        openModal("Remover esta edição da sua coleção?", async () => {
            const data = await postJSON(url, { confirm: true });
            if (data.status === "removed") {
                card.dataset.inCollection = "false";
                setCollectionState(btn, false);
            }
        });
    } else {
        postJSON(url).then(data => {
            if (data.status === "added") {
                card.dataset.inCollection = "true";
                setCollectionState(btn, true);
            }
        });
    }
}

// ── Toggle Lido ───────────────────────────────────────────────────────────
function handleRead(btn) {
    event.stopPropagation();
    const card = btn.closest(".slj-issue-card");
    const issueId = card.dataset.issueId;
    const url = TOGGLE_READ_URL + issueId + "/";

    if (btn.classList.contains("is-read")) {
        openModal("Desmarcar esta edição como lida?", async () => {
            const data = await postJSON(url, { confirm: true });
            if (data.status === "removed") {
                card.dataset.isRead = "false";
                setReadState(btn, false);
            }
        });
    } else {
        postJSON(url).then(async data => {
            if (data.status === "added") {
                // Busca a próxima edição do título
                const next = await getJSON(NEXT_ISSUE_URL + issueId + "/");

                if (next.status === "completed") {
                    // Título concluído — remove o card com animação
                    card.style.transition = "opacity .4s, transform .4s";
                    card.style.opacity = "0";
                    card.style.transform = "scale(0.9)";
                    setTimeout(() => card.remove(), 400);
                } else if (next.status === "next") {
                    // Atualiza o card para a próxima edição
                    updateCard(card, next.issue);
                }
            }
        });
    }
}

function updateCard(card, issue) {
    // Atualiza data-attributes
    card.dataset.issueId = issue.id;
    card.dataset.inCollection = issue.in_collection ? "true" : "false";
    card.dataset.isRead = issue.is_read ? "true" : "false";

    // Capa
    const coverWrap = card.querySelector(".slj-card-cover-wrap");
    const existingImg = coverWrap.querySelector(".slj-card-cover:not(.slj-card-cover--placeholder)");
    const existingPlaceholder = coverWrap.querySelector(".slj-card-cover--placeholder");

    if (issue.image_url) {
        if (existingImg) {
            existingImg.src = issue.image_url;
            existingImg.alt = issue.name;
        } else {
            if (existingPlaceholder) existingPlaceholder.remove();
            const img = document.createElement("img");
            img.src = issue.image_url;
            img.alt = issue.name;
            img.className = "slj-card-cover";
            img.loading = "lazy";
            coverWrap.insertBefore(img, coverWrap.firstChild);
        }
    } else {
        if (existingImg) existingImg.remove();
        if (!existingPlaceholder) {
            const ph = document.createElement("div");
            ph.className = "slj-card-cover slj-card-cover--placeholder";
            ph.innerHTML = '<span class="material-symbols-outlined">image_not_supported</span>';
            coverWrap.insertBefore(ph, coverWrap.firstChild);
        }
    }

    // Info
    const titleEl = card.querySelector(".slj-card-title");
    titleEl.childNodes[0].textContent = issue.title_name + " ";
    const numEl = titleEl.querySelector(".slj-card-number");
    if (issue.issue_number) {
        if (numEl) numEl.textContent = "#" + issue.issue_number;
        else {
            const span = document.createElement("span");
            span.className = "slj-card-number";
            span.textContent = "#" + issue.issue_number;
            titleEl.appendChild(span);
        }
    } else if (numEl) {
        numEl.remove();
    }

    const subtitleEl = card.querySelector(".slj-card-subtitle");
    if (issue.name && issue.name !== issue.title_name) {
        if (subtitleEl) subtitleEl.textContent = issue.name;
    } else if (subtitleEl) {
        subtitleEl.textContent = "";
    }

    const metaEl = card.querySelector(".slj-card-meta");
    metaEl.textContent = [issue.publisher, issue.date].filter(Boolean).join(" · ");

    // Atualiza botões
    setCollectionState(card.querySelector(".slj-collection-btn"), issue.in_collection);
    setReadState(card.querySelector(".slj-read-btn"), issue.is_read);

    // Animação de troca
    card.style.transition = "opacity .2s";
    card.style.opacity = "0";
    setTimeout(() => { card.style.opacity = "1"; }, 200);
}

// ── Modal ─────────────────────────────────────────────────────────────────
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
/* static/core/app.js */

// ── Sidebar mobile ────────────────────────────────────────────────────────
function toggleSidebar() {
    document.getElementById("sidebar").classList.toggle("open");
    document.getElementById("overlay").classList.toggle("open");
}

// ── Init ──────────────────────────────────────────────────────────────────
function sljInit() {
    document.querySelectorAll(".issue-card").forEach(card => initCard(card));

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

// ── Estado dos cards ──────────────────────────────────────────────────────
function initCard(card) {
    const inCollection = card.dataset.inCollection === "true";
    const isRead = card.dataset.isRead === "true";
    setCollectionState(card.querySelector(".collection-btn"), inCollection);
    setReadState(card.querySelector(".read-btn"), isRead);
}

function setCollectionState(btn, inCollection) {
    if (!btn) return;
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
    if (!btn) return;
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

// ── HTTP ──────────────────────────────────────────────────────────────────
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
function handleRead(event, btn) {
    event.stopPropagation();
    const card = btn.closest(".issue-card");
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
        postJSON(url).then(data => {
            if (data.status === "added") {
                card.dataset.isRead = "true";
                setReadState(btn, true);
            }
        });
    }
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
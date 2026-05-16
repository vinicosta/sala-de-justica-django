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

    setCollectionState(colBtn, inCollection);
    setReadState(readBtn, isRead);
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
function handleCollection(btn) {
    const card = btn.closest(".issue-card");
    const issueId = card.dataset.issueId;
    const url = TOGGLE_COLLECTION_URL + issueId + "/";

    if (btn.classList.contains("in-collection")) {
        // Pede confirmação antes de remover
        openModal(
            "Remover esta edição da sua coleção?",
            async () => {
                const data = await postJSON(url, { confirm: true });
                if (data.status === "removed") {
                    card.dataset.inCollection = "false";
                    setCollectionState(btn, false);
                }
            }
        );
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
                }
            }
        );
    } else {
        postJSON(url).then(data => {
            if (data.status === "added") {
                card.dataset.isRead = "true";
                setReadState(btn, true);
            }
        });
    }
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

    // Fecha modal com ESC
    document.addEventListener("keydown", e => {
        if (e.key === "Escape") closeModal();
    });
});
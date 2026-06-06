// ── Burger menu ───────────────────────────────────────────────────────────────
const burgerBtn      = document.getElementById("burger-btn");
const sidebar        = document.getElementById("sidebar");
const sidebarOverlay = document.getElementById("sidebar-overlay");

function openSidebar() {
  sidebar.classList.add("open");
  sidebarOverlay.classList.add("visible");
  burgerBtn.classList.add("open");
}

function closeSidebar() {
  sidebar.classList.remove("open");
  sidebarOverlay.classList.remove("visible");
  burgerBtn.classList.remove("open");
}

if (burgerBtn) burgerBtn.addEventListener("click", () => {
  sidebar.classList.contains("open") ? closeSidebar() : openSidebar();
});

if (sidebarOverlay) sidebarOverlay.addEventListener("click", closeSidebar);

document.querySelectorAll(".nav-item").forEach(el => {
  el.addEventListener("click", () => {
    if (window.innerWidth <= 768) closeSidebar();
  });
});

// ── State & DOM refs ──────────────────────────────────────────────────────────
const browserId = localStorage.getItem("browserId") || (() => {
  const id = crypto.randomUUID();
  localStorage.setItem("browserId", id);
  return id;
})();

const embeddingCache = {};
const state = {
  likedEmbeddings: [],
  dislikedIds: new Set(),
  globalVector: null,
  likedIds: new Set(),
};

const $ = (id) => document.getElementById(id);

const input        = $("query-input");
const searchBtn    = $("search-btn");
const emptyState   = $("empty-state");
const loadingState = $("loading-state");
const resultsWrap  = $("results-wrap");
const resultsList  = $("results-list");
const resultsCount = $("results-count");
const resultsQuery = $("results-query");
const logoBtn      = document.getElementById("logo-btn");

// ── Navigation ────────────────────────────────────────────────────────────────
function goHome() {
  if (input) input.value = "";
  resultsWrap.classList.add("hidden");
  loadingState.classList.add("hidden");
  emptyState.classList.remove("hidden");
  document.querySelectorAll(".nav-item").forEach((n) => n.classList.remove("active"));
  document.querySelector(".main").scrollTo({ top: 0, behavior: "smooth" });
}

if (logoBtn) logoBtn.addEventListener("click", goHome);

// ── Helpers ───────────────────────────────────────────────────────────────────
function stripeClass(score) {
  if (score >= 80) return "stripe-high";
  if (score >= 60) return "stripe-mid";
  return "stripe-low";
}

function fillClass(score) {
  if (score >= 80) return "fill-high";
  if (score >= 60) return "fill-mid";
  return "fill-low";
}

function showEmpty() {
  emptyState.classList.remove("hidden");
  loadingState.classList.add("hidden");
  resultsWrap.classList.add("hidden");
}

function showLoading() {
  emptyState.classList.add("hidden");
  loadingState.classList.remove("hidden");
  resultsWrap.classList.add("hidden");
  resultsList.innerHTML = "";
}

function showResults() {
  emptyState.classList.add("hidden");
  loadingState.classList.add("hidden");
  resultsWrap.classList.remove("hidden");
}

function showError(message) {
  emptyState.classList.remove("hidden");
  loadingState.classList.add("hidden");
  resultsWrap.classList.add("hidden");

  const toast = document.getElementById("toast");
  toast.textContent = message;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 3000);
}

function averageVectors(vectors) {
  if (!vectors || vectors.length === 0) return null;
  const vLen = vectors[0].length;
  const avg = new Array(vLen).fill(0);
  for (const v of vectors) {
    for (let i = 0; i < vLen; i++) avg[i] += v[i];
  }
  return avg.map(val => val / vectors.length);
}

// ── Search ────────────────────────────────────────────────────────────────────
async function doSearch(query, displayQuery = null, categoryId = null) {
  if (!query?.trim() && !categoryId) return;

  const queryToShow = displayQuery || query;
  showLoading();

  try {
    const res = await fetch("/api/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query: query.trim(),
        category: categoryId,
        n_results: 5,
        disliked_ids: [...state.dislikedIds],
        session_centroid: state.likedEmbeddings.length > 0 ? averageVectors(state.likedEmbeddings) : null,
        global_centroid: state.globalVector,
      }),
    });

    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    data.query = queryToShow;
    renderResults(data);
  } catch (err) {
    showEmpty();
    console.error("Search error:", err);
  }
}

// ── Render ────────────────────────────────────────────────────────────────────
function renderResults(data) {
  if (data.results.length === 0) {
    if (data.message) {
      showError(data.message);
    } else {
      showEmpty();
    }
    return;
  }

  showResults();
  resultsCount.textContent = `Найдено ${data.results.length} серий по запросу`;
  resultsQuery.textContent = `«${data.query}»`;
  resultsList.innerHTML = "";

  data.results.forEach((ep, i) => {
    if (ep.embedding) embeddingCache[ep.id] = ep.embedding;
    const card = document.createElement("div");
    card.className = "card";
    card.style.animationDelay = `${i * 0.06}s`;
    card.innerHTML = buildCard(ep);
    resultsList.appendChild(card);
  });

  resultsList.querySelectorAll(".btn-action").forEach((btn) => {
    btn.addEventListener("click", () => handleFeedback(btn));
  });
}

function buildCard(ep) {
  const score      = ep.score;
  const stripe     = stripeClass(score);
  const fill       = fillClass(score);
  const showShort  = ep.show.includes("Как я встретил вашу маму") ? "Как я встретил вашу маму" : "Друзья";
  const likedCls   = state.likedIds.has(ep.id)    ? " liked"    : "";
  const dislikeCls = state.dislikedIds.has(ep.id) ? " disliked" : "";

  const tags = ep.mood_tags
    ? ep.mood_tags.split(",").map(t => t.trim()).filter(Boolean).slice(0, 4)
        .map(t => `<span class="tag">${t}</span>`).join("")
    : "";

  return `
    <div class="card-stripe ${stripe}"></div>
    <div class="card-inner">
      <div class="card-head">
        <span class="badge-show">${showShort}</span>
        <span class="badge-ep">Сезон ${ep.season} · Эпизод ${ep.episode}</span>
      </div>
      <div class="card-title">${ep.title}</div>
      <div class="card-desc">${ep.description}</div>
      <div class="match-bar">
        <div class="match-bar-label">
          <span>Семантическое совпадение</span>
          <span>${score}%</span>
        </div>
        <div class="match-bar-track">
          <div class="match-bar-fill ${fill}" style="width:${score}%"></div>
        </div>
      </div>
      <div class="card-tags">${tags}</div>
      <div class="card-foot">
        <span class="imdb"><span class="imdb-star">★</span> IMDb ${ep.imdb_rating.toFixed(1)}</span>
        <button class="btn-action${likedCls}"   data-id="${ep.id}" data-action="like">👍 Подходит</button>
        <button class="btn-action${dislikeCls}" data-id="${ep.id}" data-action="dislike">👎 Не то</button>
      </div>
    </div>
  `;
}

// ── Feedback ──────────────────────────────────────────────────────────────────
async function handleFeedback(btn) {
  const id        = btn.dataset.id;
  const action    = btn.dataset.action;
  const embedding = embeddingCache[id];

  btn.classList.add("pop");
  const card = btn.closest(".card");
  card.classList.add(action === "like" ? "flash-like" : "flash-dislike");

  if (action === "like") {
    state.likedIds.add(id);
    state.dislikedIds.delete(id);
    if (embedding) state.likedEmbeddings.push(embedding);
  } else {
    state.dislikedIds.add(id);
    state.likedIds.delete(id);
    state.likedEmbeddings = state.likedEmbeddings.filter((_, i) => i !== state.likedEmbeddings.length - 1);
  }

  const foot = btn.closest(".card-foot");
  foot.querySelectorAll(".btn-action").forEach(b => b.classList.remove("liked", "disliked"));
  btn.classList.add(action === "like" ? "liked" : "disliked");

  try {
    const res = await fetch("/api/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        episode_id: id,
        action,
        episode_embedding: embedding || [],
        browser_id: browserId,
        session_centroid: state.likedEmbeddings.length > 0 ? averageVectors(state.likedEmbeddings) : null,
        disliked_ids: [...state.dislikedIds],
      }),
    });
    if (res.ok) {
      const data = await res.json();
      if (data.global_vector) state.globalVector = data.global_vector;
    }
  } catch (_) {}
}

// ── Event listeners ───────────────────────────────────────────────────────────
if (searchBtn) searchBtn.addEventListener("click", () => doSearch(input.value));

if (input) {
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") { e.preventDefault(); doSearch(input.value); }
  });
}

document.querySelectorAll(".nav-item, .mood-card, .suggestion-item").forEach((el) => {
  el.addEventListener("click", () => {
    if (el.classList.contains("nav-item")) {
      document.querySelectorAll(".nav-item").forEach((n) => n.classList.remove("active"));
      el.classList.add("active");
    }

    if (el.dataset.category) {
      doSearch("", el.innerText.trim(), el.dataset.category);
    } else {
      const richQuery  = el.dataset.query;
      const prettyName = el.querySelector(".mood-title")?.innerText || richQuery;
      doSearch(richQuery, prettyName);
    }
  });
});
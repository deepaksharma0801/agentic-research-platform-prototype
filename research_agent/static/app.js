const form = document.querySelector("#query-form");
const queryInput = document.querySelector("#query-input");
const topKInput = document.querySelector("#top-k");
const statusMessage = document.querySelector("#status-message");
const embeddingProvider = document.querySelector("#embedding-provider");
const summaryProvider = document.querySelector("#summary-provider");
const resultCount = document.querySelector("#result-count");
const metricPapers = document.querySelector("#metric-papers");
const metricRelated = document.querySelector("#metric-related");
const metricDistance = document.querySelector("#metric-distance");
const summaryOutput = document.querySelector("#summary-output");
const papersBody = document.querySelector("#papers-body");
const relatedList = document.querySelector("#related-list");
const refreshStatsButton = document.querySelector("#refresh-stats");
const seedDemoButton = document.querySelector("#seed-demo");
const hydrateButton = document.querySelector("#hydrate-citations");

const statRecords = document.querySelector("#stat-records");
const statEmbedded = document.querySelector("#stat-embedded");
const statCoverage = document.querySelector("#stat-coverage");
const statGraph = document.querySelector("#stat-graph");
const statCitations = document.querySelector("#stat-citations");
const statYears = document.querySelector("#stat-years");
const categoryList = document.querySelector("#category-list");
const postgresStatus = document.querySelector("#postgres-status");
const pgvectorStatus = document.querySelector("#pgvector-status");
const neo4jStatus = document.querySelector("#neo4j-status");

function setStatus(message, isError = false) {
  statusMessage.textContent = message;
  statusMessage.classList.toggle("error", isError);
}

function text(value) {
  return value === null || value === undefined || value === "" ? "n.d." : String(value);
}

function compactId(openalexId) {
  return String(openalexId || "").replace("https://openalex.org/", "");
}

function truncate(value, maxLength) {
  const normalized = String(value || "").replace(/\s+/g, " ").trim();
  if (!normalized) return "No abstract available.";
  return normalized.length > maxLength ? `${normalized.slice(0, maxLength - 1)}...` : normalized;
}

function providerMarkup(label, value) {
  return `<span>${label}</span><strong>${value || "local"}</strong>`;
}

function formatNumber(value) {
  return new Intl.NumberFormat().format(value || 0);
}

function renderStats(payload) {
  const corpus = payload.corpus || {};
  const graph = payload.graph || {};
  const providers = payload.providers || {};
  const services = payload.services || {};
  const coverage = Math.round((corpus.embedding_coverage || 0) * 100);
  const yearRange = corpus.year_range || {};

  statRecords.textContent = formatNumber(corpus.papers);
  statEmbedded.textContent = formatNumber(corpus.embedded_papers);
  statCoverage.textContent = `${coverage}% vector coverage`;
  statGraph.textContent = formatNumber(graph.nodes);
  statCitations.textContent = `${formatNumber(graph.citations)} citation edges`;
  statYears.textContent =
    yearRange.min && yearRange.max ? `${yearRange.min}-${yearRange.max}` : "--";

  postgresStatus.textContent = services.postgres || "unknown";
  pgvectorStatus.textContent = services.pgvector || "unknown";
  neo4jStatus.textContent = services.neo4j || "unknown";
  embeddingProvider.innerHTML = providerMarkup("Embeddings", providers.embedding);
  summaryProvider.innerHTML = providerMarkup("Summary", providers.summary);

  renderCategories(corpus.categories || []);
}

function renderCategories(categories) {
  categoryList.replaceChildren();
  if (!categories.length) {
    const empty = document.createElement("div");
    empty.className = "empty";
    empty.textContent = "No corpus categories yet. Seed or ingest papers to populate this view.";
    categoryList.appendChild(empty);
    return;
  }

  const max = Math.max(...categories.map((category) => category.count), 1);
  for (const category of categories) {
    const row = document.createElement("div");
    const label = document.createElement("strong");
    const track = document.createElement("div");
    const fill = document.createElement("div");
    const count = document.createElement("span");

    row.className = "category-row";
    track.className = "bar-track";
    fill.className = "bar-fill";
    fill.style.width = `${Math.max(8, (category.count / max) * 100)}%`;
    label.textContent = category.name;
    count.textContent = formatNumber(category.count);

    track.appendChild(fill);
    row.append(label, track, count);
    categoryList.appendChild(row);
  }
}

function renderMetrics(payload) {
  const papers = payload.papers || [];
  const related = payload.related_papers || [];
  const bestDistance = papers
    .map((paper) => paper.distance)
    .filter((distance) => distance !== null && distance !== undefined)
    .sort((a, b) => a - b)[0];

  metricPapers.textContent = `${papers.length} retrieved`;
  metricRelated.textContent = `${related.length} related`;
  metricDistance.textContent =
    bestDistance === undefined ? "best distance --" : `best distance ${Number(bestDistance).toFixed(3)}`;
  resultCount.textContent = `${papers.length} papers`;
}

function renderPapers(papers) {
  papersBody.replaceChildren();
  if (!papers.length) {
    const empty = document.createElement("div");
    empty.className = "empty";
    empty.textContent = "No papers found.";
    papersBody.appendChild(empty);
    return;
  }

  papers.forEach((paper, index) => {
    const row = document.createElement("article");
    const rank = document.createElement("div");
    const body = document.createElement("div");
    const title = document.createElement("span");
    const meta = document.createElement("div");
    const id = document.createElement("div");
    const abstract = document.createElement("p");
    const distance = document.createElement("div");
    const distanceLabel = document.createElement("span");
    const distanceValue = document.createElement("strong");

    row.className = "paper-row";
    rank.className = "rank-badge";
    title.className = "paper-title";
    meta.className = "paper-meta";
    id.className = "paper-id";
    abstract.className = "paper-abstract";
    distance.className = "distance-block";

    rank.textContent = String(index + 1).padStart(2, "0");
    title.textContent = paper.title || "Untitled paper";
    meta.textContent = `${text(paper.year)} / ${(paper.authors || []).slice(0, 4).join(", ") || "Unknown authors"}`;
    id.textContent = compactId(paper.openalex_id);
    abstract.textContent = truncate(paper.abstract, 360);
    distanceLabel.textContent = "Distance";
    distanceValue.textContent =
      paper.distance === null || paper.distance === undefined
        ? "--"
        : Number(paper.distance).toFixed(4);

    body.append(title, meta, id, abstract);
    distance.append(distanceLabel, distanceValue);
    row.append(rank, body, distance);
    papersBody.appendChild(row);
  });
}

function renderRelated(papers) {
  relatedList.replaceChildren();
  if (!papers.length) {
    const empty = document.createElement("p");
    empty.className = "empty";
    empty.textContent = "No citation-related papers found.";
    relatedList.appendChild(empty);
    return;
  }

  for (const paper of papers.slice(0, 12)) {
    const item = document.createElement("div");
    const title = document.createElement("strong");
    const meta = document.createElement("span");

    item.className = "related-item";
    title.textContent = paper.title || paper.openalex_id || "Unknown paper";
    meta.textContent = `${text(paper.year)} / ${compactId(paper.openalex_id)}`;
    item.append(title, meta);
    relatedList.appendChild(item);
  }
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.detail || "Request failed.");
  }
  return payload;
}

async function loadStats() {
  setStatus("Loading database metrics...");
  try {
    const payload = await fetchJson("/stats");
    renderStats(payload);
    setStatus("Dashboard metrics loaded");
  } catch (error) {
    setStatus(error.message, true);
  }
}

async function runAction(button, label, url, body) {
  button.disabled = true;
  setStatus(label);
  try {
    await fetchJson(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    await loadStats();
  } catch (error) {
    setStatus(error.message, true);
  } finally {
    button.disabled = false;
  }
}

async function runQuery(event) {
  event.preventDefault();
  const button = form.querySelector("button");
  button.disabled = true;
  setStatus("Running semantic retrieval...");

  try {
    const payload = await fetchJson("/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query: queryInput.value,
        top_k: Number(topKInput.value),
      }),
    });

    embeddingProvider.innerHTML = providerMarkup("Embeddings", payload.providers.embedding);
    summaryProvider.innerHTML = providerMarkup("Summary", payload.providers.summary);
    summaryOutput.textContent = payload.summary || "No summary returned.";
    renderMetrics(payload);
    renderPapers(payload.papers || []);
    renderRelated(payload.related_papers || []);
    setStatus("Retrieval complete");
  } catch (error) {
    setStatus(error.message, true);
  } finally {
    button.disabled = false;
  }
}

form.addEventListener("submit", runQuery);
refreshStatsButton.addEventListener("click", loadStats);
seedDemoButton.addEventListener("click", () =>
  runAction(seedDemoButton, "Seeding demo corpus...", "/demo-seed", { limit_per_topic: 10 }),
);
hydrateButton.addEventListener("click", () =>
  runAction(hydrateButton, "Hydrating citation metadata...", "/hydrate-citations", { limit: 50 }),
);

loadStats();

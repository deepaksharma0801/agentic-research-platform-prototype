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
const metricMode = document.querySelector("#metric-mode");
const summaryOutput = document.querySelector("#summary-output");
const papersBody = document.querySelector("#papers-body");
const relatedList = document.querySelector("#related-list");

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
  return normalized.length > maxLength ? `${normalized.slice(0, maxLength - 1)}…` : normalized;
}

function providerMarkup(label, value) {
  return `<span>${label}</span><strong>${value || "local"}</strong>`;
}

function renderMetrics(payload) {
  const papers = payload.papers || [];
  const related = payload.related_papers || [];
  const bestDistance = papers
    .map((paper) => paper.distance)
    .filter((distance) => distance !== null && distance !== undefined)
    .sort((a, b) => a - b)[0];

  metricPapers.textContent = papers.length;
  metricRelated.textContent = related.length;
  metricDistance.textContent =
    bestDistance === undefined ? "—" : Number(bestDistance).toFixed(3);
  metricMode.textContent = payload.providers?.summary || "local";
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
    body.className = "paper-body";
    title.className = "paper-title";
    meta.className = "paper-meta";
    id.className = "paper-id";
    abstract.className = "paper-abstract";
    distance.className = "distance-block";

    rank.textContent = String(index + 1).padStart(2, "0");
    title.textContent = paper.title || "Untitled paper";
    meta.textContent = `${text(paper.year)} · ${(paper.authors || []).slice(0, 4).join(", ") || "Unknown authors"}`;
    id.textContent = compactId(paper.openalex_id);
    abstract.textContent = truncate(paper.abstract, 330);
    distanceLabel.textContent = "Distance";
    distanceValue.textContent =
      paper.distance === null || paper.distance === undefined
        ? "—"
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
    meta.textContent = `${text(paper.year)} · ${compactId(paper.openalex_id)}`;
    item.append(title, meta);
    relatedList.appendChild(item);
  }
}

async function runQuery(event) {
  event.preventDefault();
  const button = form.querySelector("button");
  button.disabled = true;
  setStatus("Running retrieval...");

  try {
    const response = await fetch("/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query: queryInput.value,
        top_k: Number(topKInput.value),
      }),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || "Query failed.");
    }

    embeddingProvider.innerHTML = providerMarkup("Embedding", payload.providers.embedding);
    summaryProvider.innerHTML = providerMarkup("Summary", payload.providers.summary);
    summaryOutput.textContent = payload.summary || "No summary returned.";
    renderMetrics(payload);
    renderPapers(payload.papers || []);
    renderRelated(payload.related_papers || []);
    setStatus("Ready");
  } catch (error) {
    setStatus(error.message, true);
  } finally {
    button.disabled = false;
  }
}

form.addEventListener("submit", runQuery);

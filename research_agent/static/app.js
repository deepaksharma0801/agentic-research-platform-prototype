const form = document.querySelector("#query-form");
const queryInput = document.querySelector("#query-input");
const topKInput = document.querySelector("#top-k");
const statusMessage = document.querySelector("#status-message");
const embeddingProvider = document.querySelector("#embedding-provider");
const summaryProvider = document.querySelector("#summary-provider");
const resultCount = document.querySelector("#result-count");
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

function renderPapers(papers) {
  papersBody.replaceChildren();
  if (!papers.length) {
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = 4;
    cell.className = "empty";
    cell.textContent = "No papers found.";
    row.appendChild(cell);
    papersBody.appendChild(row);
    return;
  }

  for (const paper of papers) {
    const row = document.createElement("tr");
    const year = document.createElement("td");
    const title = document.createElement("td");
    const authors = document.createElement("td");
    const distance = document.createElement("td");
    const titleText = document.createElement("span");
    const idText = document.createElement("span");

    titleText.className = "paper-title";
    titleText.textContent = paper.title || "Untitled paper";
    idText.className = "paper-id";
    idText.textContent = compactId(paper.openalex_id);

    year.textContent = text(paper.year);
    title.append(titleText, idText);
    authors.textContent = (paper.authors || []).slice(0, 3).join(", ") || "Unknown";
    distance.textContent =
      paper.distance === null || paper.distance === undefined
        ? ""
        : Number(paper.distance).toFixed(4);

    row.append(year, title, authors, distance);
    papersBody.appendChild(row);
  }
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
  setStatus("Searching...");

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

    embeddingProvider.textContent = `embedding: ${payload.providers.embedding}`;
    summaryProvider.textContent = `summary: ${payload.providers.summary}`;
    resultCount.textContent = `papers: ${payload.counts.papers}`;
    summaryOutput.textContent = payload.summary || "No summary returned.";
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

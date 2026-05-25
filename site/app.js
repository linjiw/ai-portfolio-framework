const data = window.AI_FRAMEWORK_DATA;

const escapeHtml = (value) =>
  String(value ?? "").replace(
    /[&<>"']/g,
    (char) =>
      ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
      })[char]
  );

const safeUrl = (value) => {
  try {
    const url = new URL(String(value ?? ""), window.location.href);
    if (["http:", "https:"].includes(url.protocol)) {
      return url.href;
    }
  } catch {
    return "about:blank";
  }
  return "about:blank";
};

const sourceLink = (id) => {
  const source = data.sources[id];
  if (!source) return "";
  return `<a class="source-pill" href="${safeUrl(source.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(source.label)}</a>`;
};

const severityClass = (value) =>
  String(value ?? "")
    .toLowerCase()
    .replace(/\s+/g, "-")
    .replace(/[^a-z0-9_-]/g, "");

const formatUsd = (value) =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2
  }).format(Number(value ?? 0));

const formatPct = (value) => `${Number(value ?? 0).toFixed(2)}%`;

const signedClass = (value) => (Number(value ?? 0) >= 0 ? "positive" : "negative");

function init() {
  document.getElementById("asOf").textContent = `Data ${data.dataDate} | Reviewed ${data.reviewDate}`;
  document.getElementById("summaryText").textContent = data.summary;
  document.getElementById("holdingCount").textContent = data.holdings.length;
  setupTabs();
  setupFilters();
  renderPortfolio("All");
  renderDecisionProcess();
  renderControlRights();
  renderSignals();
  renderWatchlist();
  renderResearch();
  renderSources();
  renderClaims();
  loadPortfolioPerformance();
  loadCurrentPositions();
  loadResearchMonitor();
  loadFibMomentum();
}

function setupTabs() {
  const tabs = Array.from(document.querySelectorAll(".tab"));
  tabs.forEach((button, index) => {
    button.addEventListener("click", () => activateTab(button));
    button.addEventListener("keydown", (event) => {
      const keyToIndex = {
        ArrowLeft: index === 0 ? tabs.length - 1 : index - 1,
        ArrowRight: index === tabs.length - 1 ? 0 : index + 1,
        Home: 0,
        End: tabs.length - 1
      };
      if (!(event.key in keyToIndex)) return;
      event.preventDefault();
      const nextTab = tabs[keyToIndex[event.key]];
      nextTab.focus();
      activateTab(nextTab);
    });
  });
}

function activateTab(activeButton) {
  document.querySelectorAll(".tab").forEach((tab) => {
    const isActive = tab === activeButton;
    tab.classList.toggle("active", isActive);
    tab.setAttribute("aria-selected", String(isActive));
    tab.tabIndex = isActive ? 0 : -1;
  });
  document.querySelectorAll(".view").forEach((view) => {
    const isActive = view.id === `view-${activeButton.dataset.view}`;
    view.classList.toggle("active", isActive);
    view.hidden = !isActive;
  });
}

function setupFilters() {
  const select = document.getElementById("layerFilter");
  const layers = Array.from(new Set(data.holdings.flatMap((holding) => holding.layers))).sort();
  layers.forEach((layer) => {
    const option = document.createElement("option");
    option.value = layer;
    option.textContent = layer;
    select.appendChild(option);
  });
  select.addEventListener("change", () => renderPortfolio(select.value));
}

function renderPortfolio(layer) {
  const grid = document.getElementById("holdingsGrid");
  const holdings = data.holdings.filter(
    (holding) => layer === "All" || holding.layers.includes(layer)
  );
  grid.innerHTML = holdings.map(renderHoldingCard).join("");
}

function renderHoldingCard(holding) {
  const evidence = holding.evidence.map(renderEvidenceItem).join("");
  const risks = holding.risks.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
  const chips = holding.layers
    .map((layer) => `<span class="chip">${escapeHtml(layer)}</span>`)
    .join("");
  const sources = holding.sources.map(sourceLink).join("");
  return `
    <article class="holding-card">
      <div class="card-head">
        <div>
          <div class="ticker">${escapeHtml(holding.ticker)}</div>
          <div class="name">${escapeHtml(holding.name)}</div>
        </div>
        <div class="weight">${escapeHtml(holding.weight)}%</div>
      </div>
      <div class="bucket">${escapeHtml(holding.bucket)} | Conviction ${escapeHtml(holding.conviction)}</div>
      <div class="chips">${chips}</div>
      <div class="meta-row">
        <span>Confidence: ${escapeHtml(holding.confidence)}</span>
        <span>Reviewed: ${escapeHtml(holding.last_reviewed_at)}</span>
        <span>Next: ${escapeHtml(holding.next_review_due)}</span>
      </div>
      <p class="thesis">${escapeHtml(holding.thesis)}</p>
      <div>
        <div class="card-section-title">Evidence</div>
        <ul>${evidence}</ul>
      </div>
      <div>
        <div class="card-section-title">Risks</div>
        <ul class="risk-list">${risks}</ul>
      </div>
      <div>
        <div class="card-section-title">Watch</div>
        <p class="muted">${escapeHtml(holding.watch)}</p>
      </div>
      <div>
        <div class="card-section-title">Falsifier</div>
        <p class="muted">${escapeHtml(holding.falsifier)}</p>
      </div>
      <div class="source-links">${sources}</div>
    </article>
  `;
}

function renderEvidenceItem(item) {
  if (typeof item === "string") {
    return `<li>${escapeHtml(item)}</li>`;
  }
  const tags = [
    item.id ? `ID ${item.id}` : "",
    item.materiality ? `Materiality ${item.materiality}` : "",
    (item.claim_ids || []).length ? `Claims ${(item.claim_ids || []).join(", ")}` : "",
    (item.metric_ids || []).length ? `Metrics ${(item.metric_ids || []).join(", ")}` : ""
  ].filter(Boolean);
  return `
    <li>
      ${escapeHtml(item.text || "")}
      <span class="evidence-meta">${escapeHtml(tags.join(" | "))}</span>
    </li>
  `;
}

function renderDecisionProcess() {
  const process = data.decisionProcess || {};
  const overview = document.getElementById("decisionOverview");
  overview.innerHTML = `
    <p class="section-label">Decision thesis</p>
    <p class="decision-thesis">${escapeHtml(process.thesis || data.summary)}</p>
    <div class="decision-rules">
      ${(process.rules || [])
        .map((rule, index) => `<div><strong>${index + 1}</strong><span>${escapeHtml(rule)}</span></div>`)
        .join("")}
    </div>
  `;

  document.getElementById("decisionGrid").innerHTML = (process.choiceRationale || [])
    .map(
      (item) => `
        <article class="decision-card">
          <div class="card-head">
            <h3>${escapeHtml(item.label)}</h3>
            <div class="weight">${escapeHtml(item.weight)}</div>
          </div>
          <p>${escapeHtml(item.text)}</p>
        </article>
      `
    )
    .join("");

  document.getElementById("decisionGateGrid").innerHTML = (process.gates || [])
    .map(
      (gate) => `
        <article class="decision-card">
          <p class="section-label">${escapeHtml(gate.label)}</p>
          <p>${escapeHtml(gate.text)}</p>
        </article>
      `
    )
    .join("");
}

function renderControlRights() {
  const bars = document.getElementById("exposureBars");
  const maxValue = Math.max(...data.exposures.map((item) => item.value));
  bars.innerHTML = data.exposures
    .map((item) => {
      const width = Math.max(0, Math.min(100, Math.round((item.value / maxValue) * 100)));
      return `
        <div class="bar-row">
          <div class="bar-label">${escapeHtml(item.layer)}</div>
          <div class="bar-track"><div class="bar-fill" style="width:${width}%"></div></div>
          <div class="bar-value">${escapeHtml(item.value)}%</div>
          <div class="bar-note">${escapeHtml(item.holdings)}</div>
        </div>
      `;
    })
    .join("");

  document.getElementById("allocationGrid").innerHTML = data.allocation
    .map(
      (item) => `
        <div class="mini-card">
          <p class="section-label">${escapeHtml(item.label)}</p>
          <strong>${escapeHtml(item.value)}%</strong>
        </div>
      `
    )
    .join("");
}

function renderSignals() {
  document.getElementById("signalGrid").innerHTML = data.signals
    .map((signal) => {
      const sources = (signal.sources || []).map(sourceLink).join("");
      return `
        <article class="signal-card">
          <span class="severity ${severityClass(signal.severity)}">${escapeHtml(signal.severity)}</span>
          <h3>${escapeHtml(signal.target)}</h3>
          <p><strong>${escapeHtml(signal.type)}</strong></p>
          <p>${escapeHtml(signal.text)}</p>
          <div class="meta-row">
            <span>Observed: ${escapeHtml(signal.observed_value)}</span>
            <span>Value: ${escapeHtml(signal.current_value)} ${escapeHtml(signal.unit)}</span>
            <span>Threshold: ${escapeHtml(signal.threshold)}</span>
            <span>Confidence: ${escapeHtml(signal.confidence)}</span>
            <span>Next: ${escapeHtml(signal.next_review_due)}</span>
          </div>
          <p>Status rule: ${escapeHtml(signal.status_rule)}</p>
          <p>Action: ${escapeHtml(signal.action)}</p>
          <div class="source-links">${sources}</div>
        </article>
      `;
    })
    .join("");

  document.getElementById("questionGrid").innerHTML = data.monitoringQuestions
    .map((question) => {
      const sources = (question.sources || []).map(sourceLink).join("");
      return `
        <article class="question-card">
          <span class="severity ${severityClass(question.status)}">${escapeHtml(question.status)}</span>
          <h3>${escapeHtml(question.label)}</h3>
          <p>${escapeHtml(question.question)}</p>
          <div class="meta-row">
            <span>Observed: ${escapeHtml(question.observed_value)}</span>
            <span>Value: ${escapeHtml(question.current_value)} ${escapeHtml(question.unit)}</span>
            <span>Threshold: ${escapeHtml(question.threshold)}</span>
            <span>Confidence: ${escapeHtml(question.confidence)}</span>
            <span>Next: ${escapeHtml(question.next_review_due)}</span>
          </div>
          <p>Status rule: ${escapeHtml(question.status_rule)}</p>
          <p>${escapeHtml(question.trigger)}</p>
          <div class="source-links">${sources}</div>
        </article>
      `;
    })
    .join("");
}

function renderWatchlist() {
  const watchlist = data.watchlist || {};
  const summary = document.getElementById("watchlistSummary");
  const grid = document.getElementById("watchlistGrid");
  const comparison = document.getElementById("watchlistComparison");
  if (!summary || !grid || !comparison) return;

  const items = watchlist.items || [];
  if (!items.length) {
    summary.innerHTML = `<div class="empty-monitor">No watchlist entries configured yet.</div>`;
    grid.innerHTML = "";
    comparison.innerHTML = "";
    return;
  }

  summary.innerHTML = `
    <div>
      <p class="section-label">${escapeHtml(watchlist.stage || "Watchlist")}</p>
      <h3>${escapeHtml(watchlist.objective || "Research candidates")}</h3>
      <p>${escapeHtml(watchlist.policy || "")}</p>
      <p class="watchlist-boundary">${escapeHtml(watchlist.boundaryNote || "")}</p>
    </div>
    <div class="watchlist-kpis">
      <div>
        <span>Names tracked</span>
        <strong>${escapeHtml(items.length)}</strong>
      </div>
      <div>
        <span>Non-holding candidates</span>
        <strong>${escapeHtml(items.filter((item) => item.status === "watchlist_not_position").length)}</strong>
      </div>
      <div>
        <span>Portfolio holdings</span>
        <strong>${escapeHtml(items.filter((item) => item.status === "portfolio_holding_watch").length)}</strong>
      </div>
      <div>
        <span>Action boundary</span>
        <strong>${escapeHtml(watchlist.boundary || "review")}</strong>
      </div>
    </div>
  `;

  grid.innerHTML = items.map(renderWatchlistCard).join("");
  comparison.innerHTML = (watchlist.comparisonGates || [])
    .map(
      (gate) => `
        <article class="comparison-card gate-card">
          <div class="card-head">
            <p class="section-label">${escapeHtml(gate.id)}</p>
            <span class="severity ${severityClass(gate.reviewState)}">${escapeHtml(gate.reviewState)}</span>
          </div>
          <h3>${escapeHtml(gate.question)}</h3>
          <div class="meta-row">
            <span>Evidence: ${escapeHtml(gate.requiredEvidenceType)}</span>
            <span>Action: ${escapeHtml(gate.action)}</span>
          </div>
          <p>${escapeHtml(gate.currentRead)}</p>
          <p class="muted">Review trigger: ${escapeHtml(gate.reviewTrigger)}</p>
        </article>
      `
    )
    .join("");
}

function renderWatchlistCard(item) {
  const sources = (item.source_ids || []).map(sourceLink).join("");
  const signalRows = (item.keySignals || [])
    .map(
      (signal) => `
        <div>
          <span>${escapeHtml(signal.label)}</span>
          <strong>${escapeHtml(signal.value)}</strong>
          <p>${escapeHtml(signal.interpretation)}</p>
        </div>
      `
    )
    .join("");
  const metrics = (item.watchMetrics || [])
    .map(
      (metric) => `
        <li>
          <strong>${escapeHtml(metric.label)}</strong>
          <span>${escapeHtml(metric.state)} | ${escapeHtml(metric.cadence)}</span>
          <p>${escapeHtml(metric.trigger)}</p>
        </li>
      `
    )
    .join("");
  const evidenceNeeded = (item.evidenceNeeded || [])
    .map((entry) => `<li>${escapeHtml(entry)}</li>`)
    .join("");
  const bearCase = (item.bearCase || [])
    .map((entry) => `<li>${escapeHtml(entry)}</li>`)
    .join("");
  const process = (item.decisionProcess || [])
    .map(
      (step) => `
        <li>
          <strong>${escapeHtml(step.step)}</strong>
          <span>${escapeHtml(step.text)}</span>
        </li>
      `
    )
    .join("");
  const promotionGate = item.promotionGate || {};
  const requiredEvidence = (promotionGate.requiredEvidence || [])
    .map((entry) => `<li>${escapeHtml(entry)}</li>`)
    .join("");
  const disallowedTriggers = (
    promotionGate.disallowedTriggers ||
    promotionGate.reviewTriggers ||
    []
  )
    .map((entry) => `<li>${escapeHtml(entry)}</li>`)
    .join("");
  const outcomes = (promotionGate.possibleOutcomes || [])
    .map((entry) => `<span>${escapeHtml(entry)}</span>`)
    .join("");
  return `
    <article class="watchlist-card">
      <div class="card-head">
        <div>
          <div class="ticker">${escapeHtml(item.ticker)}</div>
          <div class="name">${escapeHtml(item.name)}</div>
        </div>
        <span class="severity ${severityClass(item.status)}">${escapeHtml(item.statusLabel || item.status)}</span>
      </div>
      <div class="bucket">${escapeHtml(item.role)} | Priority ${escapeHtml(item.priority)}</div>
      <div class="meta-row">
        <span>Relationship: ${escapeHtml(item.relationship)}</span>
        <span>Review: ${escapeHtml(item.nextReviewDue)}</span>
        <span>Boundary: ${escapeHtml(item.decisionBoundary)}</span>
        <span>Action: ${escapeHtml(item.actionBoundary)}</span>
      </div>
      <p class="thesis">${escapeHtml(item.coreQuestion)}</p>
      <p>${escapeHtml(item.thesisToTest)}</p>
      <div class="watchlist-signal-grid">${signalRows}</div>
      <div class="watchlist-section">
        <div class="card-section-title">Watch metrics</div>
        <ul class="watchlist-list">${metrics}</ul>
      </div>
      <div class="watchlist-section">
        <div class="card-section-title">Evidence needed</div>
        <ul>${evidenceNeeded}</ul>
      </div>
      <div class="watchlist-section">
        <div class="card-section-title">Bear case</div>
        <ul>${bearCase}</ul>
      </div>
      <div class="watchlist-section">
        <div class="card-section-title">Falsifier</div>
        <p class="muted">${escapeHtml(item.falsifier)}</p>
      </div>
      <div class="watchlist-section">
        <div class="card-section-title">Next action</div>
        <p>${escapeHtml(item.nextAction?.question || "")}</p>
        <p class="muted">${escapeHtml(item.nextAction?.successCondition || "")}</p>
      </div>
      <div class="watchlist-section promotion-gate">
        <div class="card-section-title">Promotion / replacement gate</div>
        <p class="muted">Decision log required: ${
          promotionGate.requiresDecisionLog ? "yes" : "not configured"
        }</p>
        <div class="gate-columns">
          <div>
            <strong>Required evidence</strong>
            <ul>${requiredEvidence}</ul>
          </div>
          <div>
            <strong>${promotionGate.disallowedTriggers ? "Disallowed triggers" : "Review triggers"}</strong>
            <ul>${disallowedTriggers}</ul>
          </div>
        </div>
        <div class="gate-outcomes">${outcomes}</div>
      </div>
      <div class="watchlist-section">
        <div class="card-section-title">Decision process</div>
        <ol class="decision-step-list">${process}</ol>
      </div>
      <div class="source-links">${sources}</div>
    </article>
  `;
}

async function loadCurrentPositions() {
  try {
    const response = await fetch("./current-positions-data.json", { cache: "no-store" });
    if (!response.ok) {
      renderCurrentPositionsMissing();
      return;
    }
    renderCurrentPositions(await response.json());
  } catch {
    renderCurrentPositionsMissing();
  }
}

function renderCurrentPositionsMissing() {
  const status = document.getElementById("currentPositionsStatus");
  if (!status) return;
  status.className = "current-status muted";
  status.innerHTML = `
    No sanitized current-position file is present. Run
    <code>uv run python -m scripts.build_current_positions</code>
    to refresh from the public sanitized seed, or import a new brokerage CSV with
    <code>uv run python -m scripts.build_current_positions --input /path/to/Portfolio_Positions.csv --write-seed</code>.
  `;
  document.getElementById("currentPositionsKpis").hidden = true;
  document.getElementById("currentPositionsClassifications").innerHTML =
    `<div class="empty-monitor">Current-position analysis is missing from this Pages artifact.</div>`;
  document.getElementById("currentPositionsReviewQueue").innerHTML =
    `<div class="empty-monitor">No sanitized current-position data loaded.</div>`;
  document.getElementById("currentPositionsDerivative").innerHTML =
    `<div class="empty-monitor">No derivative overlay loaded.</div>`;
  document.getElementById("currentPositionsTableWrap").hidden = true;
}

function renderCurrentPositions(payload) {
  const summary = payload.summary || {};
  const privacy = payload.privacy || {};
  const status = document.getElementById("currentPositionsStatus");
  status.className = "current-status ready";
  status.textContent = `Generated ${escapeHtml(payload.generatedAtUtc)} from ${
    escapeHtml(payload.sourceFile)
  }. Downloaded ${escapeHtml(payload.downloadedAt || "unknown")}. Account identifiers included: ${
    privacy.accountIdentifiersIncluded ? "yes" : "no"
  }.`;

  renderCurrentPositionKpis(summary);
  renderCurrentClassifications(payload.classifications || []);
  renderCurrentReviewQueue(payload.reviewQueue || []);
  renderCurrentDerivativeOverlay(payload.derivativeOverlay || {});
  renderCurrentPositionRows(payload.positions || []);
}

function renderCurrentPositionKpis(summary) {
  const kpis = document.getElementById("currentPositionsKpis");
  kpis.hidden = false;
  kpis.innerHTML = [
    ["Total value", formatUsd(summary.totalValueUsd), ""],
    ["Gross exposure", formatPct(summary.grossExposurePct), ""],
    ["Framework mapped", formatPct(summary.frameworkMappedWeightPct), ""],
    ["Watchlist", formatPct(summary.watchlistWeightPct), "yellow"],
    ["Index overlay", formatPct(summary.indexOverlayWeightPct), "yellow"],
    ["Outside framework", formatPct(summary.outsideFrameworkWeightPct), "yellow"],
    ["Cash", formatPct(summary.cashWeightPct), ""],
    ["Options net", formatUsd(summary.optionNetUsd), signedClass(summary.optionNetUsd)]
  ]
    .map(
      ([label, value, tone]) => `
        <div class="current-kpi">
          <span>${escapeHtml(label)}</span>
          <strong class="${escapeHtml(tone)}">${escapeHtml(value)}</strong>
        </div>
      `
    )
    .join("");
}

function renderCurrentClassifications(classifications) {
  const grid = document.getElementById("currentPositionsClassifications");
  if (!classifications.length) {
    grid.innerHTML = `<div class="empty-monitor">No position classifications generated.</div>`;
    return;
  }
  grid.innerHTML = classifications
    .map(
      (item) => `
        <article class="current-classification-card">
          <div class="card-head">
            <div>
              <p class="section-label">${escapeHtml(item.count)} rows</p>
              <h3>${escapeHtml(item.label)}</h3>
            </div>
            <span class="severity ${severityClass(item.status)}">${escapeHtml(item.status)}</span>
          </div>
          <strong>${formatUsd(item.valueUsd)}</strong>
          <p>${formatPct(item.weightPct)} of net account value.</p>
        </article>
      `
    )
    .join("");
}

function renderCurrentReviewQueue(queue) {
  const grid = document.getElementById("currentPositionsReviewQueue");
  if (!queue.length) {
    grid.innerHTML = `<div class="empty-monitor">No current-position review prompts generated.</div>`;
    return;
  }
  grid.innerHTML = queue
    .map(
      (item) => `
        <article class="current-review-card">
          <div class="card-head">
            <p class="section-label">${escapeHtml(item.topic)}</p>
            <span class="severity ${severityClass(item.priority)}">${escapeHtml(item.priority)}</span>
          </div>
          <h3>${escapeHtml(item.topic)}</h3>
          <p>${escapeHtml(item.question)}</p>
          ${
            (item.symbols || []).length
              ? `<p class="muted">Symbols: ${escapeHtml(item.symbols.join(", "))}</p>`
              : ""
          }
          <p class="muted">Boundary: ${escapeHtml(item.actionBoundary)}</p>
        </article>
      `
    )
    .join("");
}

function renderCurrentDerivativeOverlay(overlay) {
  const panel = document.getElementById("currentPositionsDerivative");
  const rows = overlay.netValueByUnderlying || [];
  const notes = overlay.notes || [];
  if (!rows.length) {
    panel.innerHTML = `<div class="empty-monitor">No option positions found in the imported file.</div>`;
    return;
  }
  panel.innerHTML = `
    <div class="current-derivative-grid">
      ${rows
        .map(
          (row) => `
            <div>
              <span>${escapeHtml(row.underlying)}</span>
              <strong class="${signedClass(row.netValueUsd)}">${formatUsd(row.netValueUsd)}</strong>
            </div>
          `
        )
        .join("")}
    </div>
    <ul class="current-note-list">
      ${notes.map((note) => `<li>${escapeHtml(note)}</li>`).join("")}
    </ul>
  `;
}

function renderCurrentPositionRows(positions) {
  document.getElementById("currentPositionsTableWrap").hidden = false;
  document.getElementById("currentPositionsRows").innerHTML = positions
    .map(
      (position) => `
        <tr>
          <td>
            <strong>${escapeHtml(position.displaySymbol || position.symbol)}</strong>
            <span>${escapeHtml(position.description)}</span>
          </td>
          <td>
            <span class="severity ${severityClass(position.frameworkStatus)}">${escapeHtml(
              position.frameworkStatus
            )}</span>
            <span>${escapeHtml(position.decisionRead)}</span>
          </td>
          <td>
            ${formatPct(position.currentWeightPct)}
            ${
              position.targetWeightPct === null || position.targetWeightPct === undefined
                ? `<span>Target: n/a</span>`
                : `<span>Target: ${formatPct(position.targetWeightPct)}</span>`
            }
          </td>
          <td class="${signedClass(position.currentValueUsd)}">${formatUsd(position.currentValueUsd)}</td>
          <td class="${signedClass(position.totalGainLossUsd)}">${formatUsd(position.totalGainLossUsd)}</td>
          <td>
            <span class="severity ${severityClass(position.ruleState)}">${escapeHtml(position.ruleState)}</span>
            <span>${escapeHtml(position.reviewReason)}</span>
          </td>
        </tr>
      `
    )
    .join("");
}

function renderResearch() {
  document.getElementById("researchList").innerHTML = data.holdings
    .map(
      (holding) => `
        <section class="research-row">
          <div>
            <div class="ticker">${escapeHtml(holding.ticker)}</div>
            <div class="name">${escapeHtml(holding.name)}</div>
            <div class="weight">${escapeHtml(holding.weight)}%</div>
          </div>
          <div>
            <h3>${escapeHtml(holding.bucket)}</h3>
            <p>${escapeHtml(holding.thesis)}</p>
            <p class="muted">Watch: ${escapeHtml(holding.watch)}</p>
            <p class="muted">Falsifier: ${escapeHtml(holding.falsifier)}</p>
          </div>
        </section>
      `
    )
    .join("");
}

function renderSources() {
  document.getElementById("sourceList").innerHTML = Object.entries(data.sources)
    .map(
      ([id, source]) => `
        <article class="source-card">
          <p class="section-label">${escapeHtml(id)}</p>
          <h3><a href="${safeUrl(source.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(source.label)}</a></h3>
          <p>${escapeHtml(source.url)}</p>
        </article>
      `
    )
    .join("");
}

function renderClaims() {
  document.getElementById("claimList").innerHTML = (data.claims || [])
    .map((claim) => {
      const source = data.sources[claim.source_id];
      const sourceLabel = source ? source.label : claim.source_id;
      const sourceUrl = source ? source.url : "";
      return `
        <article class="claim-card">
          <p class="section-label">${escapeHtml(claim.entity)} | ${escapeHtml(claim.claim_id)}</p>
          <h3>${escapeHtml(claim.claim)}</h3>
          <div class="meta-row">
            <span>Type: ${escapeHtml(claim.evidence_type)}</span>
            <span>Metric: ${escapeHtml(claim.metric)}</span>
            <span>Confidence: ${escapeHtml(claim.confidence)}</span>
            <span>Retrieved: ${escapeHtml(claim.retrieved_at)}</span>
          </div>
          <p>${escapeHtml(claim.quote_or_excerpt)}</p>
          <a class="source-pill" href="${safeUrl(sourceUrl)}" target="_blank" rel="noopener noreferrer">${escapeHtml(sourceLabel)}</a>
        </article>
      `;
    })
    .join("");
}

async function loadPortfolioPerformance() {
  try {
    const response = await fetch("./portfolio-data.json", { cache: "no-store" });
    if (!response.ok) {
      renderPortfolioPerformanceMissing();
      return;
    }
    const portfolio = await response.json();
    renderPortfolioPerformance(portfolio);
  } catch {
    renderPortfolioPerformanceMissing();
  }
}

function renderPortfolioPerformanceMissing() {
  const status = document.getElementById("portfolioPerformanceStatus");
  status.className = "portfolio-status muted";
  status.textContent =
    "No portfolio ledger found yet. The daily GitHub workflow generates this $1,000 tracker from the versioned lot seed.";
}

async function loadResearchMonitor() {
  try {
    const response = await fetch("./research-monitor-data.json", { cache: "no-store" });
    if (!response.ok) {
      renderResearchMonitorMissing();
      return;
    }
    const monitor = await response.json();
    renderResearchMonitor(monitor);
  } catch {
    renderResearchMonitorMissing();
  }
}

function renderResearchMonitorMissing() {
  const status = document.getElementById("monitorStatus");
  status.className = "monitor-status muted";
  status.textContent =
    "No research monitor data found yet. Run the portfolio refresh to generate deterministic alerts and source health.";
}

async function loadFibMomentum() {
  try {
    const response = await fetch("./fib-momentum-data.json", { cache: "no-store" });
    if (!response.ok) {
      renderFibMomentumMissing();
      return;
    }
    renderFibMomentum(await response.json());
  } catch {
    renderFibMomentumMissing();
  }
}

function renderFibMomentumMissing() {
  const status = document.getElementById("fibMomentumStatus");
  if (!status) return;
  status.className = "fib-status muted";
  status.innerHTML = `
    No Fibonacci EMA monitor data found yet. Run
    <code>uv run python -m scripts.build_fib_momentum</code>
    after refreshing the portfolio or importing current positions.
  `;
  document.getElementById("fibMomentumKpis").hidden = true;
  document.getElementById("fibMomentumTableWrap").hidden = true;
}

function renderFibMomentum(payload) {
  const status = document.getElementById("fibMomentumStatus");
  const summary = payload.summary || {};
  const framework = payload.framework || {};
  status.className = "fib-status ready";
  status.textContent = `Generated ${escapeHtml(payload.generatedAtUtc)} for ${
    escapeHtml(payload.period || "1y")
  } / ${escapeHtml(payload.interval || "1d")}. Boundary: ${
    escapeHtml(framework.actionBoundary || "review_only")
  }.`;

  renderFibMomentumKpis(summary);
  renderFibMomentumRows(payload.rows || []);
}

function renderFibMomentumKpis(summary) {
  const kpis = document.getElementById("fibMomentumKpis");
  const counts = summary.signalCounts || {};
  const bullish = Number(counts.strong_bullish || 0) + Number(counts.bullish || 0);
  const bearish = Number(counts.strong_bearish || 0) + Number(counts.bearish || 0);
  kpis.hidden = false;
  kpis.innerHTML = [
    ["Scanned", summary.scannedCount ?? 0, ""],
    ["Avg score", formatScore(summary.averageComposite), ""],
    ["Bullish review", bullish, "green"],
    ["Neutral", counts.neutral || 0, "gray"],
    ["Risk review", bearish, "yellow"],
    ["Top setup", summary.topTicker || "n/a", signalTone("strong_bullish")],
    ["Weakest", summary.weakestTicker || "n/a", signalTone("bearish")],
    ["Failures", summary.failureCount || 0, Number(summary.failureCount || 0) ? "yellow" : ""]
  ]
    .map(
      ([label, value, tone]) => `
        <div class="fib-kpi">
          <span>${escapeHtml(label)}</span>
          <strong class="${escapeHtml(tone)}">${escapeHtml(value)}</strong>
        </div>
      `
    )
    .join("");
}

function renderFibMomentumRows(rows) {
  const wrap = document.getElementById("fibMomentumTableWrap");
  const body = document.getElementById("fibMomentumRows");
  if (!rows.length) {
    wrap.hidden = true;
    body.innerHTML = "";
    return;
  }
  wrap.hidden = false;
  body.innerHTML = rows
    .map((row) => {
      const metrics = row.metrics || {};
      const notes = (row.notes || []).slice(0, 2).join(" ");
      return `
        <tr>
          <td>
            <strong>${escapeHtml(row.ticker)}</strong>
            <span>${escapeHtml(row.name || "")}</span>
            <span>${escapeHtml(row.sourceLabel || "")} | ${escapeHtml(row.date || "")}</span>
          </td>
          <td>
            <span class="severity ${signalTone(row.signal)}">${escapeHtml(row.signalLabel)}</span>
            <span>${escapeHtml(row.actionBoundary)}</span>
          </td>
          <td>
            <strong>${formatScore(row.compositeScore)}</strong>
            <span>Close ${formatMaybe(row.close, "", 2)}</span>
          </td>
          <td>
            ${formatScore(row.trendScore)}
            <span>Stack: ${escapeHtml(metrics.emaStack || "n/a")}</span>
            <span>EMA21 slope: ${formatMaybe(metrics.ema21SlopePct, "%")}</span>
          </td>
          <td>
            ${formatScore(row.momentumScore)}
            <span>MACD hist: ${formatMaybe(metrics.macdHist, "", 2)}</span>
            <span>RSI13: ${formatMaybe(metrics.rsi13, "", 1)}</span>
          </td>
          <td>
            ${formatScore(row.volatilityScore)} / ${formatScore(row.volumeScore)}
            <span>BB pct: ${formatMaybe(metrics.bbWidthPct, "%", 0)}</span>
            <span>Rel vol: ${formatMaybe(metrics.relVolume, "x", 1)}</span>
          </td>
          <td>${escapeHtml(notes)}</td>
        </tr>
      `;
    })
    .join("");
}

function signalTone(signal) {
  if (signal === "strong_bullish" || signal === "bullish") return "green";
  if (signal === "neutral") return "gray";
  if (signal === "strong_bearish") return "red";
  return "yellow";
}

function formatScore(value) {
  if (value === null || value === undefined || value === "") return "n/a";
  return Number(value).toFixed(1);
}

function formatMaybe(value, suffix = "", digits = 1) {
  if (value === null || value === undefined || value === "") return "n/a";
  return `${Number(value).toFixed(digits)}${suffix}`;
}

function renderResearchMonitor(monitor) {
  const status = document.getElementById("monitorStatus");
  const summary = monitor.summary || {};
  const ruleAlert = summary.rule_alert || summary.highest_alert || "green";
  document.getElementById("ruleAlertValue").textContent = ruleAlert;
  document.getElementById("ruleAlertValue").className = severityClass(ruleAlert);
  document.getElementById("ruleAlertNote").textContent =
    ruleAlert === "green"
      ? "No deterministic alert currently triggered."
      : "Deterministic monitor has a rule output to review.";
  status.className = "monitor-status ready";
  status.textContent = `Generated ${escapeHtml(monitor.generatedAtUtc)}. LLM phase: ${escapeHtml(
    monitor.principles?.llm_phase || "disabled"
  )}.`;

  const kpis = document.getElementById("monitorKpis");
  kpis.hidden = false;
  const alertCounts = summary.alert_counts || {};
  const sourceCounts = summary.source_status_counts || {};
  const evidenceCoverage = summary.evidence_coverage || {};
  const riskSummary = summary.risk_overlay || {};
  const disciplineSummary = summary.decision_discipline || {};
  const secSummary = summary.sec_filings || {};
  const linkSummary = summary.link_health || {};
  kpis.innerHTML = [
    ["Rule alert", ruleAlert, severityClass(ruleAlert)],
    ["Review queue", summary.review_queue_count ?? 0, ""],
    ["Evidence coverage", Number(evidenceCoverage.coverage_ratio || 0).toFixed(2), ""],
    ["Capex direct", `${Number(riskSummary.capex_direct_exposure_pct || 0).toFixed(0)}%`, ""],
    ["Falsifier coverage", Number(disciplineSummary.operational_falsifier_coverage || 0).toFixed(2), ""],
    ["Bear coverage", Number(disciplineSummary.bear_case_coverage || 0).toFixed(2), ""],
    ["SEC reviews", secSummary.review_required_count ?? 0, ""],
    ["Broken links", linkSummary.broken ?? 0, ""],
    ["Yellow alerts", alertCounts.yellow ?? 0, ""],
    ["Red alerts", alertCounts.red ?? 0, ""],
    ["Healthy sources", sourceCounts.healthy ?? 0, ""],
    ["Stale/broken", summary.source_issues ?? 0, ""]
  ]
    .map(
      ([label, value, tone]) => `
        <div class="monitor-kpi">
          <span>${escapeHtml(label)}</span>
          <strong class="${escapeHtml(tone)}">${escapeHtml(value)}</strong>
        </div>
      `
    )
    .join("");

  renderMonitorAlerts(monitor.alerts || []);
  renderRiskOverlay(monitor.riskOverlay || {});
  renderDecisionDiscipline(monitor.decisionDiscipline || {});
  renderSecFilings(monitor.secFilings || {});
  renderReviewQueue(monitor.reviewQueue || []);
  renderMonitorHoldings(monitor.holdings || []);
  renderSourceHealth(monitor.sourceHealth || []);
  renderLinkHealth(monitor.linkHealth || {});
  loadProvenanceCoverage();
}

function renderRiskOverlay(overlay) {
  const panel = document.getElementById("riskOverlayPanel");
  const riskFactors = overlay.riskFactors || [];
  const frameworkGaps = overlay.frameworkGaps || [];
  if (!riskFactors.length && !frameworkGaps.length) {
    panel.innerHTML = `<div class="empty-monitor">No risk overlay configured yet.</div>`;
    return;
  }
  panel.innerHTML = `
    <div class="risk-factor-grid">
      ${riskFactors
        .map((factor) => {
          const groups = Object.entries(factor.exposure_groups || {});
          return `
            <article>
              <div class="card-head">
                <div>
                  <p class="section-label">${escapeHtml(factor.id)}</p>
                  <h3>${escapeHtml(factor.label)}</h3>
                </div>
                <span class="severity ${severityClass(factor.status)}">${escapeHtml(factor.status)}</span>
              </div>
              <div class="meta-row">
                <span>Primary: ${escapeHtml(factor.primary_group)}</span>
                <span>Exposure: ${Number(factor.primary_exposure_pct || 0).toFixed(1)}%</span>
                <span>Threshold: ${Number(factor.threshold_pct || 0).toFixed(1)}%</span>
              </div>
              <p>${escapeHtml(factor.thesis_test)}</p>
              <div class="risk-group-list">
                ${groups
                  .map(
                    ([group, value]) => `
                      <div>
                        <strong>${escapeHtml(group)} ${Number(value.target_weight || 0).toFixed(1)}%</strong>
                        <span>${escapeHtml((value.tickers || []).join(", "))}</span>
                      </div>
                    `
                  )
                  .join("")}
              </div>
              <p class="muted">${escapeHtml(factor.review_policy)}</p>
            </article>
          `;
        })
        .join("")}
    </div>
    <div class="framework-gap-list">
      ${frameworkGaps
        .map(
          (gap) => `
            <article>
              <div class="card-head">
                <strong>${escapeHtml(gap.label)}</strong>
                <span class="severity ${severityClass(gap.status)}">${escapeHtml(gap.status)}</span>
              </div>
              <p>${escapeHtml(gap.reason)}</p>
              <ul>
                ${(gap.research_questions || [])
                  .map((question) => `<li>${escapeHtml(question)}</li>`)
                  .join("")}
              </ul>
            </article>
          `
        )
        .join("")}
    </div>
  `;
}

function renderDecisionDiscipline(discipline) {
  const panel = document.getElementById("disciplinePanel");
  const summary = discipline.summary || {};
  const thresholds = discipline.falsifierThresholds || [];
  if (!thresholds.length) {
    panel.innerHTML = `<div class="empty-monitor">No operational falsifier thresholds configured yet.</div>`;
    return;
  }
  panel.innerHTML = `
    <div class="discipline-kpis">
      <div>
        <span>Operational falsifiers</span>
        <strong>${escapeHtml(summary.operational_falsifier_count ?? 0)}/${escapeHtml(
          summary.holding_count ?? 0
        )}</strong>
      </div>
      <div>
        <span>Bear cases</span>
        <strong>${escapeHtml(summary.bear_case_count ?? 0)}/${escapeHtml(
          summary.holding_count ?? 0
        )}</strong>
      </div>
      <div>
        <span>Valuation gates</span>
        <strong>${escapeHtml(summary.valuation_band_count ?? 0)}/${escapeHtml(
          summary.holding_count ?? 0
        )}</strong>
      </div>
      <div>
        <span>Action boundary</span>
        <strong>review</strong>
      </div>
    </div>
    <div class="threshold-list">
      ${thresholds
        .slice(0, 6)
        .map(
          (item) => `
            <article>
              <p class="section-label">${escapeHtml(item.ticker)} | ${escapeHtml(item.metric_id)}</p>
              <p>${escapeHtml(item.threshold)}</p>
              <p class="muted">${escapeHtml(item.decision_rule)}</p>
            </article>
          `
        )
        .join("")}
    </div>
  `;
}

function renderSecFilings(secFilings) {
  const panel = document.getElementById("secPanel");
  const companies = secFilings.companies || [];
  if (!companies.length) {
    panel.innerHTML = `<div class="empty-monitor">No SEC filing feed generated yet.</div>`;
    return;
  }
  const summary = secFilings.summary || {};
  const latest = companies
    .filter((company) => company.latest_relevant_filing)
    .sort((left, right) =>
      String(right.latest_relevant_filing?.filing_date || "").localeCompare(
        String(left.latest_relevant_filing?.filing_date || "")
      )
    )
    .slice(0, 8);
  panel.innerHTML = `
    <div class="discipline-kpis">
      <div>
        <span>Tracked companies</span>
        <strong>${escapeHtml(summary.company_count ?? 0)}</strong>
      </div>
      <div>
        <span>Healthy feeds</span>
        <strong>${escapeHtml(summary.healthy_company_count ?? 0)}</strong>
      </div>
      <div>
        <span>Filing reviews</span>
        <strong>${escapeHtml(summary.review_required_count ?? 0)}</strong>
      </div>
      <div>
        <span>Boundary</span>
        <strong>event</strong>
      </div>
    </div>
    <div class="filing-list">
      ${latest
        .map((company) => {
          const filing = company.latest_relevant_filing || {};
          return `
            <article>
              <div class="card-head">
                <div>
                  <p class="section-label">${escapeHtml(company.ticker)} | ${escapeHtml(filing.form)}</p>
                  <h3>${escapeHtml(filing.filing_date || "undated")}</h3>
                </div>
                <span class="severity ${company.review_required ? "yellow" : "green"}">${
                  company.review_required ? "review" : "current"
                }</span>
              </div>
              <p>${escapeHtml(company.reason)}</p>
              <div class="meta-row">
                <span>CIK: ${escapeHtml(company.cik)}</span>
                <span>Accession: ${escapeHtml(filing.accession_number || "n/a")}</span>
              </div>
              ${
                filing.url
                  ? `<a class="source-pill" href="${safeUrl(filing.url)}" target="_blank" rel="noopener noreferrer">SEC filing</a>`
                  : ""
              }
            </article>
          `;
        })
        .join("")}
    </div>
  `;
}

function renderReviewQueue(queue) {
  const reviewQueue = document.getElementById("reviewQueue");
  if (!queue.length) {
    reviewQueue.innerHTML = `<div class="empty-monitor">No review actions currently queued.</div>`;
    return;
  }
  reviewQueue.innerHTML = queue
    .map(
      (item, index) => `
        <article class="review-card">
          <div class="review-rank">${index + 1}</div>
          <div>
            <div class="card-head">
              <h3>${escapeHtml(item.ticker)} | ${escapeHtml(item.type)}</h3>
              <span class="severity ${severityClass(item.priority)}">${escapeHtml(item.priority)}</span>
            </div>
            <p>${escapeHtml(item.question)}</p>
            <div class="meta-row">
              <span>Score: ${escapeHtml(item.score)}</span>
              <span>Metric: ${escapeHtml(item.metric_id || "n/a")}</span>
              <span>Due: ${escapeHtml(item.due || "unscheduled")}</span>
              <span>Source: ${escapeHtml(item.source)}</span>
            </div>
            ${renderScoreBreakdown(item.scoreBreakdown)}
            <p class="muted">${escapeHtml((item.score_reasons || []).join(", "))}</p>
            <p class="muted">${escapeHtml(item.success_condition)}</p>
            ${
              item.url
                ? `<a class="source-pill" href="${safeUrl(item.url)}" target="_blank" rel="noopener noreferrer">Open source</a>`
                : ""
            }
          </div>
        </article>
      `
    )
    .join("");
}

function renderScoreBreakdown(scoreBreakdown) {
  if (!scoreBreakdown) return "";
  return `
    <div class="score-breakdown">
      ${Object.entries(scoreBreakdown)
        .filter(([, value]) => Number(value || 0) !== 0)
        .map(
          ([label, value]) =>
            `<span>${escapeHtml(label)} +${escapeHtml(value)}</span>`
        )
        .join("")}
    </div>
  `;
}

function renderMonitorAlerts(alerts) {
  const alertList = document.getElementById("alertList");
  if (!alerts.length) {
    alertList.innerHTML = `<div class="empty-monitor">No deterministic alerts currently triggered.</div>`;
    return;
  }
  alertList.innerHTML = alerts
    .map(
      (alert) => `
        <article class="alert-card">
          <span class="severity ${severityClass(alert.level)}">${escapeHtml(alert.level)}</span>
          <h3>${escapeHtml(alert.ticker)} | ${escapeHtml(alert.rule_id)}</h3>
          <p>${escapeHtml(alert.message)}</p>
          <div class="meta-row">
            <span>Category: ${escapeHtml(alert.category)}</span>
            <span>Review: ${alert.requires_human_review ? "Required" : "Not required"}</span>
            <span>Date: ${escapeHtml(alert.date)}</span>
          </div>
        </article>
      `
    )
    .join("");
}

async function loadProvenanceCoverage() {
  try {
    const response = await fetch("./provenance-coverage.json", { cache: "no-store" });
    if (!response.ok) {
      renderProvenanceCoverageMissing();
      return;
    }
    renderProvenanceCoverage(await response.json());
  } catch {
    renderProvenanceCoverageMissing();
  }
}

function renderProvenanceCoverageMissing() {
  document.getElementById("provenancePanel").innerHTML =
    `<div class="empty-monitor">No provenance coverage generated yet.</div>`;
}

function renderProvenanceCoverage(provenance) {
  const summary = provenance.summary || {};
  const weakSources = provenance.weakSources || [];
  document.getElementById("provenancePanel").innerHTML = `
    <div class="provenance-kpis">
      <div>
        <span>Material bullets</span>
        <strong>${escapeHtml(summary.materialEvidenceBullets ?? 0)}</strong>
      </div>
      <div>
        <span>Claim-linked</span>
        <strong>${escapeHtml(summary.claimLinkedEvidenceBullets ?? 0)}</strong>
      </div>
      <div>
        <span>Coverage</span>
        <strong>${Number(summary.coverageRatio || 0).toFixed(2)}</strong>
      </div>
      <div>
        <span>Weak sources</span>
        <strong>${escapeHtml(summary.weakSourceCount ?? 0)}</strong>
      </div>
    </div>
    ${
      weakSources.length
        ? `<div class="weak-source-list">${weakSources
            .map(
              (source) => `
                <article>
                  <strong>${escapeHtml(source.ticker)} | ${escapeHtml(source.source_id)}</strong>
                  <p>${escapeHtml(source.reason)}</p>
                  <p class="muted">${escapeHtml(source.recommended_action)}</p>
                </article>
              `
            )
            .join("")}</div>`
        : `<p class="muted">No weak-source records currently flagged.</p>`
    }
  `;
}

function renderMonitorHoldings(holdings) {
  document.getElementById("monitorGrid").innerHTML = holdings
    .map((holding) => {
      const capexRisk = holding.risk_profile?.hyperscaler_capex_cycle || {};
      const threshold = holding.falsifier_threshold || {};
      const valuation = holding.valuation_band || {};
      const bearCase = holding.bear_case || {};
      return `
        <article class="monitor-card">
          <div class="card-head">
            <div>
              <div class="ticker">${escapeHtml(holding.ticker)}</div>
              <div class="name">${escapeHtml(holding.name)}</div>
            </div>
            <span class="severity ${severityClass(holding.status)}">${escapeHtml(holding.status)}</span>
          </div>
          <p>${escapeHtml(holding.core_question)}</p>
          <div class="meta-row">
            <span>Target: ${Number(holding.target_weight || 0).toFixed(2)}%</span>
            <span>Current: ${
              holding.current_weight === null ? "n/a" : Number(holding.current_weight || 0).toFixed(2)
            }%</span>
            <span>Drift: ${Number(holding.weight_drift_pct_points || 0).toFixed(2)} pp</span>
          </div>
          <div class="metric-list">
            ${(holding.top_metrics || [])
              .map(
                (metric) => `
                  <div>
                    <strong>${escapeHtml(metric.name)}</strong>
                    <span>${escapeHtml(metric.cadence)} | ${escapeHtml(metric.source)}</span>
                    <span>State: ${escapeHtml(metric.evidence_state?.state)} | Confidence: ${escapeHtml(
                      metric.evidence_state?.confidence
                    )}</span>
                  </div>
                `
              )
              .join("")}
          </div>
          <p class="muted">Watch: ${escapeHtml(holding.watch_rule)}</p>
          <div class="discipline-list">
            <div>
              <strong>Risk overlay</strong>
              <span>${escapeHtml(capexRisk.category || "unmapped")} | ${escapeHtml(
                capexRisk.sensitivity || "n/a"
              )}</span>
            </div>
            <div>
              <strong>Falsifier trigger</strong>
              <span>${escapeHtml(threshold.threshold || "not configured")}</span>
            </div>
            <div>
              <strong>Valuation gate</strong>
              <span>${escapeHtml(valuation.metric || "n/a")} ${escapeHtml(
                valuation.reasonable_band || ""
              )} | high ${escapeHtml(valuation.review_high || "n/a")}</span>
            </div>
            <div>
              <strong>Bear case</strong>
              <span>${escapeHtml(bearCase.bear_case || "not configured")}</span>
            </div>
          </div>
        </article>
      `;
    })
    .join("");
}

function renderSourceHealth(sources) {
  if (!sources.length) {
    document.getElementById("sourceHealthWrap").innerHTML =
      `<div class="empty-monitor">No source-health records found.</div>`;
    return;
  }
  document.getElementById("sourceHealthWrap").innerHTML = `
    <table class="source-health-table">
      <thead>
        <tr>
          <th>Source</th>
          <th>Status</th>
          <th>Cadence</th>
          <th>Last update</th>
          <th>Boundary</th>
        </tr>
      </thead>
      <tbody>
        ${sources
          .map(
            (source) => `
              <tr>
                <td>
                  <strong>${escapeHtml(source.label)}</strong>
                  <span>${escapeHtml(source.tier)}</span>
                </td>
                <td><span class="severity ${severityClass(source.status)}">${escapeHtml(source.status)}</span></td>
                <td>${escapeHtml(source.cadence)}</td>
                <td>${escapeHtml(source.last_update || "not automated")}</td>
                <td>${escapeHtml(source.status_policy)}</td>
              </tr>
            `
          )
          .join("")}
      </tbody>
    </table>
  `;
}

function renderLinkHealth(linkHealth) {
  const panel = document.getElementById("linkHealthPanel");
  const sources = linkHealth.sources || [];
  if (!sources.length) {
    panel.innerHTML = `<div class="empty-monitor">No link-health snapshot generated yet.</div>`;
    return;
  }
  const summary = linkHealth.summary || {};
  const attention = sources
    .filter(
      (source) =>
        source.link_status !== "ok" ||
        source.source_quality_status === "weak_source" ||
        source.primary_support_required
    )
    .slice(0, 8);
  panel.innerHTML = `
    <div class="discipline-kpis">
      <div>
        <span>Total sources</span>
        <strong>${escapeHtml(summary.total ?? 0)}</strong>
      </div>
      <div>
        <span>OK / redirected</span>
        <strong>${escapeHtml((summary.ok ?? 0) + (summary.redirected ?? 0))}</strong>
      </div>
      <div>
        <span>Forbidden / timeout</span>
        <strong>${escapeHtml((summary.forbidden ?? 0) + (summary.timeout ?? 0))}</strong>
      </div>
      <div>
        <span>Broken</span>
        <strong>${escapeHtml(summary.broken ?? 0)}</strong>
      </div>
    </div>
    <div class="link-health-list">
      ${
        attention.length
          ? attention
              .map(
                (source) => `
                  <article>
                    <div class="card-head">
                      <strong>${escapeHtml(source.source_id)}</strong>
                      <span class="severity ${severityClass(source.link_status)}">${escapeHtml(
                        source.link_status
                      )}</span>
                    </div>
                    <p>${escapeHtml(source.label)}</p>
                    <div class="meta-row">
                      <span>Quality: ${escapeHtml(source.source_quality_status)}</span>
                      <span>HTTP: ${escapeHtml(source.http_status || "n/a")}</span>
                      <span>Fallback: ${source.fallback_required ? "Required" : "Not required"}</span>
                      <span>Archive: ${source.archive_recommended ? "Recommended" : "Not needed"}</span>
                    </div>
                    ${
                      (source.preferred_primary_types || []).length
                        ? `<p class="muted">Preferred primary support: ${escapeHtml(
                            source.preferred_primary_types.join(", ")
                          )}</p>`
                        : ""
                    }
                    <p class="muted">${escapeHtml(source.quality_reason || "")}</p>
                  </article>
                `
              )
              .join("")
          : `<p class="muted">No source needs link-health attention in the latest snapshot.</p>`
      }
    </div>
  `;
}

function renderPortfolioPerformance(portfolio) {
  const summary = portfolio.summary || {};
  const status = document.getElementById("portfolioPerformanceStatus");
  status.className = "portfolio-status ready";
  status.textContent = `Updated ${escapeHtml(portfolio.asOfDate)} from the daily portfolio workflow.`;

  const kpis = document.getElementById("portfolioPerformanceKpis");
  kpis.hidden = false;
  const returnKpi = portfolio.returnKpi || {
    label: summary.annualized_return_basis === "since_start" ? "Since start" : "Annualized",
    value_pct: summary.annualized_return_pct,
    horizonDays: Number(summary.annualized_return_days || 0),
    isAnnualized: summary.annualized_return_basis !== "since_start"
  };
  const periodDays = Number(returnKpi.horizonDays || 0);
  const periodHelper =
    !returnKpi.isAnnualized && periodDays > 0
      ? `${periodDays}d`
      : "";
  kpis.innerHTML = [
    ["Total value", formatUsd(summary.total_value_usd), ""],
    ["Total P/L", formatUsd(summary.pnl_usd), signedClass(summary.pnl_usd)],
    ["Return", formatPct(summary.return_pct), signedClass(summary.return_pct)],
    ["Daily P/L", formatUsd(summary.daily_pnl_usd), signedClass(summary.daily_pnl_usd)],
    ["Daily return", formatPct(summary.daily_return_pct), signedClass(summary.daily_return_pct)],
    [
      returnKpi.label,
      formatPct(returnKpi.value_pct),
      signedClass(returnKpi.value_pct),
      periodHelper
    ]
  ]
    .map(
      ([label, value, tone, helper]) => `
        <div class="portfolio-kpi">
          <span>${escapeHtml(label)}</span>
          <strong class="${tone}">${escapeHtml(value)}</strong>
          ${helper ? `<small>${escapeHtml(helper)}</small>` : ""}
        </div>
      `
    )
    .join("");

  renderPortfolioPerformancePlots(portfolio);
  renderPortfolioPerformanceTable(portfolio);
}

function renderPortfolioPerformancePlots(portfolio) {
  const plots = document.getElementById("portfolioPerformancePlots");
  plots.hidden = false;
  const version = encodeURIComponent(portfolio.updatedAtUtc || Date.now());
  const valuePlot = portfolio.plots?.value;
  const allocationPlot = portfolio.plots?.allocation;
  plots.innerHTML = `
    <figure>
      <figcaption>Value history</figcaption>
      ${
        valuePlot
          ? `<img src="${escapeHtml(valuePlot)}?v=${version}" alt="Portfolio value history plot" />`
          : renderInlineValueChart(portfolio.history || [])
      }
    </figure>
    <figure>
      <figcaption>Current holding values</figcaption>
      ${
        allocationPlot
          ? `<img src="${escapeHtml(allocationPlot)}?v=${version}" alt="Current market value by holding plot" />`
          : renderInlineAllocationChart(portfolio.holdings || [])
      }
    </figure>
  `;
}

function renderPortfolioPerformanceTable(portfolio) {
  document.getElementById("portfolioPerformanceTableWrap").hidden = false;
  document.getElementById("portfolioPerformanceRows").innerHTML = (portfolio.holdings || [])
    .map((holding) => {
      const pnl = Number(holding.pnl_usd || 0);
      return `
        <tr>
          <td>
            <strong>${escapeHtml(holding.ticker)}</strong>
            <span>${escapeHtml(holding.holding_name)}</span>
          </td>
          <td>${escapeHtml(holding.target_weight)}%</td>
          <td>
            ${formatUsd(holding.price_usd)}
            <span>${escapeHtml(holding.currency)} ${Number(holding.price_native || 0).toFixed(2)}</span>
          </td>
          <td>${formatUsd(holding.market_value_usd)}</td>
          <td class="${signedClass(pnl)}">${formatUsd(pnl)}</td>
          <td class="${signedClass(holding.return_pct)}">${formatPct(holding.return_pct)}</td>
        </tr>
      `;
    })
    .join("");
}

function renderInlineValueChart(history) {
  if (!history.length) return `<div class="empty-chart">No history yet</div>`;
  const width = 720;
  const height = 260;
  const padding = 34;
  const values = history.map((row) => Number(row.total_value_usd || 0));
  const min = Math.min(...values, 1000);
  const max = Math.max(...values, 1000);
  const span = Math.max(max - min, 1);
  const points = values
    .map((value, index) => {
      const x = padding + (index / Math.max(values.length - 1, 1)) * (width - padding * 2);
      const y = height - padding - ((value - min) / span) * (height - padding * 2);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
  return `
    <svg class="inline-chart" viewBox="0 0 ${width} ${height}" role="img" aria-label="Portfolio value chart">
      <polyline points="${points}" fill="none" stroke="#0f766e" stroke-width="4" />
    </svg>
  `;
}

function renderInlineAllocationChart(holdings) {
  if (!holdings.length) return `<div class="empty-chart">No holdings yet</div>`;
  const max = Math.max(...holdings.map((holding) => Number(holding.market_value_usd || 0)), 1);
  return `
    <div class="inline-bars">
      ${holdings
        .map((holding) => {
          const width = Math.max(2, (Number(holding.market_value_usd || 0) / max) * 100);
          return `
            <div>
              <span>${escapeHtml(holding.ticker)}</span>
              <div><i style="width:${width}%"></i></div>
              <b>${formatUsd(holding.market_value_usd)}</b>
            </div>
          `;
        })
        .join("")}
    </div>
  `;
}

init();

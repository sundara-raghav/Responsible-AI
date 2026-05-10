let approvalChart;
let ratioChart;
const MAX_HISTORY = 8;
const auditHistory = [];

function switchView(viewName) {
  const auditView = document.getElementById("auditView");
  const minimizationView = document.getElementById("minimizationView");
  const navAudit = document.getElementById("navAudit");
  const navMinimization = document.getElementById("navMinimization");

  const isAudit = viewName === "audit";
  auditView.classList.toggle("is-hidden", !isAudit);
  minimizationView.classList.toggle("is-hidden", isAudit);
  navAudit.classList.toggle("is-active", isAudit);
  navMinimization.classList.toggle("is-active", !isAudit);
}

function formatPercent(value) {
  return `${Number(value).toFixed(1)}%`;
}

function setInsight(message, isError = false) {
  const insightText = document.getElementById("insightText");
  const insightBox = document.getElementById("insightBox");

  insightText.textContent = message;
  insightBox.classList.toggle("error", isError);
}

function renderKpis(result) {
  document.getElementById("kpiStatus").textContent = result.status;
  document.getElementById("kpiRatio").textContent = result.ratio.toFixed(2);
  document.getElementById("kpiGap").textContent = `${result.parity_gap.toFixed(1)} pts`;
  document.getElementById("kpiScore").textContent = `${result.fairness_score.toFixed(1)}%`;
}

function renderHistory() {
  const body = document.getElementById("historyBody");
  body.innerHTML = "";

  auditHistory.forEach((item) => {
    const row = document.createElement("tr");
    row.innerHTML = `<td>${item.kind}</td><td>${item.ratio.toFixed(2)}</td><td>${item.status}</td>`;
    body.appendChild(row);
  });
}

function addHistoryEntry(kind, result) {
  auditHistory.unshift({ kind, ratio: result.ratio, status: result.status });
  if (auditHistory.length > MAX_HISTORY) {
    auditHistory.pop();
  }
  renderHistory();
}

function renderCharts(result) {
  const approvalCtx = document.getElementById("biasChart").getContext("2d");
  const ratioCtx = document.getElementById("ratioChart").getContext("2d");

  if (approvalChart) {
    approvalChart.destroy();
  }
  if (ratioChart) {
    ratioChart.destroy();
  }

  approvalChart = new Chart(approvalCtx, {
    type: "bar",
    data: {
      labels: result.data.labels,
      datasets: [
        {
          label: "Loan Approval Rate (%)",
          data: result.data.approval_rates,
          backgroundColor: ["#1E9E63", "#D1495B"],
          borderColor: ["#137348", "#A93747"],
          borderWidth: 1,
          borderRadius: 10,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: {
            color: "#1F2933",
            font: {
              family: "Space Grotesk",
              weight: "600",
            },
          },
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          max: 100,
          ticks: {
            callback: (value) => `${value}%`,
          },
        },
      },
    },
  });

  ratioChart = new Chart(ratioCtx, {
    type: "bar",
    data: {
      labels: ["Observed Ratio", "Threshold Ratio"],
      datasets: [
        {
          label: "Disparate Impact",
          data: [result.ratio, result.data.threshold],
          backgroundColor: ["#2D6CDF", "#F4B400"],
          borderRadius: 10,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false,
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          max: 1.2,
        },
      },
    },
  });
}

function renderAuditResults(result, auditKind) {
  renderKpis(result);
  renderCharts(result);
  addHistoryEntry(auditKind, result);

  setInsight(
    `Status: ${result.status}. Ratio: ${result.ratio.toFixed(2)} (threshold >= ${result.data.threshold.toFixed(2)}). ` +
      `Parity gap is ${result.parity_gap.toFixed(1)} points. Minority group should be at least ${formatPercent(
        result.data.required_minority_rate
      )} to satisfy the rule. ${result.recommendation}`
  );
}

async function runAudit() {
  const dimension = document.getElementById("dimensionSelect").value;

  try {
    const response = await fetch(`/audit-data?dimension=${encodeURIComponent(dimension)}`);
    if (!response.ok) {
      throw new Error(`Audit request failed with status ${response.status}`);
    }

    const result = await response.json();
    renderAuditResults(result, `Sample:${dimension}`);
  } catch (error) {
    setInsight(`Audit error: ${error.message}`, true);
  }
}

async function runCustomAudit() {
  const payload = {
    labels: [
      document.getElementById("labelA").value || "Group A (Majority)",
      document.getElementById("labelB").value || "Group B (Minority)",
    ],
    approval_rates: [Number(document.getElementById("rateA").value), Number(document.getElementById("rateB").value)],
    threshold: Number(document.getElementById("threshold").value),
  };

  try {
    const response = await fetch("/audit-data", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const result = await response.json();
    if (!response.ok) {
      throw new Error(result.error || "Failed to run custom audit");
    }

    renderAuditResults(result, "Custom");
  } catch (error) {
    setInsight(`Custom audit error: ${error.message}`, true);
  }
}

window.addEventListener("load", () => {
  switchView("audit");
  runAudit();
});

function getSampleMinimizationData() {
  return [
    {
      user_id: 101,
      name: "Alice Johnson",
      email: "alice@example.com",
      phone: "+1-202-555-0134",
      age: 24,
      country: "US",
      transaction_amount: 780.5,
      is_fraud: 0,
      internal_notes: "High-value customer",
    },
    {
      user_id: 102,
      name: "Bob Smith",
      email: "bob@example.com",
      phone: "+1-202-555-0199",
      age: 38,
      country: "US",
      transaction_amount: 122.1,
      is_fraud: 1,
      internal_notes: "Monitor unusual login locations",
    },
  ];
}

function listToDisplay(values) {
  if (!values || values.length === 0) {
    return "None";
  }
  return values.join(", ");
}

function updatePrivacyScore(score) {
  const scoreNode = document.getElementById("privacyScore");
  scoreNode.textContent = `${score.toFixed(0)}%`;
  scoreNode.classList.remove("score-good", "score-medium", "score-low");

  if (score > 70) {
    scoreNode.classList.add("score-good");
    return;
  }

  if (score >= 40) {
    scoreNode.classList.add("score-medium");
    return;
  }

  scoreNode.classList.add("score-low");
}

async function runMinimizationReport() {
  const purpose = document.getElementById("minPurpose").value;
  const data = getSampleMinimizationData();

  try {
    const response = await fetch("/api/minimize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ data, purpose }),
    });

    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || "Failed to run minimization report");
    }

    const collectedFields = data.length ? Object.keys(data[0]) : [];
    const usedFields = payload.data.length ? Object.keys(payload.data[0]) : [];
    const minimizedPercent =
      collectedFields.length === 0
        ? 100
        : ((collectedFields.length - usedFields.length) / collectedFields.length) * 100;

    const actions = payload.audit_log.actions || [];
    const latestAction = actions.length ? actions[actions.length - 1] : { fields_dropped: [], fields_masked: [] };

    document.getElementById("fieldsCollected").textContent = `${collectedFields.length}`;
    document.getElementById("fieldsUsed").textContent = `${usedFields.length}`;
    document.getElementById("droppedFields").textContent = listToDisplay(latestAction.fields_dropped);
    document.getElementById("maskedFields").textContent = listToDisplay(latestAction.fields_masked);
    updatePrivacyScore(Math.max(0, Math.min(100, minimizedPercent)));
  } catch (error) {
    setInsight(`Data minimization error: ${error.message}`, true);
  }
}
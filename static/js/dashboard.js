/**
 * Dashboard Controller Module for Smart Agriculture Assistant.
 * Coordinates user input submission, sample demo profiles, dynamic result rendering,
 * explainability factors, interactive tabs, and report export.
 */

let currentAnalysisData = null;
let sampleFarmsCache = [];

document.addEventListener("DOMContentLoaded", () => {
  initSampleFarms();
  setupFormHandlers();
  setupTabHandlers();
});

/**
 * Fetch and setup demo farm profiles
 */
async function initSampleFarms() {
  const sampleSelect = document.getElementById("sampleFarmSelect");
  if (!sampleSelect) return;

  try {
    const res = await fetch("/api/sample-farms");
    const json = await res.json();
    if (json.status === "success" && json.sample_farms) {
      sampleFarmsCache = json.sample_farms;
      sampleFarmsCache.forEach((farm, idx) => {
        const opt = document.createElement("option");
        opt.value = idx;
        opt.textContent = `${farm.name} (${farm.region})`;
        sampleSelect.appendChild(opt);
      });
    }
  } catch (err) {
    console.error("Failed to load sample farms:", err);
  }
}

/**
 * Populate form fields from selected demo farm
 */
function loadSampleFarm(index) {
  if (index === "" || !sampleFarmsCache[index]) return;
  const farm = sampleFarmsCache[index];

  document.getElementById("farmName").value = farm.name;
  document.getElementById("inputN").value = farm.N;
  document.getElementById("inputP").value = farm.P;
  document.getElementById("inputK").value = farm.K;
  document.getElementById("inputTemp").value = farm.temperature;
  document.getElementById("inputHumidity").value = farm.humidity;
  document.getElementById("inputPh").value = farm.ph;
  document.getElementById("inputRainfall").value = farm.rainfall;
  document.getElementById("inputSeason").value = farm.season;

  showToast(`Loaded sample profile: ${farm.name}`, "success");
}

/**
 * Form Submit & Validation
 */
function setupFormHandlers() {
  const form = document.getElementById("farmAnalysisForm");
  const sampleSelect = document.getElementById("sampleFarmSelect");
  const resetBtn = document.getElementById("resetFormBtn");
  const printBtn = document.getElementById("printReportBtn");

  if (sampleSelect) {
    sampleSelect.addEventListener("change", (e) => loadSampleFarm(e.target.value));
  }

  if (resetBtn) {
    resetBtn.addEventListener("click", () => {
      form.reset();
      document.getElementById("resultsSection").style.display = "none";
      showToast("Form cleared.", "info");
    });
  }

  if (printBtn) {
    printBtn.addEventListener("click", () => window.print());
  }

  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      await runFarmAnalysis();
    });
  }
}

/**
 * Execute Farm Analysis API Call
 */
async function runFarmAnalysis() {
  const submitBtn = document.getElementById("analyzeBtn");
  const originalBtnText = submitBtn.innerHTML;

  // Gather inputs
  const payload = {
    farm_name: document.getElementById("farmName").value.trim() || "My Farm",
    N: parseFloat(document.getElementById("inputN").value),
    P: parseFloat(document.getElementById("inputP").value),
    K: parseFloat(document.getElementById("inputK").value),
    temperature: parseFloat(document.getElementById("inputTemp").value),
    humidity: parseFloat(document.getElementById("inputHumidity").value),
    ph: parseFloat(document.getElementById("inputPh").value) || 6.5,
    rainfall: parseFloat(document.getElementById("inputRainfall").value),
    season: document.getElementById("inputSeason").value,
    top_k: 3
  };

  // Client-side quick checks
  if (isNaN(payload.N) || isNaN(payload.P) || isNaN(payload.K) || isNaN(payload.temperature) || isNaN(payload.humidity) || isNaN(payload.rainfall)) {
    showToast("Please fill in all required numerical fields.", "warning");
    return;
  }

  try {
    submitBtn.disabled = true;
    submitBtn.innerHTML = `<span>⏳</span> Analyzing Farm Conditions...`;

    const res = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const data = await res.json();

    if (!res.ok || data.status !== "success") {
      showToast(data.message || "Failed to analyze farm conditions.", "danger");
      return;
    }

    currentAnalysisData = data.data;
    renderAnalysisResults(currentAnalysisData);
    showToast("Analysis complete! Recommended crops generated.", "success");

    // Scroll smoothly to results
    const resultsElem = document.getElementById("resultsSection");
    resultsElem.style.display = "block";
    resultsElem.scrollIntoView({ behavior: "smooth", block: "start" });

  } catch (err) {
    console.error("API error:", err);
    showToast("An error occurred communicating with the server.", "danger");
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = originalBtnText;
  }
}

/**
 * Render Complete Analysis Results
 */
function renderAnalysisResults(data) {
  const primary = data.primary_recommendation;
  const topRecs = data.top_recommendations || [];
  const soil = data.soil_health || {};
  const env = data.environmental_conditions || {};

  // 1. Primary Recommendation Hero Card
  document.getElementById("heroCropName").innerHTML = `${primary.icon || '🌾'} ${primary.crop_name}`;
  document.getElementById("heroScientific").textContent = primary.scientific_name ? `(${primary.scientific_name}) • ${primary.category}` : primary.category;
  document.getElementById("heroScore").textContent = `${primary.suitability_score}%`;
  document.getElementById("heroGaugeBar").style.width = `${primary.suitability_score}%`;
  document.getElementById("heroConfidenceBadge").textContent = primary.confidence_label;

  // 2. Render Top 3 Candidate Cards
  renderTopCandidates(topRecs);

  // 3. Render Explainable "Why This Crop" Breakdown
  renderWhyBreakdown(primary);

  // 4. Render Soil Health Section
  renderSoilHealth(soil);

  // 5. Render Environmental Conditions Section
  renderEnvironmentalConditions(env);

  // 6. Render Agricultural Guidance for Selected Crop
  renderGuidanceTabs(primary);

  // 7. Render Charts
  renderTopCropsChart("topCropsChart", topRecs);
  renderSoilNutrientChart("soilChart", data.inputs.N, data.inputs.P, data.inputs.K, data.inputs.ph);

  // 8. Warnings & Notes
  renderWarnings(env.warnings || [], data.warnings || []);
}

/**
 * Top Candidate Cards
 */
function renderTopCandidates(recs) {
  const container = document.getElementById("topCandidatesContainer");
  if (!container) return;
  container.innerHTML = "";

  recs.forEach((rec, idx) => {
    const card = document.createElement("div");
    card.className = `crop-candidate-card ${idx === 0 ? 'selected' : ''}`;
    card.onclick = () => selectCandidateCrop(idx);

    card.innerHTML = `
      <div class="candidate-rank">#${rec.rank}</div>
      <div style="font-size: 2rem; margin-bottom: 0.5rem;">${rec.icon || '🌱'}</div>
      <h4 style="font-size: 1.15rem; margin-bottom: 0.25rem;">${rec.crop_name}</h4>
      <div style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 0.75rem;">${rec.category}</div>
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <span class="badge ${rec.suitability_score >= 80 ? 'badge-success' : 'badge-primary'}">${rec.suitability_score}% Suitability</span>
      </div>
    `;
    container.appendChild(card);
  });
}

/**
 * Switch selected candidate crop in result view
 */
function selectCandidateCrop(index) {
  if (!currentAnalysisData || !currentAnalysisData.top_recommendations[index]) return;
  const selected = currentAnalysisData.top_recommendations[index];

  // Update selection UI border
  const cards = document.querySelectorAll(".crop-candidate-card");
  cards.forEach((c, idx) => {
    if (idx === index) c.classList.add("selected");
    else c.classList.remove("selected");
  });

  // Re-render Explainability & Guidance for selected crop
  renderWhyBreakdown(selected);
  renderGuidanceTabs(selected);
}

/**
 * Render "Why This Crop?" Breakdown
 */
function renderWhyBreakdown(cropRec) {
  const container = document.getElementById("whyFactorsList");
  const cropTitleElem = document.getElementById("whyCropName");
  if (cropTitleElem) cropTitleElem.textContent = cropRec.crop_name;
  if (!container) return;
  container.innerHTML = "";

  const breakdown = cropRec.why_breakdown || { factors: [] };
  
  breakdown.factors.forEach(factor => {
    const li = document.createElement("li");
    li.className = "why-item";
    li.innerHTML = `
      <span class="${factor.positive ? 'why-icon-check' : 'why-icon-warn'}">${factor.icon}</span>
      <div>
        <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:2px;">
          <span class="why-category">${factor.category}</span>
          <span class="badge ${factor.positive ? 'badge-success' : 'badge-warning'}">${factor.status}</span>
        </div>
        <div class="why-desc">${factor.detail}</div>
      </div>
    `;
    container.appendChild(li);
  });
}

/**
 * Render Soil Health Status
 */
function renderSoilHealth(soil) {
  document.getElementById("soilOverallStatus").textContent = soil.overall_status || "Good";
  const badgeElem = document.getElementById("soilOverallBadge");
  badgeElem.className = `badge badge-${soil.overall_badge || 'success'}`;
  badgeElem.textContent = `${soil.overall_score || 80}/100`;

  document.getElementById("soilSummaryText").textContent = soil.summary || "";

  // Nutrients
  const setNutrient = (idVal, idStatus, idBadge, data) => {
    document.getElementById(idVal).textContent = `${data.value} kg/ha`;
    const statusElem = document.getElementById(idStatus);
    statusElem.textContent = data.status;
    statusElem.className = `badge badge-${data.badge}`;
  };

  if (soil.nitrogen) setNutrient("valNitrogen", "statusNitrogen", "badgeNitrogen", soil.nitrogen);
  if (soil.phosphorus) setNutrient("valPhosphorus", "statusPhosphorus", "badgePhosphorus", soil.phosphorus);
  if (soil.potassium) setNutrient("valPotassium", "statusPotassium", "badgePotassium", soil.potassium);

  if (soil.ph) {
    document.getElementById("valPh").textContent = `${soil.ph.value} pH`;
    const phStatus = document.getElementById("statusPh");
    phStatus.textContent = soil.ph.status;
    phStatus.className = `badge badge-${soil.ph.badge}`;
  }
}

/**
 * Render Environmental Summary
 */
function renderEnvironmentalConditions(env) {
  document.getElementById("dispTemp").textContent = `${env.temperature_val}°C`;
  document.getElementById("dispHumidity").textContent = `${env.humidity_val}%`;
  document.getElementById("dispRainfall").textContent = `${env.rainfall_val} mm`;
}

/**
 * Render Warnings
 */
function renderWarnings(envWarnings, dataWarnings) {
  const container = document.getElementById("warningsContainer");
  const list = document.getElementById("warningsList");
  if (!container || !list) return;

  const allWarnings = [...envWarnings, ...dataWarnings];
  if (allWarnings.length === 0) {
    container.style.display = "none";
    return;
  }

  container.style.display = "block";
  list.innerHTML = "";
  allWarnings.forEach(w => {
    const li = document.createElement("li");
    li.textContent = w;
    list.appendChild(li);
  });
}

/**
 * Render Guidance Tab Panes
 */
function renderGuidanceTabs(cropRec) {
  const g = cropRec.guidance || {};
  document.getElementById("guidanceCropTitle").textContent = `${cropRec.crop_name} Agronomic Guidance`;
  document.getElementById("guideOverview").textContent = g.overview || "No overview available.";
  document.getElementById("guideSoil").textContent = g.suitable_soil || "No soil guidance available.";
  document.getElementById("guideNutrients").textContent = g.nutrient_considerations || "";
  document.getElementById("guideWater").textContent = g.water_requirement || "";
  document.getElementById("guideIrrigation").textContent = g.irrigation_guidance || "";
  document.getElementById("guideCultivation").textContent = g.cultivation_tips || "";
  document.getElementById("guideMonitoring").textContent = g.monitoring_tips || "";
  document.getElementById("guideConcerns").textContent = g.common_concerns || "";
}

/**
 * Tab Navigation Handler
 */
function setupTabHandlers() {
  const tabBtns = document.querySelectorAll(".tab-btn");
  tabBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      const targetId = btn.getAttribute("data-tab");
      tabBtns.forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));

      btn.classList.add("active");
      const pane = document.getElementById(targetId);
      if (pane) pane.classList.add("active");
    });
  });
}

/**
 * Dashboard Controller Module for Smart Agriculture Assistant.
 * Coordinates user input submission, sample demo profiles, dynamic result rendering,
 * explainability factors, interactive tabs, and report export.
 */

let currentAnalysisData = null;
let sampleFarmsCache = [];
const farmSources = {N:"manual", P:"manual", K:"manual", ph:"manual", temperature:"manual", humidity:"manual", rainfall:"manual", soil_temperature:"manual", soil_moisture:"manual"};
let selectedFarmId = null;
let verifiedReportId = null;
let latestSensorValues = {};
let settingCollectedValues = false;

document.addEventListener("DOMContentLoaded", () => {
  initSampleFarms();
  setupFormHandlers();
  setupTabHandlers();
  setupFarmDataCollection();
  loadAccountFarms();
  updateSourceTable();
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
  ["N", "P", "K", "ph", "temperature", "humidity", "rainfall"].forEach(field => farmSources[field] = "demo");
  updateSourceTable();

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
      document.getElementById("soilReportReview").hidden = true;
      document.getElementById("soilReportFile").value = "";
      verifiedReportId = null;
      Object.keys(farmSources).forEach(field => farmSources[field] = "manual");
      verifiedReportId = null;
      updateSourceTable();
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

function optionalNumber(id) {
  const raw = document.getElementById(id)?.value;
  return raw === undefined || raw === "" ? null : Number(raw);
}

function collectedFormValues() {
  return {
    N: optionalNumber("inputN"), P: optionalNumber("inputP"), K: optionalNumber("inputK"),
    ph: optionalNumber("inputPh"), temperature: optionalNumber("inputTemp"),
    humidity: optionalNumber("inputHumidity"), rainfall: optionalNumber("inputRainfall"),
    soil_temperature: optionalNumber("inputSoilTemp"), soil_moisture: optionalNumber("inputSoilMoisture"),
    season: document.getElementById("inputSeason").value
  };
}

function updateSourceTable() {
  const body = document.getElementById("farmDataSources");
  if (!body) return;
  const values = collectedFormValues();
  const details = [
    ["Nitrogen", "N", "kg/ha"], ["Phosphorus", "P", "kg/ha"], ["Potassium", "K", "kg/ha"],
    ["Soil pH", "ph", ""], ["Soil temperature", "soil_temperature", "°C"],
    ["Soil moisture", "soil_moisture", "%"], ["Air temperature", "temperature", "°C"],
    ["Humidity", "humidity", "%"], ["Rainfall", "rainfall", "mm"]
  ];
  body.replaceChildren();
  details.forEach(([label, field, unit]) => {
    const row = document.createElement("tr");
    const shownValue = Number.isFinite(values[field]) ? `${values[field]}${unit ? ` ${unit}` : ""}` : "Not provided";
    const source = ({manual:"Manual", soil_report:"Soil Test Report", soil_sensor:"Soil Sensor", weather_service:"Weather Service", demo:"Demo Data"})[farmSources[field]] || "Manual";
    [label, shownValue, source].forEach(text => { const cell = document.createElement("td"); cell.textContent = text; row.append(cell); });
    body.append(row);
  });
  const required = [["Nitrogen","N"],["Phosphorus","P"],["Potassium","K"],["Soil pH","ph"],["Air temperature","temperature"],["Humidity","humidity"],["Rainfall","rainfall"]];
  const missing = required.filter(([,field]) => !Number.isFinite(values[field])).map(([label]) => label);
  const completeness = document.getElementById("farmDataCompleteness");
  if (completeness) completeness.textContent = missing.length ? `${Math.round((required.length - missing.length) * 100 / required.length)}% complete. Missing: ${missing.join(", ")}.` : "All required values are present. Check ranges and source labels before analysis.";
}

async function updateReadiness() {
  const status = document.getElementById("farmDataCompleteness");
  const values = collectedFormValues();
  try {
    const response = await fetch("/api/farm-data/validate", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({...values, sources:farmSources})});
    const result = await response.json();
    if (!response.ok || result.status !== "success") { status.textContent = result.message || "Check each value and try again."; return; }
    if (result.valid) {
      const warning = (result.warnings || []).length ? ` ${result.warnings.join(" ")}` : "";
      status.textContent = `All required data is ready (${result.completeness}%). Sources are shown below.${warning}`;
    } else {
      const names = {N:"Nitrogen",P:"Phosphorus",K:"Potassium",ph:"Soil pH",temperature:"Air temperature",humidity:"Humidity",rainfall:"Rainfall"};
      const missing = (result.missing || []).map(field => names[field] || field);
      status.textContent = `${result.completeness}% complete. Missing: ${missing.join(", ") || result.message}`;
    }
  } catch (_) { status.textContent = "Farm data status could not be checked. You can still review the required fields below."; }
}

function setupFarmDataCollection() {
  const fieldInputs = {inputN:"N", inputP:"P", inputK:"K", inputPh:"ph", inputTemp:"temperature", inputHumidity:"humidity", inputRainfall:"rainfall", inputSoilTemp:"soil_temperature", inputSoilMoisture:"soil_moisture"};
  Object.entries(fieldInputs).forEach(([id, field]) => document.getElementById(id)?.addEventListener("input", () => {
    if (!settingCollectedValues) farmSources[field] = "manual";
    updateSourceTable();
  }));
  document.getElementById("checkFarmDataBtn")?.addEventListener("click", updateReadiness);

  document.getElementById("uploadSoilReportBtn")?.addEventListener("click", uploadSoilReport);
  document.getElementById("verifySoilValuesBtn")?.addEventListener("click", verifySoilReport);
  document.getElementById("sendSensorBtn")?.addEventListener("click", () => submitSensorReading(false));
  document.getElementById("simulateSensorBtn")?.addEventListener("click", () => submitSensorReading(true));
  document.getElementById("loadWeatherBtn")?.addEventListener("click", loadFarmWeather);
}

async function loadAccountFarms() {
  const wrapper = document.getElementById("accountFarmPickerWrap");
  const select = document.getElementById("accountFarmSelect");
  if (!wrapper || !select) return;
  try {
    const response = await fetch("/api/farms");
    if (!response.ok) return;
    const data = await response.json();
    wrapper.hidden = false;
    data.farms.forEach(farm => {
      const option = document.createElement("option"); option.value = farm.id; option.textContent = farm.name; select.append(option);
    });
    const requested = new URLSearchParams(location.search).get("farm_id");
    if (requested && data.farms.some(farm => String(farm.id) === requested)) select.value = requested;
    select.addEventListener("change", () => {
      selectedFarmId = select.value || null;
      const farm = data.farms.find(item => String(item.id) === String(selectedFarmId));
      if (farm) {
        document.getElementById("farmName").value = farm.name;
        document.getElementById("farmLocationInput").value = farm.location || [farm.village, farm.district, farm.state].filter(Boolean).join(", ");
      }
    });
    select.dispatchEvent(new Event("change"));
  } catch (_) { /* Public analysis remains available without an account. */ }
}

async function uploadSoilReport() {
  const fileInput = document.getElementById("soilReportFile");
  const message = document.getElementById("soilReportMessage");
  if (!fileInput.files.length) { message.textContent = "Choose a report file first."; return; }
  const form = new FormData(); form.append("report", fileInput.files[0]);
  if (selectedFarmId) form.append("farm_id", selectedFarmId);
  message.textContent = "Reading report…";
  try {
    const response = await fetch("/api/soil-report/upload", {method:"POST", body:form});
    const result = await response.json();
    if (!response.ok || result.status !== "success") throw new Error(result.message || "Report upload failed.");
    verifiedReportId = result.report_id;
    const reportFields = {N:"reportN", P:"reportP", K:"reportK", ph:"reportPh"};
    Object.entries(reportFields).forEach(([field,id]) => {
      const extracted = result.values[field];
      document.getElementById(id).value = extracted?.value ?? "";
      const confidence = extracted?.status === "detected" ? "detected" : "not confidently detected; enter manually";
      document.getElementById(id).setAttribute("aria-label", `${field}: ${confidence}`);
    });
    document.getElementById("soilReportReview").hidden = false;
    message.textContent = `${result.filename}: detected values are editable. Review and press Verify Soil Values.`;
    updateSourceTable();
  } catch (error) { message.textContent = error.message; }
}

async function verifySoilReport() {
  const message = document.getElementById("soilReportMessage");
  if (!verifiedReportId) { message.textContent = "Upload a report before verifying values."; return; }
  const values = {N:optionalNumber("reportN"), P:optionalNumber("reportP"), K:optionalNumber("reportK"), ph:optionalNumber("reportPh")};
  try {
    const response = await fetch(`/api/soil-reports/${verifiedReportId}/verify`, {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({values})});
    const result = await response.json();
    if (!response.ok || result.status !== "success") throw new Error(result.message || "Could not verify report values.");
    const destinations = {N:"inputN", P:"inputP", K:"inputK", ph:"inputPh"};
    settingCollectedValues = true;
    Object.entries(destinations).forEach(([field,id]) => {
      if (values[field] !== null) { document.getElementById(id).value = values[field]; farmSources[field] = "soil_report"; }
    });
    settingCollectedValues = false;
    message.textContent = "Values verified. Any missing report value still needs a manual entry before analysis.";
    updateSourceTable(); updateReadiness();
  } catch (error) { settingCollectedValues = false; message.textContent = error.message; }
}

async function submitSensorReading(simulate) {
  const message = document.getElementById("sensorMessage");
  const body = {device_id:document.getElementById("sensorDeviceId").value.trim(), farm_id:selectedFarmId ? Number(selectedFarmId) : null};
  if (!simulate) {
    body.soil_temperature = optionalNumber("sensorSoilTemp");
    body.soil_moisture = optionalNumber("sensorMoisture");
    body.ph = optionalNumber("sensorPh");
  }
  try {
    const response = await fetch(simulate ? "/api/sensor-data/simulate" : "/api/sensor-data", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(body)});
    const result = await response.json();
    if (!response.ok || result.status !== "success") throw new Error(result.message || "Sensor reading could not be saved.");
    const reading = result.reading;
    latestSensorValues = reading;
    settingCollectedValues = true;
    if (Number.isFinite(reading.ph)) { document.getElementById("inputPh").value = reading.ph; farmSources.ph = simulate ? "demo" : "soil_sensor"; }
    if (Number.isFinite(reading.soil_temperature)) { document.getElementById("inputSoilTemp").value = reading.soil_temperature; farmSources.soil_temperature = simulate ? "demo" : "soil_sensor"; }
    if (Number.isFinite(reading.soil_moisture)) { document.getElementById("inputSoilMoisture").value = reading.soil_moisture; farmSources.soil_moisture = simulate ? "demo" : "soil_sensor"; }
    settingCollectedValues = false;
    message.textContent = simulate ? "Demo/Simulated reading saved and labelled as demo data." : `Reading received from ${body.device_id}.`;
    updateSourceTable(); updateReadiness();
  } catch (error) { settingCollectedValues = false; message.textContent = error.message; }
}

async function loadFarmWeather() {
  const message = document.getElementById("weatherMessage");
  const locationValue = document.getElementById("farmLocationInput").value.trim();
  if (!locationValue) { message.textContent = "Enter or select a farm location first."; return; }
  message.textContent = "Requesting weather for this location…";
  try {
    const response = await fetch("/api/weather-data", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({location:locationValue, farm_id:selectedFarmId ? Number(selectedFarmId) : null})});
    const result = await response.json();
    if (!response.ok || result.status !== "success") throw new Error(result.message || "Weather is unavailable.");
    const weather = result.weather;
    settingCollectedValues = true;
    [["temperature","inputTemp"],["humidity","inputHumidity"],["rainfall","inputRainfall"]].forEach(([field,id]) => {
      if (Number.isFinite(weather[field])) { document.getElementById(id).value = weather[field]; farmSources[field] = "weather_service"; }
    });
    settingCollectedValues = false;
    message.textContent = "Weather data loaded from the configured provider. Check the rainfall period against crop-season needs.";
    updateSourceTable(); updateReadiness();
  } catch (error) { settingCollectedValues = false; message.textContent = error.message; }
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
    ph: optionalNumber("inputPh"),
    soil_temperature: optionalNumber("inputSoilTemp"),
    soil_moisture: optionalNumber("inputSoilMoisture"),
    rainfall: parseFloat(document.getElementById("inputRainfall").value),
    season: document.getElementById("inputSeason").value,
    top_k: 3,
    require_complete: true,
    sources: {...farmSources},
    farm_id: selectedFarmId ? Number(selectedFarmId) : null,
    farm_location: document.getElementById("farmLocationInput")?.value.trim() || null,
    report_id: verifiedReportId
  };

  // Client-side quick checks
  const missing = [["Nitrogen",payload.N],["Phosphorus",payload.P],["Potassium",payload.K],["Soil pH",payload.ph],["Air temperature",payload.temperature],["Humidity",payload.humidity],["Rainfall",payload.rainfall]].filter(([,value]) => !Number.isFinite(value)).map(([name]) => name);
  if (missing.length) {
    showToast(`Farm data missing: ${missing.join(", ")}. Enter these values or use a report/weather source.`, "warning");
    return;
  }
  updateReadiness();

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

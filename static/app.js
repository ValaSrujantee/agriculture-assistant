// Smart Agriculture Assistant Frontend Client Script

let breakdownChartInstance = null;
let allCropsCache = {};
let allSoilsCache = {};

document.addEventListener('DOMContentLoaded', async () => {
    lucide.createIcons();
    await fetchInitialData();
    // Run initial recommendation with defaults
    document.getElementById('recommendForm').dispatchEvent(new Event('submit'));
});

// Switch Tab Navigation
function switchTab(tabId) {
    document.querySelectorAll('.tab-view').forEach(el => {
        el.classList.add('hidden');
        el.classList.remove('active');
    });
    document.querySelectorAll('.nav-tab').forEach(el => {
        el.classList.remove('active');
        el.classList.add('text-slate-600');
    });

    const targetView = document.getElementById(`view-${tabId}`);
    const targetTab = document.getElementById(`tab-${tabId}`);

    if (targetView && targetTab) {
        targetView.classList.remove('hidden');
        targetView.classList.add('active');
        targetTab.classList.add('active');
        targetTab.classList.remove('text-slate-600');
    }
    lucide.createIcons();
}

// Preset loader for quick testing
function loadSamplePreset(presetType) {
    if (presetType === 'monsoon_clay') {
        document.getElementById('soil_type').value = 'Clay Loam';
        document.getElementById('season').value = 'Kharif';
        document.getElementById('temperature').value = 28;
        document.getElementById('temp-val').innerText = '28 °C';
        document.getElementById('rainfall').value = 1400;
        document.getElementById('rain-val').innerText = '1400 mm';
        document.getElementById('ph').value = 6.5;
        document.getElementById('ph-val').innerText = '6.5 pH';
        document.getElementById('nitrogen').value = 90;
        document.getElementById('phosphorus').value = 45;
        document.getElementById('potassium').value = 40;
    }
    document.getElementById('recommendForm').dispatchEvent(new Event('submit'));
}

// Fetch Initial Database
async function fetchInitialData() {
    try {
        const cropsRes = await fetch('/api/crops');
        if (cropsRes.ok) {
            const data = await cropsRes.json();
            allCropsCache = data.crops || {};
            renderEncyclopedia(allCropsCache);
        }

        const soilsRes = await fetch('/api/soils');
        if (soilsRes.ok) {
            const data = await soilsRes.json();
            allSoilsCache = data.soils || {};
            renderSoilProfiles(allSoilsCache);
        }
    } catch (e) {
        console.warn("Backend API not reachable yet; using standalone client engine.", e);
    }
}

// Handle Crop Recommendation Submission
async function handleRecommendationSubmit(event) {
    if (event) event.preventDefault();

    const payload = {
        soil_type: document.getElementById('soil_type').value,
        season: document.getElementById('season').value,
        temperature: parseFloat(document.getElementById('temperature').value),
        rainfall: parseFloat(document.getElementById('rainfall').value),
        ph: parseFloat(document.getElementById('ph').value),
        nitrogen: parseFloat(document.getElementById('nitrogen').value),
        phosphorus: parseFloat(document.getElementById('phosphorus').value),
        potassium: parseFloat(document.getElementById('potassium').value)
    };

    try {
        const res = await fetch('/api/recommend', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            const data = await res.json();
            displayRecommendations(data.recommendations);
            updateSoilAnalysisView(data.soil_analysis, payload);
        }
    } catch (err) {
        console.error("Error fetching recommendation:", err);
    }
}

// Display Recommendation Results
function displayRecommendations(recommendations) {
    if (!recommendations || recommendations.length === 0) return;

    const top = recommendations[0];

    // Update Top Match Spotlight Card
    document.getElementById('topMatchScore').innerText = `${top.score}%`;
    document.getElementById('topMatchIcon').innerText = top.icon || '🌾';
    document.getElementById('topMatchName').innerText = top.name;
    document.getElementById('topMatchCategory').innerText = top.category;
    document.getElementById('topMatchYield').innerText = `⚡ Expected Yield: ${top.details.yield}`;
    document.getElementById('topMatchWater').innerText = top.details.water_management;
    document.getElementById('topMatchFertilizer').innerText = top.details.fertilizer;

    // Render Factor Breakdown Chart
    renderBreakdownChart(top.breakdown);

    // Render Ranked List
    const rankedContainer = document.getElementById('rankedCropsList');
    rankedContainer.innerHTML = '';

    recommendations.slice(1, 8).forEach((item, index) => {
        const card = document.createElement('div');
        card.className = 'crop-card p-4 rounded-xl border border-slate-200 bg-slate-50 hover:bg-white hover:border-emerald-300 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3';

        const tierBadgeColor = item.tier_color === 'emerald' ? 'bg-emerald-100 text-emerald-800' :
                               (item.tier_color === 'blue' ? 'bg-blue-100 text-blue-800' :
                               (item.tier_color === 'amber' ? 'bg-amber-100 text-amber-800' : 'bg-rose-100 text-rose-800'));

        card.innerHTML = `
            <div class="flex items-center gap-3">
                <div class="text-2xl p-2 bg-white rounded-lg border border-slate-200 shadow-sm">${item.icon || '🌱'}</div>
                <div>
                    <h4 class="font-bold text-sm text-slate-900">${item.name}</h4>
                    <p class="text-xs text-slate-500">${item.category} • ${item.details.growth_duration}</p>
                </div>
            </div>
            <div class="flex items-center gap-3 self-end sm:self-center">
                <span class="text-[11px] font-semibold px-2.5 py-1 rounded-full ${tierBadgeColor}">${item.tier}</span>
                <span class="text-base font-extrabold text-slate-800 w-14 text-right">${item.score}%</span>
            </div>
        `;
        rankedContainer.appendChild(card);
    });

    lucide.createIcons();
}

// Render Suitability Chart with Chart.js
function renderBreakdownChart(breakdown) {
    const ctx = document.getElementById('breakdownChart');
    if (!ctx) return;

    if (breakdownChartInstance) {
        breakdownChartInstance.destroy();
    }

    const labels = ['Rainfall', 'Temperature', 'Soil Type', 'Season Match', 'Soil pH', 'NPK Nutrients'];
    const dataValues = [
        breakdown.rainfall,
        breakdown.temperature,
        breakdown.soil,
        breakdown.season,
        breakdown.ph,
        breakdown.npk
    ];

    breakdownChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Suitability Score (%)',
                data: dataValues,
                backgroundColor: [
                    'rgba(59, 130, 246, 0.75)',
                    'rgba(245, 158, 11, 0.75)',
                    'rgba(16, 185, 129, 0.75)',
                    'rgba(139, 92, 246, 0.75)',
                    'rgba(236, 72, 153, 0.75)',
                    'rgba(34, 197, 94, 0.75)'
                ],
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: { font: { size: 10 } }
                },
                x: {
                    ticks: { font: { size: 10 } }
                }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}

// Update Soil Health Tab View
function updateSoilAnalysisView(analysis, inputs) {
    if (!analysis) return;

    document.getElementById('stat-n').innerText = inputs.nitrogen;
    document.getElementById('stat-p').innerText = inputs.phosphorus;
    document.getElementById('stat-k').innerText = inputs.potassium;
    document.getElementById('stat-ph').innerText = inputs.ph;

    const nStatus = analysis.status.nitrogen.status;
    const pStatus = analysis.status.phosphorus.status;
    const kStatus = analysis.status.potassium.status;
    const phStatus = analysis.status.ph.status;

    document.getElementById('badge-n').innerText = nStatus;
    document.getElementById('badge-p').innerText = pStatus;
    document.getElementById('badge-k').innerText = kStatus;
    document.getElementById('badge-ph').innerText = phStatus;

    const adviceContainer = document.getElementById('fertilizerAdviceList');
    adviceContainer.innerHTML = '';

    // pH remedy
    if (analysis.status.ph.remedy) {
        const phBox = document.createElement('div');
        phBox.className = 'p-3 bg-purple-50 border border-purple-200 rounded-lg flex items-start gap-2.5';
        phBox.innerHTML = `
            <i data-lucide="test-tube" class="w-4 h-4 text-purple-600 mt-0.5 flex-shrink-0"></i>
            <div>
                <strong class="text-purple-900 block font-semibold">pH Conditioning (${analysis.status.ph.status}):</strong>
                <span class="text-purple-800 text-[11px]">${analysis.status.ph.remedy}</span>
            </div>
        `;
        adviceContainer.appendChild(phBox);
    }

    // Fertilizer recommendations
    analysis.fertilizer_recommendations.forEach(rec => {
        const item = document.createElement('div');
        item.className = 'p-3 bg-emerald-50 border border-emerald-200 rounded-lg flex items-start gap-2.5';
        item.innerHTML = `
            <i data-lucide="sparkles" class="w-4 h-4 text-emerald-600 mt-0.5 flex-shrink-0"></i>
            <span class="text-emerald-950 font-medium">${rec}</span>
        `;
        adviceContainer.appendChild(item);
    });

    lucide.createIcons();
}

// Handle Disease Diagnosis Query
async function handleDiseaseSubmit(event) {
    if (event) event.preventDefault();

    const crop = document.getElementById('disease_crop').value;
    const symptoms = document.getElementById('disease_symptoms').value;
    const resultsContainer = document.getElementById('diagnosisResults');

    if (!symptoms.trim()) {
        resultsContainer.innerHTML = `<div class="p-4 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-800 font-medium">Please describe symptoms or click one of the quick presets.</div>`;
        return;
    }

    try {
        const res = await fetch('/api/diagnose', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ crop, symptoms })
        });

        if (res.ok) {
            const data = await res.json();
            renderDiagnosisResults(data.diagnosis);
        }
    } catch (e) {
        console.error("Diagnosis fetch failed:", e);
    }
}

function setSymptomQuery(crop, query) {
    document.getElementById('disease_crop').value = crop;
    document.getElementById('disease_symptoms').value = query;
    handleDiseaseSubmit();
}

function renderDiagnosisResults(diagnosisList) {
    const container = document.getElementById('diagnosisResults');
    container.innerHTML = '';

    if (!diagnosisList || diagnosisList.length === 0) {
        container.innerHTML = `
            <div class="p-5 bg-white border border-slate-200 rounded-xl text-center text-slate-500 text-xs">
                No matching diseases found for the specified symptoms. Please consult a local agricultural extension officer.
            </div>
        `;
        return;
    }

    diagnosisList.forEach(diag => {
        const urgencyColor = diag.urgency === 'Critical' ? 'bg-rose-100 text-rose-800' : 'bg-amber-100 text-amber-800';
        const card = document.createElement('div');
        card.className = 'bg-white rounded-2xl shadow-sm border border-slate-200 p-6 space-y-4';
        card.innerHTML = `
            <div class="flex items-start justify-between border-b border-slate-100 pb-3">
                <div>
                    <span class="text-[11px] font-bold uppercase tracking-wider text-slate-500">${diag.crop}</span>
                    <h4 class="text-base font-extrabold text-slate-900 mt-0.5">${diag.diagnosis}</h4>
                </div>
                <div class="flex items-center gap-2">
                    <span class="text-xs px-2.5 py-0.5 rounded-full font-bold ${urgencyColor}">Urgency: ${diag.urgency}</span>
                    <span class="text-xs font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">${diag.confidence}% Match</span>
                </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                <div class="bg-rose-50/60 p-3.5 rounded-xl border border-rose-100">
                    <strong class="text-rose-900 block font-semibold mb-1 flex items-center gap-1.5">
                        <i data-lucide="shield-alert" class="w-3.5 h-3.5 text-rose-600"></i> Chemical Treatment
                    </strong>
                    <p class="text-rose-800 text-[11px] leading-relaxed">${diag.chemical_control}</p>
                </div>
                <div class="bg-emerald-50/60 p-3.5 rounded-xl border border-emerald-100">
                    <strong class="text-emerald-900 block font-semibold mb-1 flex items-center gap-1.5">
                        <i data-lucide="leaf" class="w-3.5 h-3.5 text-emerald-600"></i> Organic / Bio-Control
                    </strong>
                    <p class="text-emerald-800 text-[11px] leading-relaxed">${diag.organic_control}</p>
                </div>
            </div>

            <div class="bg-slate-50 p-3 rounded-xl border border-slate-200 text-xs">
                <strong class="text-slate-800 block font-semibold mb-1">🛡️ Preventive Protocol:</strong>
                <p class="text-slate-600 text-[11px]">${diag.preventive_tips}</p>
            </div>
        `;
        container.appendChild(card);
    });

    lucide.createIcons();
}

// Render Encyclopedia Grid
function renderEncyclopedia(crops) {
    const grid = document.getElementById('encyclopediaGrid');
    if (!grid) return;
    grid.innerHTML = '';

    Object.keys(crops).forEach(key => {
        const crop = crops[key];
        const card = document.createElement('div');
        card.className = 'crop-card bg-white rounded-2xl shadow-sm border border-slate-200 p-5 flex flex-col justify-between';
        card.innerHTML = `
            <div>
                <div class="flex items-center justify-between mb-3">
                    <span class="text-3xl">${crop.icon || '🌱'}</span>
                    <span class="text-[10px] uppercase font-bold px-2 py-0.5 bg-slate-100 text-slate-700 rounded-md">${crop.category}</span>
                </div>
                <h4 class="text-base font-bold text-slate-900 mb-1">${crop.name}</h4>
                <p class="text-xs text-emerald-700 font-medium mb-3">📅 Seasons: ${crop.season.join(', ')}</p>

                <div class="space-y-1.5 text-[11px] text-slate-600 border-t border-slate-100 pt-3">
                    <p><strong>🌡️ Temp:</strong> ${crop.min_temp}°C - ${crop.max_temp}°C (Opt: ${crop.optimal_temp}°C)</p>
                    <p><strong>🌧️ Rainfall:</strong> ${crop.min_rainfall} - ${crop.max_rainfall} mm</p>
                    <p><strong>🌱 Soil:</strong> ${crop.soil_types.join(', ')}</p>
                    <p><strong>⚡ Yield:</strong> ${crop.yield_potential}</p>
                </div>
            </div>

            <div class="mt-4 pt-3 border-t border-slate-100">
                <p class="text-[10px] text-slate-500 italic line-clamp-2">${crop.market_advice}</p>
            </div>
        `;
        grid.appendChild(card);
    });

    lucide.createIcons();
}

// Filter Encyclopedia
function filterEncyclopedia(query) {
    const q = query.toLowerCase();
    const filtered = {};
    Object.keys(allCropsCache).forEach(key => {
        const crop = allCropsCache[key];
        const text = `${crop.name} ${crop.category} ${crop.season.join(' ')} ${crop.soil_types.join(' ')}`.toLowerCase();
        if (text.includes(q)) {
            filtered[key] = crop;
        }
    });
    renderEncyclopedia(filtered);
}

// Render Soil Profiles
function renderSoilProfiles(soils) {
    const grid = document.getElementById('soilProfilesGrid');
    if (!grid) return;
    grid.innerHTML = '';

    Object.keys(soils).forEach(name => {
        const soil = soils[name];
        const card = document.createElement('div');
        card.className = 'p-4 rounded-xl border border-slate-200 bg-slate-50 space-y-2 text-xs';
        card.innerHTML = `
            <h4 class="font-bold text-slate-900 text-sm flex items-center justify-between">
                <span>${name}</span>
                <span class="text-[10px] bg-slate-200 text-slate-700 px-2 py-0.5 rounded font-normal">pH: ${soil.ph_typical}</span>
            </h4>
            <p class="text-slate-600 text-[11px]">${soil.characteristics}</p>
            <div class="pt-2 border-t border-slate-200/80">
                <strong class="text-slate-700 block mb-1">Suitable Crops:</strong>
                <div class="flex flex-wrap gap-1">
                    ${soil.best_crops.map(c => `<span class="bg-white border border-slate-200 px-1.5 py-0.5 rounded text-[10px] font-medium text-slate-700">${c}</span>`).join('')}
                </div>
            </div>
            <p class="text-[11px] text-emerald-800 font-medium pt-1">💡 <em>${soil.soil_enhancement}</em></p>
        `;
        grid.appendChild(card);
    });
}

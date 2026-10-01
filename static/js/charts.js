/**
 * Chart.js Integration Module for Smart Agriculture Assistant.
 * Renders interactive visual analytics for crop suitability, soil NPK, and environmental profiles.
 */

const chartInstances = {};

function destroyChart(id) {
  if (chartInstances[id]) {
    chartInstances[id].destroy();
    delete chartInstances[id];
  }
}

/**
 * Top Recommended Crops Comparison Bar Chart
 */
function renderTopCropsChart(canvasId, recommendations) {
  destroyChart(canvasId);
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;

  const labels = recommendations.map(r => `${r.icon || ''} ${r.crop_name}`);
  const data = recommendations.map(r => r.suitability_score);
  const colors = [
    'rgba(45, 106, 79, 0.85)',
    'rgba(82, 183, 136, 0.85)',
    'rgba(233, 196, 106, 0.85)'
  ];

  chartInstances[canvasId] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Model Suitability Score (%)',
        data: data,
        backgroundColor: colors.slice(0, data.length),
        borderColor: colors.map(c => c.replace('0.85', '1.0')),
        borderWidth: 1.5,
        borderRadius: 8
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: function(context) {
              return `Suitability: ${context.raw}%`;
            }
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          max: 100,
          ticks: {
            callback: value => `${value}%`,
            font: { family: 'Inter' }
          },
          grid: { color: 'rgba(0,0,0,0.05)' }
        },
        x: {
          grid: { display: false },
          ticks: { font: { family: 'Inter', weight: '600' } }
        }
      }
    }
  });
}

/**
 * Soil N-P-K Nutrient Balance Radar / Polar Area Chart
 */
function renderSoilNutrientChart(canvasId, n, p, k, ph) {
  destroyChart(canvasId);
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;

  chartInstances[canvasId] = new Chart(ctx, {
    type: 'radar',
    data: {
      labels: ['Nitrogen (N)', 'Phosphorus (P)', 'Potassium (K)', 'pH Level (x10)'],
      datasets: [
        {
          label: 'Your Farm Soil Levels',
          data: [n, p, k, ph * 10],
          backgroundColor: 'rgba(45, 106, 79, 0.25)',
          borderColor: '#2d6a4f',
          pointBackgroundColor: '#2d6a4f',
          pointBorderColor: '#fff',
          pointHoverBackgroundColor: '#fff',
          pointHoverBorderColor: '#2d6a4f',
          borderWidth: 2
        },
        {
          label: 'General Benchmark',
          data: [80, 50, 60, 65], // 6.5 pH * 10
          backgroundColor: 'rgba(233, 196, 106, 0.15)',
          borderColor: '#e9c46a',
          borderDash: [5, 5],
          pointRadius: 0,
          borderWidth: 1.5
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
          labels: { font: { family: 'Inter', size: 12 } }
        }
      },
      scales: {
        r: {
          angleLines: { color: 'rgba(0,0,0,0.08)' },
          grid: { color: 'rgba(0,0,0,0.06)' },
          suggestedMin: 0,
          suggestedMax: 150,
          ticks: { backdropColor: 'transparent', font: { size: 10 } }
        }
      }
    }
  });
}

/**
 * Feature Importances Bar Chart for Model Transparency
 */
function renderFeatureImportanceChart(canvasId, importances) {
  destroyChart(canvasId);
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;

  const labels = Object.keys(importances).map(k => k.toUpperCase());
  const data = Object.values(importances).map(v => (v * 100).toFixed(1));

  chartInstances[canvasId] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Relative Feature Importance (%)',
        data: data,
        backgroundColor: 'rgba(45, 106, 79, 0.8)',
        borderColor: '#1b4332',
        borderWidth: 1,
        borderRadius: 6
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: function(ctx) {
              return `Importance: ${ctx.raw}%`;
            }
          }
        }
      },
      scales: {
        x: {
          beginAtZero: true,
          max: 35,
          ticks: { callback: v => `${v}%` }
        },
        y: {
          grid: { display: false },
          ticks: { font: { weight: 'bold' } }
        }
      }
    }
  });
}

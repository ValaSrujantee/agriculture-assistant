/* Account and farm dashboard interactions. */
const accountApi = async (url, options = {}) => {
  const response = await fetch(url, options);
  const payload = await response.json().catch(() => ({}));
  if (!response.ok || payload.status !== "success") throw new Error(payload.message || "Request could not be completed.");
  return payload;
};
const formObject = form => Object.fromEntries(new FormData(form).entries());
const showAccountMessage = (element, message, success = false) => {
  if (!element) return;
  element.textContent = message;
  element.classList.toggle("success", success);
};
const escapeAccountText = text => String(text ?? "").replace(/[&<>"']/g, char => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[char]));

document.addEventListener("DOMContentLoaded", () => {
  const loginForm = document.getElementById("loginForm");
  if (loginForm) loginForm.addEventListener("submit", async event => {
    event.preventDefault();
    const message = document.getElementById("formMessage");
    try {
      await accountApi("/api/auth/login", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(formObject(loginForm))});
      location.assign("/farmer-dashboard");
    } catch (error) { showAccountMessage(message, error.message); }
  });

  const registerForm = document.getElementById("registerForm");
  if (registerForm) registerForm.addEventListener("submit", async event => {
    event.preventDefault();
    const message = document.getElementById("formMessage");
    try {
      await accountApi("/api/auth/register", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(formObject(registerForm))});
      location.assign("/farmer-dashboard");
    } catch (error) { showAccountMessage(message, error.message); }
  });

  const profileForm = document.getElementById("profileForm");
  if (profileForm) {
    accountApi("/api/profile").then(({profile}) => {
      for (const [key, value] of Object.entries(profile)) if (profileForm.elements[key]) profileForm.elements[key].value = value || "";
    }).catch(error => showAccountMessage(document.getElementById("formMessage"), error.message));
    profileForm.addEventListener("submit", async event => {
      event.preventDefault();
      try {
        await accountApi("/api/profile", {method:"PUT", headers:{"Content-Type":"application/json"}, body:JSON.stringify(formObject(profileForm))});
        showAccountMessage(document.getElementById("formMessage"), "Profile saved.", true);
      } catch (error) { showAccountMessage(document.getElementById("formMessage"), error.message); }
    });
  }

  document.querySelectorAll("[data-logout]").forEach(button => button.addEventListener("click", async () => {
    try { await accountApi("/api/auth/logout", {method:"POST"}); } finally { location.assign("/login"); }
  }));

  if (document.getElementById("farmList")) initFarmerDashboard();
});

async function initFarmerDashboard() {
  const farmList = document.getElementById("farmList");
  const reportList = document.getElementById("reportList");
  const form = document.getElementById("farmForm");
  const modal = document.getElementById("farmModal");
  const message = document.getElementById("farmFormMessage");
  let farms = [];
  let trendChart = null;

  const loadFarms = async () => {
    const payload = await accountApi("/api/farms");
    farms = payload.farms;
    farmList.replaceChildren();
    const select = document.getElementById("trendFarmSelect");
    select.innerHTML = '<option value="">Choose a farm</option>';
    if (!farms.length) {
      const empty = document.createElement("div"); empty.className = "card empty-state";
      empty.textContent = "You have not added a farm yet. Add one to keep assessments together."; farmList.append(empty);
      return;
    }
    farms.forEach(farm => {
      const card = document.createElement("article"); card.className = "card farm-card";
      const title = document.createElement("h3"); title.textContent = farm.name;
      const detail = document.createElement("p");
      detail.textContent = [farm.size ? `${farm.size} ${farm.size_unit || ""}`.trim() : "Size not provided", farm.village, farm.district, farm.state].filter(Boolean).join(" · ");
      const crop = document.createElement("p"); crop.textContent = [farm.irrigation_source && `Irrigation: ${farm.irrigation_source}`, farm.current_crop && `Current crop: ${farm.current_crop}`, farm.soil_type && `Soil: ${farm.soil_type}`].filter(Boolean).join(" · ") || "Add crop and soil details whenever you are ready.";
      const actions = document.createElement("div"); actions.className = "farm-actions";
      const analyze = document.createElement("a"); analyze.className = "btn btn-primary btn-sm"; analyze.href = `/dashboard?farm_id=${farm.id}`; analyze.textContent = "Analyze";
      const edit = document.createElement("button"); edit.className = "btn btn-secondary btn-sm"; edit.textContent = "Edit"; edit.addEventListener("click", () => openEdit(farm));
      const remove = document.createElement("button"); remove.className = "btn btn-secondary btn-sm danger-action"; remove.textContent = "Delete";
      remove.addEventListener("click", async () => {
        if (!confirm(`Delete ${farm.name}? Its linked report or assessment entries may no longer be attached to this farm.`)) return;
        try { await accountApi(`/api/farms/${farm.id}`, {method:"DELETE"}); await loadFarms(); await loadReports(); }
        catch (error) { alert(error.message); }
      });
      actions.append(analyze, edit, remove); card.append(title, detail, crop, actions); farmList.append(card);
      const option = document.createElement("option"); option.value = farm.id; option.textContent = farm.name; select.append(option);
    });
  };

  const loadReports = async () => {
    const {reports} = await accountApi("/api/soil-reports");
    reportList.replaceChildren();
    if (!reports.length) {
      const empty = document.createElement("div"); empty.className = "card empty-state"; empty.textContent = "No reports uploaded yet."; reportList.append(empty); return;
    }
    reports.forEach(report => {
      const card = document.createElement("article"); card.className = "card saved-report";
      const title = document.createElement("strong"); title.textContent = report.filename;
      const meta = document.createElement("span"); meta.textContent = `${report.farm_name || "No farm selected"} · ${report.uploaded_at} · ${report.verified ? "Verified" : "Needs verification"}`;
      const extracted = document.createElement("p");
      extracted.textContent = ["N","P","K","ph"].map(key => `${key}: ${report.values[key]?.value ?? "Not detected"}`).join(" · ");
      card.append(title, meta, extracted); reportList.append(card);
    });
  };

  const openEdit = farm => {
    form.reset();
    for (const [key, value] of Object.entries(farm)) if (form.elements[key]) form.elements[key].value = value ?? "";
    document.getElementById("farmModalTitle").textContent = "Edit farm";
    showAccountMessage(message, ""); modal.hidden = false;
  };
  const openNew = () => { form.reset(); document.getElementById("farmModalTitle").textContent = "Add a farm"; showAccountMessage(message, ""); modal.hidden = false; };
  document.getElementById("newFarmBtn").addEventListener("click", openNew);
  document.getElementById("closeFarmModal").addEventListener("click", () => modal.hidden = true);
  document.getElementById("cancelFarmBtn").addEventListener("click", () => modal.hidden = true);
  modal.addEventListener("click", event => { if (event.target === modal) modal.hidden = true; });
  form.addEventListener("submit", async event => {
    event.preventDefault();
    const data = formObject(form); const id = data.id; delete data.id;
    try {
      await accountApi(id ? `/api/farms/${id}` : "/api/farms", {method:id ? "PUT" : "POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(data)});
      modal.hidden = true; await loadFarms();
    } catch (error) { showAccountMessage(message, error.message); }
  });
  document.getElementById("trendFarmSelect").addEventListener("change", async event => {
    const farmId = event.target.value;
    if (!farmId) return;
    try {
      const {trend} = await accountApi(`/api/farms/${farmId}/soil-trend`);
      const empty = document.getElementById("trendEmpty");
      if (trend.length < 2 || typeof Chart === "undefined") { empty.hidden = false; return; }
      empty.hidden = true;
      if (trendChart) trendChart.destroy();
      trendChart = new Chart(document.getElementById("soilTrendChart"), {type:"line", data:{labels:trend.map(row => row.timestamp), datasets:[
        {label:"Nitrogen", data:trend.map(row => row.n_val), borderColor:"#27864a", tension:.25},
        {label:"Phosphorus", data:trend.map(row => row.p_val), borderColor:"#d39727", tension:.25},
        {label:"Potassium", data:trend.map(row => row.k_val), borderColor:"#4382b7", tension:.25},
        {label:"pH", data:trend.map(row => row.ph), borderColor:"#9653ad", tension:.25}
      ]}, options:{responsive:true, maintainAspectRatio:false, interaction:{mode:"index", intersect:false}}});
    } catch (error) { showAccountMessage(document.getElementById("trendEmpty"), error.message); }
  });
  try { await loadFarms(); await loadReports(); }
  catch (error) { farmList.textContent = error.message; reportList.textContent = error.message; }
}

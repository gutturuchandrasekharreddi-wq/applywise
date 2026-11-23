const $ = (selector) => document.querySelector(selector);
const statuses = ["saved", "applied", "interview", "offer", "rejected", "withdrawn"];
const labels = { saved: "Saved", applied: "Applied", interview: "Interview", offer: "Offer", rejected: "Rejected", withdrawn: "Withdrawn" };
const colors = { saved: "#b6c6b6", applied: "#83a18b", interview: "#9cabc0", offer: "#c3ad7b", rejected: "#c49d9d", withdrawn: "#c7ceca" };
const escapeHtml = (value = "") => String(value).replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]);
const dateLabel = (value) => value ? new Date(`${value}T00:00:00`).toLocaleDateString(undefined, { month: "short", day: "numeric" }) : "—";
const toast = (message) => { const node = $("#toast"); node.textContent = message; node.classList.add("show"); setTimeout(() => node.classList.remove("show"), 2600); };

async function request(url, options = {}) {
  const response = await fetch(url, { ...options, headers: { "Content-Type": "application/json", ...options.headers } });
  if (!response.ok) { const body = await response.json().catch(() => ({})); throw new Error(body.detail || "Something went wrong. Please try again."); }
  return response.status === 204 ? null : response.json();
}

function companyMark(company) { return `<span class="company-mark">${escapeHtml((company || "?").trim().slice(0, 1).toUpperCase())}</span>`; }
function renderPipeline(grouped) {
  const stages = ["saved", "applied", "interview", "offer"];
  $("#pipeline").innerHTML = stages.map((status) => `<div class="pipeline-step" data-status="${status}"><div class="step-top"><i class="step-dot"></i>${labels[status]}</div><div class="step-count">${grouped[status] || 0}</div></div>`).join("");
  const total = stages.reduce((sum, status) => sum + (grouped[status] || 0), 0);
  $("#pipeline-bar").innerHTML = stages.map((status) => `<span style="width:${total ? ((grouped[status] || 0) / total * 100) : 0}%;background:${colors[status]}"></span>`).join("");
  $("#pipeline-legend").innerHTML = [`${grouped.saved || 0} saved`, `${grouped.applied || 0} applied`, `${grouped.interview || 0} interviews`, `${grouped.offer || 0} offers`].map((text, index) => `<span><i style="background:${Object.values(colors)[index]}"></i>${text}</span>`).join("");
}

function renderFollowups(items) {
  if (!items.length) { $("#followup-list").innerHTML = `<div class="follow-empty"><span>✓</span><span>You're all caught up. Your next follow-up will show up here.</span></div>`; return; }
  $("#followup-list").innerHTML = items.map((item) => `<div class="follow-item">${companyMark(item.company)}<div class="follow-main"><strong>${escapeHtml(item.company)} · ${escapeHtml(item.role)}</strong><small>${item.follow_up_on < new Date().toISOString().slice(0, 10) ? "Past due" : "Due today"} · ${dateLabel(item.follow_up_on)}</small></div><span class="follow-date">Follow up</span></div>`).join("");
}

function renderApplications(items) {
  $("#nav-count").textContent = items.length;
  $("#empty-state").style.display = items.length ? "none" : "block";
  $("#application-rows").innerHTML = items.map((item) => `<tr><td><div class="company-cell">${companyMark(item.company)}<div class="company-info"><strong>${escapeHtml(item.company)}</strong><small>${escapeHtml(item.role)}${item.job_url ? ` · <a href="${escapeHtml(item.job_url)}" target="_blank" rel="noopener">View role ↗</a>` : ""}</small></div></div></td><td><span class="status-pill status-${item.status}">${labels[item.status] || escapeHtml(item.status)}</span></td><td>${dateLabel(item.applied_on)}</td><td class="${item.follow_up_on && item.follow_up_on <= new Date().toISOString().slice(0, 10) ? "due-date" : ""}">${dateLabel(item.follow_up_on)}</td><td>${escapeHtml(item.location || "—")}</td><td><div class="row-actions"><button class="row-action" title="Advance status" aria-label="Advance status" data-advance="${item.id}">↗</button><button class="row-action" title="Delete application" aria-label="Delete application" data-delete="${item.id}">×</button></div></td></tr>`).join("");
}

async function loadDashboard() {
  try {
    const [overview, applications] = await Promise.all([request("/api/overview"), request("/api/applications")]);
    $("#metric-total").textContent = overview.total;
    $("#metric-progress").textContent = (overview.by_status.saved || 0) + (overview.by_status.applied || 0) + (overview.by_status.interview || 0);
    $("#metric-response").textContent = overview.response_rate;
    $("#metric-followups").textContent = overview.follow_up_count;
    renderPipeline(overview.by_status);
    renderFollowups(overview.follow_ups);
    renderApplications(applications);
  } catch (error) { toast(error.message); }
}

function openDialog(id) { $(`#${id}`).showModal(); }
document.querySelectorAll("[data-close]").forEach((button) => button.addEventListener("click", () => $(`#${button.dataset.close}`).close()));
$("#open-create").addEventListener("click", () => openDialog("application-dialog"));
$("#open-create-table").addEventListener("click", () => openDialog("application-dialog"));
$("#empty-create").addEventListener("click", () => openDialog("application-dialog"));
$("#open-match").addEventListener("click", () => openDialog("match-dialog"));
$("#open-match-top").addEventListener("click", () => openDialog("match-dialog"));
$("#refresh").addEventListener("click", loadDashboard);
$("#today-label").textContent = new Date().toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" });

$("#application-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const body = Object.fromEntries([...form.entries()].filter(([, value]) => value !== ""));
  try { await request("/api/applications", { method: "POST", body: JSON.stringify(body) }); event.currentTarget.reset(); $("#application-dialog").close(); toast("Application added to your pipeline."); await loadDashboard(); }
  catch (error) { toast(error.message); }
});

async function filterApplications() {
  const params = new URLSearchParams();
  if ($("#search").value.trim()) params.set("q", $("#search").value.trim());
  if ($("#status-filter").value) params.set("status", $("#status-filter").value);
  try { renderApplications(await request(`/api/applications?${params}`)); } catch (error) { toast(error.message); }
}
$("#search").addEventListener("input", filterApplications);
$("#status-filter").addEventListener("change", filterApplications);

$("#application-rows").addEventListener("click", async (event) => {
  const advance = event.target.closest("[data-advance]");
  const remove = event.target.closest("[data-delete]");
  try {
    if (advance) {
      const rows = await request("/api/applications");
      const item = rows.find((row) => row.id === Number(advance.dataset.advance));
      const flow = ["saved", "applied", "interview", "offer"];
      const currentIndex = flow.indexOf(item.status);
      if (currentIndex < 0 || currentIndex >= flow.length - 1) { toast("This application can't be advanced to another stage."); return; }
      const next = flow[currentIndex + 1];
      await request(`/api/applications/${item.id}`, { method: "PATCH", body: JSON.stringify({ status: next }) });
      toast(`Moved to ${labels[next].toLowerCase()}.`);
    }
    if (remove && confirm("Remove this application from your tracker?")) {
      await request(`/api/applications/${remove.dataset.delete}`, { method: "DELETE" }); toast("Application removed.");
    }
    await loadDashboard();
  } catch (error) { toast(error.message); }
});

$("#match-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const button = event.currentTarget.querySelector("button[type=submit]");
  button.disabled = true; button.innerHTML = "Comparing…";
  try {
    const result = await request("/api/match", { method: "POST", body: JSON.stringify(Object.fromEntries(form.entries())) });
    const chips = (items, missing = false) => items.length ? items.map((term) => `<span class="term-chip ${missing ? "missing" : ""}">${escapeHtml(term)}</span>`).join("") : `<span class="metric-note">No terms to show</span>`;
    const resultNode = $("#match-result");
    resultNode.innerHTML = `<div class="result-top"><div class="score-ring" style="--score:${result.score * 3.6}deg"><span>${result.score}%</span></div><div><strong>${result.score >= 70 ? "Strong overlap" : result.score >= 40 ? "Some shared ground" : "Room to tailor"}</strong><p>A directional comparison of terms—not a judgment of your fit.</p></div></div><div class="term-groups"><div class="term-group"><h3>Already in your resume</h3><div class="term-list">${chips(result.matched_terms)}</div></div><div class="term-group"><h3>Worth addressing if relevant</h3><div class="term-list">${chips(result.missing_terms, true)}</div></div></div>`;
    resultNode.hidden = false;
  } catch (error) { toast(error.message); }
  finally { button.disabled = false; button.innerHTML = "Compare text <span>→</span>"; }
});

loadDashboard();

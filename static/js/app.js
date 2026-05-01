class EmailCampaignApp {
  constructor() {
    this.state = {
      campaignRunning: false,
      leadsUploaded: false,
      historyPage: 1,
      config: { daily_limit: 50, delay_seconds: 30 },
    };
    this.pollInterval = null;
    this.init();
  }

  init() {
    this.setupNav();
    this.checkAuthStatus();
    this.loadConfig();
    this.loadTemplates();
    this.setupDragDrop();
  }

  // ── Navigation ──────────────────────────────────────────────────────────

  setupNav() {
    document.querySelectorAll(".nav-btn").forEach((btn) => {
      btn.addEventListener("click", () => this.switchView(btn.dataset.view));
    });
  }

  switchView(name) {
    document.querySelectorAll(".view").forEach((v) => v.classList.remove("active"));
    document.querySelectorAll(".nav-btn").forEach((b) => b.classList.remove("active"));
    document.getElementById(`${name}-view`).classList.add("active");
    document.querySelector(`[data-view="${name}"]`).classList.add("active");
    if (name === "history") this.loadHistory(1);
    if (name === "settings") this.renderAuthDetail();
    if (name === "templates") this.renderTemplates();
  }

  // ── Auth ────────────────────────────────────────────────────────────────

  async checkAuthStatus() {
    try {
      const data = await this.apiFetch("/api/auth/status");
      const badge = document.getElementById("auth-status");
      if (data.authenticated) {
        badge.textContent = `✓ ${data.email || "Connected"}`;
        badge.className = "auth-badge auth-ok";
      } else if (!data.credentials_exist) {
        badge.textContent = "⚠ No credentials.json";
        badge.className = "auth-badge auth-fail";
      } else {
        badge.textContent = "⚠ Not authenticated";
        badge.className = "auth-badge auth-fail";
      }
      this._authData = data;
    } catch (e) {
      document.getElementById("auth-status").textContent = "⚠ Auth error";
    }
  }

  renderAuthDetail() {
    const d = this._authData || {};
    const el = document.getElementById("auth-detail");
    if (d.authenticated) {
      el.innerHTML = `<span style="color:#48bb78">✓ Authenticated as ${d.email || "unknown"}</span>`;
    } else if (!d.credentials_exist) {
      el.innerHTML = `<span style="color:#fc8181">✗ credentials.json not found. Place it in the project folder.</span>`;
    } else {
      el.innerHTML = `<span style="color:#f6e05e">⚠ Token missing or expired. Click below to authenticate.</span>`;
    }
  }

  async initiateAuth() {
    this.showToast("Opening OAuth flow… check your browser.", "warning");
    try {
      const data = await this.apiFetch("/api/auth/initiate", { method: "POST" });
      if (data.success) {
        this.showToast("Authentication complete!", "success");
        this.checkAuthStatus();
      } else {
        this.showToast(data.error || "Auth failed", "error");
      }
    } catch (e) {
      this.showToast("Auth request failed: " + e.message, "error");
    }
  }

  // ── Upload ──────────────────────────────────────────────────────────────

  setupDragDrop() {
    const area = document.getElementById("upload-area");
    area.addEventListener("dragover", (e) => { e.preventDefault(); area.style.borderColor = "#3b82f6"; });
    area.addEventListener("dragleave", () => { area.style.borderColor = ""; });
    area.addEventListener("drop", (e) => {
      e.preventDefault();
      area.style.borderColor = "";
      const file = e.dataTransfer.files[0];
      if (file) this.uploadFile(file);
    });
  }

  handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) this.uploadFile(file);
  }

  async uploadFile(file) {
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await fetch("/api/upload", { method: "POST", body: formData });
      const data = await res.json();
      if (data.success) {
        this.state.leadsUploaded = true;
        this.renderUploadResult(data);
        this.showToast(`Loaded ${data.total_leads} leads (${data.new_leads} new)`, "success");
        document.getElementById("stat-total").textContent = data.total_leads;
      } else {
        this.showToast(data.error, "error");
      }
    } catch (e) {
      this.showToast("Upload failed: " + e.message, "error");
    }
  }

  renderUploadResult(data) {
    document.getElementById("upload-result").style.display = "block";
    document.getElementById("up-new").textContent = `${data.new_leads} new`;
    document.getElementById("up-dup").textContent = `${data.duplicate_leads} duplicates`;
    document.getElementById("up-total").textContent = `${data.total_leads} total`;
    document.getElementById("up-time").textContent = `~${data.estimated_minutes} min`;

    const tbody = document.getElementById("preview-body");
    tbody.innerHTML = "";
    (data.preview || []).forEach((lead) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${this.esc(lead.name)}</td>
        <td>${this.esc(lead.email)}</td>
        <td>${this.esc(lead.pitch_type)}</td>
        <td>${this.esc(lead.price)}</td>
        <td>${lead.is_duplicate ? '<span class="dup-tag">⚠ Duplicate</span>' : '<span class="new-tag">✓ New</span>'}</td>
      `;
      tbody.appendChild(tr);
    });
  }

  // ── Campaign ────────────────────────────────────────────────────────────

  async startCampaign() {
    if (!this.state.leadsUploaded) {
      this.showToast("Please upload a CSV file first", "warning");
      this.switchView("upload");
      return;
    }
    try {
      const data = await this.apiFetch("/api/campaign/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(this.state.config),
      });
      if (data.success) {
        this.state.campaignRunning = true;
        document.getElementById("btn-start").style.display = "none";
        document.getElementById("btn-stop").style.display = "inline-block";
        this.showMsg("Campaign running…");
        this.startPolling();
      } else {
        this.showToast(data.error, "error");
      }
    } catch (e) {
      this.showToast("Failed to start: " + e.message, "error");
    }
  }

  async stopCampaign() {
    try {
      await this.apiFetch("/api/campaign/stop", { method: "POST" });
      this.showToast("Stop signal sent", "warning");
    } catch (e) {
      this.showToast("Stop failed: " + e.message, "error");
    }
  }

  // ── Progress polling ────────────────────────────────────────────────────

  startPolling() {
    this.pollInterval = setInterval(() => this.fetchProgress(), 2000);
  }

  stopPolling() {
    if (this.pollInterval) { clearInterval(this.pollInterval); this.pollInterval = null; }
  }

  async fetchProgress() {
    try {
      const data = await this.apiFetch("/api/progress");
      this.renderProgress(data);
      if (["completed", "stopped", "error"].includes(data.state)) {
        this.stopPolling();
        this.state.campaignRunning = false;
        document.getElementById("btn-start").style.display = "inline-block";
        document.getElementById("btn-stop").style.display = "none";
        const msgs = { completed: "Campaign completed!", stopped: "Campaign stopped.", error: "Campaign error: " + (data.error_message || "") };
        this.showToast(msgs[data.state], data.state === "completed" ? "success" : "warning");
        this.hideMsg();
      }
    } catch (e) { /* ignore transient errors */ }
  }

  renderProgress(p) {
    document.getElementById("progress-bar").style.width = `${p.percentage || 0}%`;
    document.getElementById("progress-pct").textContent = `${p.percentage || 0}%`;
    document.getElementById("stat-sent").textContent = p.sent_count;
    document.getElementById("stat-failed").textContent = p.failed_count;
    document.getElementById("stat-skipped").textContent = p.skipped_count;
    document.getElementById("stat-total").textContent = p.total_leads;

    const stateLabels = { idle: "Idle", running: "Running…", stopped: "Stopped", completed: "Completed", error: "Error" };
    document.getElementById("campaign-status-label").textContent = stateLabels[p.state] || p.state;

    if (p.current_lead) {
      document.getElementById("current-lead-display").textContent =
        `Sending to: ${p.current_lead.name} (${p.current_lead.email})`;
    } else {
      document.getElementById("current-lead-display").textContent = "";
    }

    // Success rate
    const total = p.sent_count + p.failed_count;
    const rate = total > 0 ? Math.round((p.sent_count / total) * 100) + "%" : "—";
    document.getElementById("stat-rate").textContent = rate;

    // Remaining
    const remaining = this.state.config.daily_limit - p.sent_count;
    document.getElementById("stat-remaining").textContent = remaining > 0 ? remaining : 0;
  }

  // ── History ─────────────────────────────────────────────────────────────

  async loadHistory(page = 1) {
    this.state.historyPage = page;
    try {
      const data = await this.apiFetch(`/api/history?page=${page}&per_page=50`);
      document.getElementById("history-total").textContent = `${data.total_count} total`;
      const tbody = document.getElementById("history-body");
      tbody.innerHTML = "";
      if (data.emails.length === 0) {
        tbody.innerHTML = `<tr><td colspan="3" style="text-align:center;color:#64748b;padding:24px">No emails sent yet</td></tr>`;
      } else {
        data.emails.forEach((item, i) => {
          const tr = document.createElement("tr");
          tr.innerHTML = `<td>${(page - 1) * 50 + i + 1}</td><td>${this.esc(item.email)}</td><td>${this.esc(item.timestamp)}</td>`;
          tbody.appendChild(tr);
        });
      }
      this.renderPagination(data.page, data.total_pages);
    } catch (e) {
      this.showToast("Failed to load history", "error");
    }
  }

  renderPagination(current, total) {
    const el = document.getElementById("pagination");
    el.innerHTML = "";
    for (let i = 1; i <= total; i++) {
      const btn = document.createElement("button");
      btn.className = "page-btn" + (i === current ? " active" : "");
      btn.textContent = i;
      btn.onclick = () => this.loadHistory(i);
      el.appendChild(btn);
    }
  }

  // ── Settings ────────────────────────────────────────────────────────────

  async loadConfig() {
    try {
      const data = await this.apiFetch("/api/config");
      this.state.config = data;
      document.getElementById("cfg-daily-limit").value = data.daily_limit;
      document.getElementById("cfg-delay").value = data.delay_seconds;
      document.getElementById("stat-remaining").textContent = data.daily_limit;
    } catch (e) { /* use defaults */ }
  }

  async saveConfig() {
    const daily_limit = parseInt(document.getElementById("cfg-daily-limit").value);
    const delay_seconds = parseInt(document.getElementById("cfg-delay").value);
    const errEl = document.getElementById("cfg-error");
    errEl.style.display = "none";
    try {
      const data = await this.apiFetch("/api/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ daily_limit, delay_seconds }),
      });
      if (data.success) {
        this.state.config = data.config;
        this.showToast("Settings saved!", "success");
      } else {
        errEl.textContent = data.error;
        errEl.style.display = "block";
      }
    } catch (e) {
      this.showToast("Save failed: " + e.message, "error");
    }
  }

  // ── Templates ───────────────────────────────────────────────────────────

  async loadTemplates() {
    try {
      const data = await this.apiFetch("/api/templates");
      this.state.templates = data.templates || [];
    } catch (e) {
      this.state.templates = [];
    }
  }

  renderTemplates() {
    const list = document.getElementById("templates-list");
    list.innerHTML = "";
    if (!this.state.templates || this.state.templates.length === 0) {
      list.innerHTML = `<p style="color:#64748b;text-align:center;padding:40px">No templates yet. Create one above!</p>`;
      return;
    }
    this.state.templates.forEach((tpl) => {
      const card = document.createElement("div");
      card.className = "template-card" + (tpl.is_default ? " default" : "");
      card.innerHTML = `
        <div class="template-header">
          <span class="template-name">${this.esc(tpl.name)}</span>
          ${tpl.is_default ? '<span class="template-badge">✓ Default</span>' : ''}
        </div>
        <div class="template-subject"><strong>Subject:</strong> ${this.esc(tpl.subject)}</div>
        <div class="template-body">${this.esc(tpl.body)}</div>
        <div class="template-actions">
          ${!tpl.is_default ? `<button class="btn-small btn-set-default" onclick="app.setDefaultTemplate('${tpl.id}')">Set as Default</button>` : ''}
          <button class="btn-small btn-delete" onclick="app.deleteTemplate('${tpl.id}')">Delete</button>
        </div>
      `;
      list.appendChild(card);
    });
  }

  showNewTemplateForm() {
    document.getElementById("new-template-form").style.display = "block";
    document.getElementById("tpl-name").value = "";
    document.getElementById("tpl-subject").value = "";
    document.getElementById("tpl-body").value = "";
  }

  hideNewTemplateForm() {
    document.getElementById("new-template-form").style.display = "none";
  }

  async saveNewTemplate() {
    const name = document.getElementById("tpl-name").value.trim();
    const subject = document.getElementById("tpl-subject").value.trim();
    const body = document.getElementById("tpl-body").value.trim();
    if (!name || !subject || !body) {
      this.showToast("All fields are required", "warning");
      return;
    }
    try {
      const data = await this.apiFetch("/api/templates", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, subject, body }),
      });
      if (data.success) {
        this.showToast("Template created!", "success");
        this.hideNewTemplateForm();
        await this.loadTemplates();
        this.renderTemplates();
      } else {
        this.showToast(data.error, "error");
      }
    } catch (e) {
      this.showToast("Failed to create template: " + e.message, "error");
    }
  }

  async setDefaultTemplate(id) {
    try {
      const data = await this.apiFetch(`/api/templates/${id}/set-default`, { method: "POST" });
      if (data.success) {
        this.showToast("Default template updated!", "success");
        await this.loadTemplates();
        this.renderTemplates();
      } else {
        this.showToast(data.error, "error");
      }
    } catch (e) {
      this.showToast("Failed to set default: " + e.message, "error");
    }
  }

  async deleteTemplate(id) {
    if (!confirm("Delete this template?")) return;
    try {
      const data = await this.apiFetch(`/api/templates/${id}`, { method: "DELETE" });
      if (data.success) {
        this.showToast("Template deleted", "success");
        await this.loadTemplates();
        this.renderTemplates();
      } else {
        this.showToast(data.error, "error");
      }
    } catch (e) {
      this.showToast("Failed to delete: " + e.message, "error");
    }
  }

  // ── Helpers ─────────────────────────────────────────────────────────────

  async apiFetch(url, options = {}) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 10000);
    try {
      const res = await fetch(url, { ...options, signal: controller.signal });
      clearTimeout(timeout);
      return await res.json();
    } catch (e) {
      clearTimeout(timeout);
      if (e.name === "AbortError") throw new Error("Server not responding");
      throw e;
    }
  }

  showToast(msg, type = "success") {
    const el = document.createElement("div");
    el.className = `toast toast-${type}`;
    el.textContent = msg;
    document.getElementById("toast-container").appendChild(el);
    setTimeout(() => el.remove(), 5000);
  }

  showMsg(text) {
    const el = document.getElementById("campaign-message");
    el.textContent = text;
    el.style.display = "block";
  }

  hideMsg() {
    document.getElementById("campaign-message").style.display = "none";
  }

  esc(str) {
    return String(str || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }
}

document.addEventListener("DOMContentLoaded", () => { window.app = new EmailCampaignApp(); });

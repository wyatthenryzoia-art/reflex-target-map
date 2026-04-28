// Static-site filtering, search, sort. Reads /assets/data.json (relative).
(function () {
  const VERTICAL_LABELS = {
    humanoid_general: "Humanoid (general)",
    humanoid_industrial: "Humanoid (industrial)",
    mobile_manipulator_warehouse: "Mobile manipulator (warehouse)",
    mobile_manipulator_other: "Mobile manipulator (other)",
    drone_aerial: "Drone / aerial",
    agriculture: "Agriculture",
    defense_dual_use: "Defense (dual-use)",
    surgical_medical: "Surgical / medical",
    last_mile_delivery: "Last-mile delivery",
    cleaning_janitorial: "Cleaning / janitorial",
    consumer_home: "Consumer / home",
    research_only: "Research only",
  };

  const REGION_RANK = { california: 0, us_other: 1, international: 2, "": 3 };

  const els = {
    vertical: document.getElementById("f-vertical"),
    region: document.getElementById("f-region"),
    spend: document.getElementById("f-spend"),
    search: document.getElementById("f-search"),
    tbody: document.getElementById("rows"),
    count: document.getElementById("count"),
    modalBg: document.getElementById("modal-bg"),
    modalContent: document.getElementById("modal-content"),
  };

  let data = [];
  let sortKey = "default"; // region-then-score
  let sortDir = -1;

  fetch("./assets/data.json").then((r) => r.json()).then((rows) => {
    data = rows;
    populateVerticalFilter();
    bindEvents();
    render();
  });

  function populateVerticalFilter() {
    const counts = {};
    for (const r of data) if (r.vertical) counts[r.vertical] = (counts[r.vertical] || 0) + 1;
    const verticals = Object.keys(counts).sort((a, b) => counts[b] - counts[a]);
    for (const v of verticals) {
      const opt = document.createElement("option");
      opt.value = v;
      opt.textContent = `${VERTICAL_LABELS[v] || v} (${counts[v]})`;
      els.vertical.appendChild(opt);
    }
  }

  function bindEvents() {
    [els.vertical, els.region, els.spend].forEach((el) => el.addEventListener("change", render));
    els.search.addEventListener("input", render);
    document.querySelectorAll("th[data-key]").forEach((th) => {
      th.addEventListener("click", () => {
        const k = th.dataset.key;
        if (sortKey === k) sortDir *= -1;
        else { sortKey = k; sortDir = ["score", "pain_score"].includes(k) ? -1 : 1; }
        render();
      });
    });
    els.modalBg.addEventListener("click", (e) => { if (e.target === els.modalBg) closeModal(); });
  }

  function render() {
    const vertical = els.vertical.value;
    const region = els.region.value;
    const spend = els.spend.value;
    const q = els.search.value.trim().toLowerCase();

    let filtered = data.filter((r) => {
      if (vertical && r.vertical !== vertical) return false;
      if (region && r.region !== region) return false;
      if (spend && (r.spend_tier || "").toLowerCase() !== spend.toLowerCase()) return false;
      if (q) {
        const hay = [r.company_name, r.buyer_name, r.vertical, r.one_line_description, r.hq_display].filter(Boolean).join(" ").toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });

    if (sortKey === "default") {
      filtered.sort((a, b) => (REGION_RANK[a.region] ?? 9) - (REGION_RANK[b.region] ?? 9) || b.score - a.score || a.company_name.localeCompare(b.company_name));
    } else {
      filtered.sort((a, b) => {
        let av = a[sortKey] ?? "";
        let bv = b[sortKey] ?? "";
        if (typeof av === "number" || typeof bv === "number") {
          av = Number(av) || 0; bv = Number(bv) || 0;
          return (av - bv) * sortDir;
        }
        return String(av).localeCompare(String(bv)) * sortDir;
      });
    }

    document.querySelectorAll("th[data-key]").forEach((th) => {
      th.classList.remove("sorted-asc", "sorted-desc");
      if (th.dataset.key === sortKey) th.classList.add(sortDir === 1 ? "sorted-asc" : "sorted-desc");
    });

    els.tbody.innerHTML = filtered.map(rowHTML).join("");
    els.count.textContent = `Showing ${filtered.length} of ${data.length} companies.`;

    document.querySelectorAll(".sources-link").forEach((a) => {
      a.addEventListener("click", (e) => {
        e.preventDefault();
        openModal(a.dataset.id);
      });
    });
  }

  function rowHTML(r) {
    const vlaBadge = r.vla_classification ? `<span class="badge badge-${r.vla_classification.replace(/_/g, "-")}">${r.vla_classification.replace("vla_", "")}</span>` : "";
    const company = r.dossier_url
      ? `<a href="${r.dossier_url}">${escape(r.company_name)}</a>`
      : escape(r.company_name);
    const buyer = r.buyer_linkedin_url
      ? `<a href="${r.buyer_linkedin_url}" target="_blank" rel="noopener">${escape(r.buyer_name || "—")}</a>`
      : escape(r.buyer_name || "—");
    const hqClass = r.region === "california" ? "hq-ca" : (r.region === "us_other" ? "hq-us" : "hq-intl");
    const rowClass = r.has_dossier ? "row-priority" : "";
    return `<tr class="${rowClass}">
      <td class="col-company" data-label="Company">${company}<div class="muted" style="font-size:12px">${escape(r.one_line_description || "")}</div></td>
      <td data-label="Vertical">${VERTICAL_LABELS[r.vertical] || escape(r.vertical || "—")}</td>
      <td data-label="HQ" class="${hqClass}">${escape(r.hq_display || "—")}</td>
      <td data-label="Score" class="score">${r.score ?? ""}</td>
      <td data-label="VLA">${vlaBadge}</td>
      <td data-label="Pain"><span class="pain pain-${r.pain_score ?? 0}">${r.pain_score ?? "—"}</span></td>
      <td data-label="Spend">${(r.spend_tier || "—").toUpperCase()}</td>
      <td data-label="Buyer">${buyer}</td>
      <td data-label="Sources"><a href="#" class="sources-link" data-id="${r.id}">view</a></td>
    </tr>`;
  }

  function openModal(id) {
    const row = data.find((r) => r.id === id);
    if (!row) return;
    const urls = (row.source_urls || []).map((u) => `<li><a href="${u}" target="_blank" rel="noopener">${u}</a></li>`).join("");
    els.modalContent.innerHTML = `
      <h3>${escape(row.company_name)} — sources</h3>
      <ul>${urls || "<li class=muted>(no sources recorded)</li>"}</ul>
      <button onclick="document.getElementById('modal-bg').classList.remove('open')">Close</button>
    `;
    els.modalBg.classList.add("open");
  }
  function closeModal() { els.modalBg.classList.remove("open"); }

  function escape(s) {
    return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  }
})();

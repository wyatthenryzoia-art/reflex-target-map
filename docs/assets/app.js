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

  const els = {
    tier: document.getElementById("f-tier"),
    vertical: document.getElementById("f-vertical"),
    spend: document.getElementById("f-spend"),
    search: document.getElementById("f-search"),
    tbody: document.getElementById("rows"),
    count: document.getElementById("count"),
    modalBg: document.getElementById("modal-bg"),
    modalContent: document.getElementById("modal-content"),
  };

  let data = [];
  let sortKey = "score";
  let sortDir = -1; // -1 desc, 1 asc

  fetch("./assets/data.json").then((r) => r.json()).then((rows) => {
    data = rows;
    populateVerticalFilter();
    bindEvents();
    render();
  });

  function populateVerticalFilter() {
    const verticals = Array.from(new Set(data.map((r) => r.vertical).filter(Boolean))).sort();
    for (const v of verticals) {
      const opt = document.createElement("option");
      opt.value = v;
      opt.textContent = VERTICAL_LABELS[v] || v;
      els.vertical.appendChild(opt);
    }
  }

  function bindEvents() {
    [els.tier, els.vertical, els.spend].forEach((el) => el.addEventListener("change", render));
    els.search.addEventListener("input", render);
    document.querySelectorAll("th[data-key]").forEach((th) => {
      th.addEventListener("click", () => {
        const k = th.dataset.key;
        if (sortKey === k) sortDir *= -1;
        else { sortKey = k; sortDir = ["score", "pain_score"].includes(k) ? -1 : 1; }
        render();
      });
    });
    els.modalBg.addEventListener("click", (e) => {
      if (e.target === els.modalBg) closeModal();
    });
  }

  function render() {
    const tier = els.tier.value;
    const vertical = els.vertical.value;
    const spend = els.spend.value;
    const q = els.search.value.trim().toLowerCase();

    let filtered = data.filter((r) => {
      if (tier && String(r.tier) !== tier) return false;
      if (vertical && r.vertical !== vertical) return false;
      if (spend && (r.spend_tier || "").toLowerCase() !== spend.toLowerCase()) return false;
      if (q) {
        const hay = [r.company_name, r.buyer_name, r.vertical, r.one_line_description].filter(Boolean).join(" ").toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });

    filtered.sort((a, b) => {
      let av = a[sortKey] ?? "";
      let bv = b[sortKey] ?? "";
      if (typeof av === "number" || typeof bv === "number") {
        av = Number(av) || 0; bv = Number(bv) || 0;
        return (av - bv) * sortDir;
      }
      return String(av).localeCompare(String(bv)) * sortDir;
    });

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
    const tierBadge = `<span class="badge badge-tier-${r.tier}">Tier ${r.tier}</span>`;
    const vlaBadge = r.vla_classification ? `<span class="badge badge-${r.vla_classification.replace(/_/g, "-")}">${r.vla_classification.replace("vla_", "")}</span>` : "";
    const company = r.dossier_url
      ? `<a href="${r.dossier_url}">${escape(r.company_name)}</a>`
      : escape(r.company_name);
    const buyer = r.buyer_linkedin_url
      ? `<a href="${r.buyer_linkedin_url}" target="_blank" rel="noopener">${escape(r.buyer_name || "—")}</a>`
      : escape(r.buyer_name || "—");
    return `<tr class="tier-${r.tier}">
      <td class="col-company" data-label="Company">${company}<div class="muted" style="font-size:12px">${escape(r.one_line_description || "")}</div></td>
      <td data-label="Vertical">${VERTICAL_LABELS[r.vertical] || escape(r.vertical || "—")}</td>
      <td data-label="Tier">${tierBadge}</td>
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

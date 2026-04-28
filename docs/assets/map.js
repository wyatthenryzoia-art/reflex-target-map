// Leaflet + CARTO dark tile map. Markers clustered, popup on click.
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
    map: document.getElementById("map"),
    vertical: document.getElementById("f-vertical"),
    region: document.getElementById("f-region"),
    vla: document.getElementById("f-vla"),
    search: document.getElementById("f-search"),
    count: document.getElementById("count"),
  };

  let data = [];
  let geoIndex = {};
  let map = null;
  let cluster = null;
  let markersById = {};

  Promise.all([
    fetch("./assets/data.json").then((r) => r.json()),
    fetch("./assets/geo.json").then((r) => r.json()),
  ]).then(([rows, geo]) => {
    data = rows;
    for (const g of geo) geoIndex[(g.hq_city || "") + "|" + (g.hq_country || "")] = g;
    initMap();
    populateVerticalFilter();
    bindEvents();
    render();
  }).catch((e) => {
    if (els.map) els.map.innerHTML = '<div style="padding:40px;color:#fff;text-align:center">Failed to load map: ' + e.message + '</div>';
  });

  function initMap() {
    map = L.map(els.map, {
      worldCopyJump: true,
      zoomControl: true,
      attributionControl: true,
      preferCanvas: false,
    }).setView([39, -96], 4);   // open on North America

    // CARTO dark basemap. dark_nolabels keeps the map quiet — only landmass + faint borders.
    L.tileLayer(
      "https://{s}.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}{r}.png",
      {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/">CARTO</a>',
        subdomains: "abcd",
        maxZoom: 18,
      }
    ).addTo(map);

    // Add place labels on a separate pane, so they sit above markers' tiles
    // but below the markers themselves.
    L.tileLayer(
      "https://{s}.basemaps.cartocdn.com/dark_only_labels/{z}/{x}/{y}{r}.png",
      {
        subdomains: "abcd",
        maxZoom: 18,
        opacity: 0.55,
      }
    ).addTo(map);

    cluster = L.markerClusterGroup({
      showCoverageOnHover: false,
      spiderfyOnMaxZoom: true,
      maxClusterRadius: 35,
      iconCreateFunction: (c) => {
        const n = c.getChildCount();
        const size = n < 10 ? 32 : n < 50 ? 38 : 46;
        return L.divIcon({
          html: `<div class="cluster-mark"><span>${n}</span></div>`,
          className: "cluster-wrap",
          iconSize: [size, size],
        });
      },
    });
    map.addLayer(cluster);
  }

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
    [els.vertical, els.region, els.vla].forEach((el) => el && el.addEventListener("change", render));
    if (els.search) els.search.addEventListener("input", debounce(render, 150));
  }

  function debounce(fn, ms) {
    let t = null;
    return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); };
  }

  function lookup(row) { return geoIndex[(row.hq_city || "") + "|" + (row.hq_country || "")]; }

  function render() {
    const vertical = els.vertical.value;
    const region = els.region.value;
    const vla = els.vla.value;
    const q = (els.search.value || "").trim().toLowerCase();
    const filtered = data.filter((r) => {
      if (vertical && r.vertical !== vertical) return false;
      if (region && r.region !== region) return false;
      if (vla && r.vla_classification !== vla) return false;
      if (q) {
        const hay = [r.company_name, r.buyer_name, r.vertical, r.one_line_description, r.hq_display].filter(Boolean).join(" ").toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });

    cluster.clearLayers();
    markersById = {};
    let placed = 0;
    for (const r of filtered) {
      const g = lookup(r);
      if (!g) continue;
      const m = L.marker([g.lat, g.lon], { icon: makeIcon(r) });
      m.bindPopup(() => popupHtml(r), { maxWidth: 320, autoPan: true });
      m.on("click", () => m.openPopup());
      cluster.addLayer(m);
      markersById[r.id] = m;
      placed += 1;
    }
    els.count.textContent = `${placed} of ${data.length} companies`;
  }

  function makeIcon(r) {
    const cls = "pin pin-" + (r.vla_classification || "vla_possible").replace("_", "-") + (r.has_dossier ? " priority" : "");
    return L.divIcon({
      className: "pin-wrap",
      html: `<div class="${cls}"></div>`,
      iconSize: [16, 16],
      iconAnchor: [8, 8],
    });
  }

  function popupHtml(r) {
    const buyer = r.buyer_linkedin_url
      ? `<a href="${r.buyer_linkedin_url}" target="_blank" rel="noopener">${escape(r.buyer_name || "—")}</a>`
      : escape(r.buyer_name || "(buyer not yet ID'd)");
    const dossier = r.dossier_url ? `<a class="primary" href="${r.dossier_url}">view dossier →</a>` : "";
    const vlaLabel = r.vla_classification ? r.vla_classification.replace("vla_", "") : "—";
    return `
      <div class="popup">
        <h4>${r.dossier_url ? `<a href="${r.dossier_url}">${escape(r.company_name)}</a>` : escape(r.company_name)}</h4>
        <p class="desc">${escape(r.one_line_description || "")}</p>
        <dl>
          <div><dt>vertical</dt><dd>${VERTICAL_LABELS[r.vertical] || escape(r.vertical || "—")}</dd></div>
          <div><dt>hq</dt><dd>${escape(r.hq_display || "—")}</dd></div>
          <div><dt>vla</dt><dd>${vlaLabel}</dd></div>
          <div><dt>buyer</dt><dd>${buyer}</dd></div>
        </dl>
        ${dossier}
      </div>
    `;
  }

  function escape(s) {
    return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  }
})();

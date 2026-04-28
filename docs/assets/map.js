// World map renderer with robot markers. Uses vendored topojson-client.
// Equirectangular projection; markers placed by lat/lon → SVG x/y.

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

  const W = 1440;       // SVG viewport width
  const H = 720;        // SVG viewport height (equirectangular = 2:1)
  const R = 5;          // marker radius (base)
  const R_ACTIVE = 7;   // marker radius for vla_active

  const els = {
    map: document.getElementById("map"),
    countries: document.getElementById("countries"),
    markers: document.getElementById("markers"),
    tooltip: document.getElementById("tooltip"),
    vertical: document.getElementById("f-vertical"),
    region: document.getElementById("f-region"),
    vla: document.getElementById("f-vla"),
    search: document.getElementById("f-search"),
    count: document.getElementById("count"),
  };

  let data = [];
  let geoIndex = {};   // "city|country" → {lat, lon, source}
  let activeMarker = null;

  function project(lon, lat) {
    const x = (lon + 180) / 360 * W;
    const y = (90 - lat) / 180 * H;
    return [x, y];
  }

  function pathForGeometry(geom) {
    // returns SVG path string for a Polygon or MultiPolygon (already in lon/lat)
    if (geom.type === "Polygon") {
      return geom.coordinates.map(ringToPath).join(" ");
    }
    if (geom.type === "MultiPolygon") {
      return geom.coordinates.flat().map(ringToPath).join(" ");
    }
    return "";
  }
  function ringToPath(ring) {
    return ring.map(([lon, lat], i) => {
      const [x, y] = project(lon, lat);
      return (i === 0 ? "M" : "L") + x.toFixed(1) + "," + y.toFixed(1);
    }).join("") + "Z";
  }

  Promise.all([
    fetch("./assets/data.json").then((r) => r.json()),
    fetch("./assets/geo.json").then((r) => r.json()),
    fetch("./assets/vendor/countries-110m.json").then((r) => r.json()),
  ]).then(([rows, geo, world]) => {
    data = rows;
    for (const g of geo) {
      const k = (g.hq_city || "") + "|" + (g.hq_country || "");
      geoIndex[k] = g;
    }
    drawCountries(world);
    populateVerticalFilter();
    bindEvents();
    render();
  }).catch((e) => {
    if (els.map) els.map.innerHTML = '<text x="50%" y="50%" fill="#fff" text-anchor="middle">Failed to load map data: ' + e.message + '</text>';
  });

  function drawCountries(world) {
    const fc = topojson.feature(world, world.objects.countries);
    const paths = fc.features.map((f) => `<path d="${pathForGeometry(f.geometry)}"/>`).join("");
    els.countries.innerHTML = paths;
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
    if (els.search) els.search.addEventListener("input", render);
    document.addEventListener("click", (e) => {
      if (!e.target.closest(".marker") && !e.target.closest("#tooltip")) {
        hideTooltip();
      }
    });
  }

  function lookup(row) {
    const k = (row.hq_city || "") + "|" + (row.hq_country || "");
    return geoIndex[k];
  }

  function render() {
    const vertical = els.vertical.value;
    const region = els.region.value;
    const vla = els.vla.value;
    const q = (els.search.value || "").trim().toLowerCase();

    let filtered = data.filter((r) => {
      if (vertical && r.vertical !== vertical) return false;
      if (region && r.region !== region) return false;
      if (vla && r.vla_classification !== vla) return false;
      if (q) {
        const hay = [r.company_name, r.buyer_name, r.vertical, r.one_line_description, r.hq_display].filter(Boolean).join(" ").toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });

    // bucket markers by rounded position so we can offset overlapping ones
    const bucket = {};
    const placed = [];
    for (const r of filtered) {
      const g = lookup(r);
      if (!g) continue;
      const [x, y] = project(g.lon, g.lat);
      const key = Math.round(x / 6) + "_" + Math.round(y / 6);
      const n = (bucket[key] || 0);
      bucket[key] = n + 1;
      const angle = n * 1.7;
      const dx = n === 0 ? 0 : Math.cos(angle) * (4 + n * 1.5);
      const dy = n === 0 ? 0 : Math.sin(angle) * (4 + n * 1.5);
      placed.push({ ...r, x: x + dx, y: y + dy });
    }

    // sort active first so they paint on top
    placed.sort((a, b) => {
      const av = a.vla_classification === "vla_active" ? 2 : (a.vla_classification === "vla_likely" ? 1 : 0);
      const bv = b.vla_classification === "vla_active" ? 2 : (b.vla_classification === "vla_likely" ? 1 : 0);
      return av - bv;
    });

    els.markers.innerHTML = placed.map(markerSvg).join("");
    els.count.textContent = `${placed.length} of ${data.length} companies`;

    document.querySelectorAll(".marker").forEach((m) => {
      m.addEventListener("click", (e) => {
        e.stopPropagation();
        const id = m.dataset.id;
        showTooltip(id, m);
      });
      m.addEventListener("mouseenter", () => {
        const id = m.dataset.id;
        showTooltip(id, m);
      });
    });
  }

  function markerSvg(r) {
    const cls = "marker vla-" + (r.vla_classification || "vla_possible").replace("_", "-");
    const radius = r.vla_classification === "vla_active" ? R_ACTIVE : R;
    const priority = r.has_dossier ? " priority" : "";
    return `<g class="${cls}${priority}" data-id="${r.id}" transform="translate(${r.x.toFixed(1)},${r.y.toFixed(1)})">
      <circle r="${radius + 4}" class="halo"/>
      <circle r="${radius}" class="dot"/>
    </g>`;
  }

  function showTooltip(id, marker) {
    const row = data.find((r) => r.id === id);
    if (!row) return;
    const buyer = row.buyer_linkedin_url
      ? `<a href="${row.buyer_linkedin_url}" target="_blank" rel="noopener">${escape(row.buyer_name || "—")}</a>`
      : escape(row.buyer_name || "(buyer not yet ID'd)");
    const dossier = row.dossier_url
      ? `<a class="primary" href="${row.dossier_url}">view dossier →</a>`
      : "";
    const vlaLabel = row.vla_classification ? row.vla_classification.replace("vla_", "") : "—";
    els.tooltip.innerHTML = `
      <button class="x" aria-label="close">×</button>
      <h4>${row.dossier_url ? `<a href="${row.dossier_url}">${escape(row.company_name)}</a>` : escape(row.company_name)}</h4>
      <p class="desc">${escape(row.one_line_description || "")}</p>
      <dl>
        <div><dt>vertical</dt><dd>${VERTICAL_LABELS[row.vertical] || escape(row.vertical || "—")}</dd></div>
        <div><dt>hq</dt><dd>${escape(row.hq_display || "—")}</dd></div>
        <div><dt>vla</dt><dd>${vlaLabel}</dd></div>
        <div><dt>buyer</dt><dd>${buyer}</dd></div>
      </dl>
      ${dossier}
    `;
    // position tooltip near the marker, kept inside the map
    const mapRect = els.map.getBoundingClientRect();
    const markerRect = marker.getBoundingClientRect();
    const tip = els.tooltip;
    tip.classList.add("open");
    const tw = tip.offsetWidth;
    const th = tip.offsetHeight;
    let left = markerRect.left - mapRect.left + 12;
    let top = markerRect.top - mapRect.top + 12;
    if (left + tw > mapRect.width) left = markerRect.left - mapRect.left - tw - 12;
    if (top + th > mapRect.height) top = markerRect.top - mapRect.top - th - 12;
    if (left < 0) left = 8;
    if (top < 0) top = 8;
    tip.style.left = left + "px";
    tip.style.top = top + "px";

    tip.querySelector(".x").addEventListener("click", hideTooltip);
    activeMarker = marker;
  }

  function hideTooltip() {
    els.tooltip.classList.remove("open");
    activeMarker = null;
  }

  function escape(s) {
    return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  }

  window.addEventListener("keydown", (e) => { if (e.key === "Escape") hideTooltip(); });
})();

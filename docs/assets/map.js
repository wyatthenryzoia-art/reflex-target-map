// Pan/zoom world map with markers at company HQs.
// Vendored: world-atlas@2 countries-50m, us-atlas@3 states-10m, topojson-client.
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

  // World canvas (equirectangular). 1440 x 720 = 2:1 aspect.
  const W = 1440, H = 720;

  // Marker base sizes — scaled inversely so they stay readable as we zoom.
  const R = 5, R_ACTIVE = 7;

  const els = {
    map: document.getElementById("map"),
    countries: document.getElementById("countries"),
    states: document.getElementById("states"),
    markers: document.getElementById("markers"),
    tooltip: document.getElementById("tooltip"),
    vertical: document.getElementById("f-vertical"),
    region: document.getElementById("f-region"),
    vla: document.getElementById("f-vla"),
    search: document.getElementById("f-search"),
    count: document.getElementById("count"),
    reset: document.getElementById("reset-zoom"),
    zoomIn: document.getElementById("zoom-in"),
    zoomOut: document.getElementById("zoom-out"),
  };

  let data = [];
  let geoIndex = {};

  // --- pan/zoom state (viewBox manipulation) ---
  const view = { x: 0, y: 0, w: W, h: H };
  const MIN_ZOOM = 1;       // 1 = whole world (viewBox === W x H)
  const MAX_ZOOM = 12;      // 12x = city-level
  const STATE_VISIBLE_ZOOM = 2.5;  // show US state borders past this

  function project(lon, lat) {
    return [(lon + 180) / 360 * W, (90 - lat) / 180 * H];
  }
  function pathFor(geom) {
    if (geom.type === "Polygon") return geom.coordinates.map(ring).join(" ");
    if (geom.type === "MultiPolygon") return geom.coordinates.flat().map(ring).join(" ");
    return "";
  }
  function ring(coords) {
    return coords.map(([lon, lat], i) => {
      const [x, y] = project(lon, lat);
      return (i === 0 ? "M" : "L") + x.toFixed(1) + "," + y.toFixed(1);
    }).join("") + "Z";
  }

  Promise.all([
    fetch("./assets/data.json").then((r) => r.json()),
    fetch("./assets/geo.json").then((r) => r.json()),
    fetch("./assets/vendor/countries-50m.json").then((r) => r.json()),
    fetch("./assets/vendor/us-states-10m.json").then((r) => r.json()),
  ]).then(([rows, geo, world, us]) => {
    data = rows;
    for (const g of geo) geoIndex[(g.hq_city || "") + "|" + (g.hq_country || "")] = g;
    drawCountries(world);
    drawStates(us);
    populateVerticalFilter();
    bindEvents();
    syncViewBox();
    render();
  }).catch((e) => {
    if (els.map) els.map.innerHTML = '<text x="50%" y="50%" fill="#fff" text-anchor="middle">Failed to load map: ' + e.message + '</text>';
  });

  function drawCountries(world) {
    const fc = topojson.feature(world, world.objects.countries);
    els.countries.innerHTML = fc.features.map((f) => `<path d="${pathFor(f.geometry)}"/>`).join("");
  }
  function drawStates(us) {
    // us-atlas uses Albers projection coordinates, NOT lon/lat — we need to use mesh-by-id
    // and re-project. Simpler: take feature collection of states (already has geometries
    // in lon/lat in this dataset).
    if (!us.objects || !us.objects.states) { els.states.innerHTML = ""; return; }
    const fc = topojson.feature(us, us.objects.states);
    els.states.innerHTML = fc.features.map((f) => `<path d="${pathFor(f.geometry)}"/>`).join("");
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
    if (els.reset) els.reset.addEventListener("click", () => setView(0, 0, W, H, true));
    if (els.zoomIn) els.zoomIn.addEventListener("click", () => zoomBy(0.6, W / 2, H / 2));
    if (els.zoomOut) els.zoomOut.addEventListener("click", () => zoomBy(1.7, W / 2, H / 2));

    // wheel = zoom around cursor
    els.map.addEventListener("wheel", (e) => {
      e.preventDefault();
      const [px, py] = pointFromEvent(e);
      const factor = Math.exp(e.deltaY * 0.0015);
      zoomBy(factor, px, py);
    }, { passive: false });

    // mouse drag = pan
    let dragging = false;
    let dragStart = null;
    els.map.addEventListener("mousedown", (e) => {
      if (e.target.closest(".marker")) return; // don't drag when clicking a marker
      dragging = true;
      dragStart = { x: e.clientX, y: e.clientY, vx: view.x, vy: view.y };
      els.map.classList.add("dragging");
    });
    window.addEventListener("mousemove", (e) => {
      if (!dragging) return;
      const rect = els.map.getBoundingClientRect();
      const sx = view.w / rect.width;
      const sy = view.h / rect.height;
      const nx = dragStart.vx - (e.clientX - dragStart.x) * sx;
      const ny = dragStart.vy - (e.clientY - dragStart.y) * sy;
      setView(nx, ny, view.w, view.h);
    });
    window.addEventListener("mouseup", () => {
      dragging = false;
      els.map.classList.remove("dragging");
    });

    // touch (pinch + drag) — basic single-finger pan + two-finger pinch
    let touchState = null;
    els.map.addEventListener("touchstart", (e) => {
      if (e.touches.length === 1) {
        touchState = { mode: "pan", x: e.touches[0].clientX, y: e.touches[0].clientY, vx: view.x, vy: view.y };
      } else if (e.touches.length === 2) {
        const t1 = e.touches[0], t2 = e.touches[1];
        const cx = (t1.clientX + t2.clientX) / 2;
        const cy = (t1.clientY + t2.clientY) / 2;
        const d = Math.hypot(t1.clientX - t2.clientX, t1.clientY - t2.clientY);
        touchState = { mode: "pinch", cx, cy, d, view: { ...view } };
      }
    }, { passive: true });
    els.map.addEventListener("touchmove", (e) => {
      if (!touchState) return;
      e.preventDefault();
      const rect = els.map.getBoundingClientRect();
      if (touchState.mode === "pan" && e.touches.length === 1) {
        const sx = view.w / rect.width;
        const sy = view.h / rect.height;
        const nx = touchState.vx - (e.touches[0].clientX - touchState.x) * sx;
        const ny = touchState.vy - (e.touches[0].clientY - touchState.y) * sy;
        setView(nx, ny, view.w, view.h);
      } else if (touchState.mode === "pinch" && e.touches.length === 2) {
        const t1 = e.touches[0], t2 = e.touches[1];
        const d = Math.hypot(t1.clientX - t2.clientX, t1.clientY - t2.clientY);
        const factor = touchState.d / d;
        const nw = Math.max(W / MAX_ZOOM, Math.min(W / MIN_ZOOM, touchState.view.w * factor));
        const nh = nw * (H / W);
        const px = ((touchState.cx - rect.left) / rect.width) * touchState.view.w + touchState.view.x;
        const py = ((touchState.cy - rect.top) / rect.height) * touchState.view.h + touchState.view.y;
        const nx = px - ((touchState.cx - rect.left) / rect.width) * nw;
        const ny = py - ((touchState.cy - rect.top) / rect.height) * nh;
        setView(nx, ny, nw, nh);
      }
    }, { passive: false });
    els.map.addEventListener("touchend", () => { touchState = null; });

    // close tooltip on outside click
    document.addEventListener("click", (e) => {
      if (!e.target.closest(".marker") && !e.target.closest("#tooltip")) hideTooltip();
    });
    window.addEventListener("keydown", (e) => { if (e.key === "Escape") hideTooltip(); });
  }

  function pointFromEvent(e) {
    const rect = els.map.getBoundingClientRect();
    const px = ((e.clientX - rect.left) / rect.width) * view.w + view.x;
    const py = ((e.clientY - rect.top) / rect.height) * view.h + view.y;
    return [px, py];
  }

  function zoomBy(factor, px, py) {
    const nw = Math.max(W / MAX_ZOOM, Math.min(W / MIN_ZOOM, view.w * factor));
    const nh = nw * (H / W);
    // anchor on (px, py) so the cursor stays stationary in world coords
    const ax = (px - view.x) / view.w;
    const ay = (py - view.y) / view.h;
    const nx = px - ax * nw;
    const ny = py - ay * nh;
    setView(nx, ny, nw, nh, false);
  }

  function setView(x, y, w, h, animate = false) {
    // clamp so we can't pan off the map
    const clampedW = Math.max(W / MAX_ZOOM, Math.min(W, w));
    const clampedH = clampedW * (H / W);
    const cx = Math.max(0, Math.min(W - clampedW, x));
    const cy = Math.max(0, Math.min(H - clampedH, y));
    if (animate) els.map.classList.add("animate");
    else els.map.classList.remove("animate");
    view.x = cx; view.y = cy; view.w = clampedW; view.h = clampedH;
    syncViewBox();
    if (animate) setTimeout(() => els.map.classList.remove("animate"), 350);
  }

  function syncViewBox() {
    els.map.setAttribute("viewBox", `${view.x} ${view.y} ${view.w} ${view.h}`);
    // markers should stay roughly the same screen size; counter-scale via attribute
    const zoom = W / view.w;
    document.documentElement.style.setProperty("--map-zoom", zoom);
    // toggle states layer visibility past threshold
    if (els.states) {
      els.states.style.opacity = zoom >= STATE_VISIBLE_ZOOM ? "1" : "0";
    }
    // update zoom indicator if present
    const z = document.getElementById("zoom-indicator");
    if (z) z.textContent = `${zoom.toFixed(1)}×`;
  }

  function lookup(row) { return geoIndex[(row.hq_city || "") + "|" + (row.hq_country || "")]; }

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

    // bucket by rounded position so overlapping markers fan out in a small grid
    const bucket = {};
    const placed = [];
    for (const r of filtered) {
      const g = lookup(r);
      if (!g) continue;
      const [x, y] = project(g.lon, g.lat);
      const key = Math.round(x / 4) + "_" + Math.round(y / 4);
      const n = (bucket[key] || 0);
      bucket[key] = n + 1;
      // gentle fibonacci-ish spiral
      const golden = 2.39996;
      const angle = n * golden;
      const dist = n === 0 ? 0 : Math.sqrt(n) * 4;
      const dx = Math.cos(angle) * dist;
      const dy = Math.sin(angle) * dist;
      placed.push({ ...r, x: x + dx, y: y + dy });
    }
    // active first for paint order
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
        showTooltip(m.dataset.id, m);
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
    const dossier = row.dossier_url ? `<a class="primary" href="${row.dossier_url}">view dossier →</a>` : "";
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
  }
  function hideTooltip() { els.tooltip.classList.remove("open"); }
  function escape(s) {
    return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  }
})();

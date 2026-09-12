/* ============================================================
   Augusta 12 scrollytelling chapters (issue #13).
   Canvas 2D, no libraries. Reads data/003_chapters.json once and
   redraws every figure deterministically from it -- the browser
   never invents a number.

   Deterministic hooks (QA / social capture):
     ?chapter=N&step=M   renders that chapter's figure in its
                         settled state inside a capture card sized
                         for a 1080x1350 carousel crop, sets
                         window.__phaseComplete = true once drawn.
     window.__chapterState  {chapter, step} of the active scroll
                             position (updated on scroll too).
   ============================================================ */
(function(){
"use strict";

var DATA_URL = "/augusta-12/data/003_chapters.json";
var AERIAL_MAP_URL = "/augusta-12/data/aerial_map.json";
var AERIAL_IMG_URL = "/assets/img/003_aerial.png";
var TIER_LABELS = {0: "Scratch", 5: "5-handicap", 10: "10-handicap", 15: "15-handicap", 20: "20-handicap"};
var PIN_LABELS = {left: "Left pin", center: "Center pin", sunday: "Sunday pin"};

var qs = new URLSearchParams(location.search);
// No JS-driven animation here (figures redraw instantly on step change,
// never tweened): the only motion this page adds is the step opacity/
// border-color transition in chapters.css, which its own
// prefers-reduced-motion media query already disables.

var chaptersData = null;
var aerialMap = null;
var aerialImg = null;
var aerialReady = false;

window.__chapterState = {chapter: null, step: null};

function fmt1(n){ return (Math.round(n * 10) / 10).toFixed(1); }
function fmtPct(p){ return (Math.round(p * 1000) / 10).toFixed(1) + "%"; }
function cellKey(tier, pin, wind){ return tier + "|" + pin + "|" + (wind ? 1 : 0); }

// ---------------------------------------------------------------
// Top-down projection: every chapter figure draws over 003_aerial.png,
// positioned/scaled through aerial_map.json's own shape-affine (model yd
// -> aerial pixels, analysis/003-augusta-12/art/fit_shapes.py) composed
// with a crop-and-scale that fits the same model-yard viewport this page
// always showed (VIEW_X_MIN/MAX, VIEW_Y_MIN/MAX) into the canvas. No
// separate y-flip is needed here the way the old code-drawn projector
// needed one: the aerial photo and its affine already agree on "tee near
// the bottom, green near the top."
// ---------------------------------------------------------------
var VIEW_X_MIN = -22, VIEW_X_MAX = 22;
var VIEW_Y_MIN = 108, VIEW_Y_MAX = 205;

function applyAerialAffine(affine, x_yd, y_yd){
  return [
    affine[0][0] * x_yd + affine[0][1] * y_yd + affine[0][2],
    affine[1][0] * x_yd + affine[1][1] * y_yd + affine[1][2]
  ];
}

function frontEdgeYd(x_yd, map){
  var f = map.short_affine_blend.front_edge;
  return f.front_edge_at_x0_yd + f.slope_yd_per_yd * x_yd;
}

// modelToAerialPx: model yd -> aerial_final.png pixel, blending
// green_affine / short_affine at the front edge exactly like hero.js's
// project() does (aerial_map.json carries the same short_affine_blend
// shape when a short_affine was needed; see fit_shapes.py).
function modelToAerialPx(x_yd, y_yd, map){
  if (!map.short_affine){
    return applyAerialAffine(map.affine, x_yd, y_yd);
  }
  var fe = frontEdgeYd(x_yd, map);
  var margin = map.short_affine_blend.blend_margin_yd;
  var g = applyAerialAffine(map.affine, x_yd, y_yd);
  if (y_yd >= fe + margin) return g;
  var s = applyAerialAffine(map.short_affine, x_yd, y_yd);
  if (y_yd <= fe - margin) return s;
  var t = Math.min(1, Math.max(0, (y_yd - (fe - margin)) / (2 * margin)));
  return [s[0] + (g[0] - s[0]) * t, s[1] + (g[1] - s[1]) * t];
}

function makeProjector(canvas){
  var w = canvas.width, h = canvas.height;
  if (!aerialReady){
    // Fallback while the aerial map/image are still loading: same model
    // viewport, no image, so a figure requested before boot still gets
    // sane (if imageless) coordinates instead of throwing.
    var xr0 = VIEW_X_MAX - VIEW_X_MIN, yr0 = VIEW_Y_MAX - VIEW_Y_MIN;
    var scale0 = Math.min(w / xr0, h / yr0);
    var offX0 = (w - xr0 * scale0) / 2, offY0 = (h - yr0 * scale0) / 2;
    return {
      scale: scale0,
      drawBase: function(){},
      toPx: function(x_yd, y_yd){
        return [offX0 + (x_yd - VIEW_X_MIN) * scale0, h - (offY0 + (y_yd - VIEW_Y_MIN) * scale0)];
      }
    };
  }

  var corners = [
    [VIEW_X_MIN, VIEW_Y_MIN], [VIEW_X_MAX, VIEW_Y_MIN],
    [VIEW_X_MIN, VIEW_Y_MAX], [VIEW_X_MAX, VIEW_Y_MAX]
  ].map(function(p){ return modelToAerialPx(p[0], p[1], aerialMap); });
  var minAx = Math.min.apply(null, corners.map(function(c){ return c[0]; }));
  var maxAx = Math.max.apply(null, corners.map(function(c){ return c[0]; }));
  var minAy = Math.min.apply(null, corners.map(function(c){ return c[1]; }));
  var maxAy = Math.max.apply(null, corners.map(function(c){ return c[1]; }));
  // Cover-fit (max), not contain-fit: the model viewport (44 x 97 yd,
  // portrait) and this square canvas rarely share an aspect ratio once
  // run through the aerial's own anisotropic px/yd scale, and a
  // contain-fit leaves bare canvas margins a wide dispersion oval (tier
  // 20, say) can visibly spill past. Cover-fit fills the whole canvas,
  // showing a little more surrounding fairway/trees on one axis instead.
  var scale = Math.max(w / (maxAx - minAx), h / (maxAy - minAy));
  var offX = (w - (maxAx - minAx) * scale) / 2;
  var offY = (h - (maxAy - minAy) * scale) / 2;

  // Effective model-yd -> canvas-px scale, for dispersion ovals: the mean
  // magnitude of the affine's two column vectors (px per yd of x, px per
  // yd of y) times the crop-to-canvas scale above. The aerial is close to
  // orthographic (art/README.md), so this isotropic approximation reads
  // the same as the old plain top-down projector did, now driven by the
  // fitted affine instead of a hand-typed constant.
  var A = aerialMap.affine;
  var colX = [A[0][0], A[1][0]], colY = [A[0][1], A[1][1]];
  var magX = Math.hypot(colX[0], colX[1]), magY = Math.hypot(colY[0], colY[1]);
  var modelScale = ((magX + magY) / 2) * scale;
  // Rotation of the model's x-axis (lateral, the oval's "line" axis) as it
  // lands in canvas space -- used to draw ovals at the aerial's own tilt
  // instead of assuming the tee-to-green line is perfectly vertical.
  var rotation = Math.atan2(colX[1], colX[0]);

  return {
    scale: modelScale,
    rotation: rotation,
    drawBase: function(ctx){
      ctx.drawImage(aerialImg, minAx, minAy, maxAx - minAx, maxAy - minAy,
        offX, offY, (maxAx - minAx) * scale, (maxAy - minAy) * scale);
    },
    toPx: function(x_yd, y_yd){
      var a = modelToAerialPx(x_yd, y_yd, aerialMap);
      return [offX + (a[0] - minAx) * scale, offY + (a[1] - minAy) * scale];
    }
  };
}

function readColors(){
  var cs = getComputedStyle(document.documentElement);
  function v(name){ return cs.getPropertyValue(name).trim(); }
  return {
    ink: v("--ink"), inkSoft: v("--ink-soft"), muted: v("--muted"),
    clay: v("--clay"), clayText: v("--clay-text"),
    blue: v("--blue"), blueText: v("--blue-text"),
    maroon: v("--maroon"), card: v("--card"), bg: v("--bg"), line: v("--line")
  };
}

// The hole itself is now carried entirely by the aerial photograph
// (proj.drawBase, wired through aerial_map.json) -- no code-drawn green
// parallelogram, creek band, or bunker boxes; see chapters.js's header
// comment and makeProjector above.

// labelPlate: a small translucent card-colored backing behind a text
// label so it stays readable over the aerial photo's own busy colors,
// same trick a printed map uses under a place name.
function labelPlate(ctx, x, y, w, h, colors){
  ctx.fillStyle = hexA(colors.card, 0.82);
  ctx.fillRect(x, y, w, h);
}

function hexA(hex, alpha){
  // hex like #RRGGBB (site.css tokens); fall back to rgba black if unparsed.
  var m = /^#([0-9a-f]{6})$/i.exec(hex.trim());
  if (!m) return "rgba(0,0,0," + alpha + ")";
  var n = parseInt(m[1], 16);
  var r = (n >> 16) & 255, g = (n >> 8) & 255, b = n & 255;
  return "rgba(" + r + "," + g + "," + b + "," + alpha + ")";
}

function drawPinMarker(ctx, proj, x, y, color){
  var p = proj.toPx(x, y);
  ctx.beginPath();
  ctx.moveTo(p[0], p[1] - 9);
  ctx.lineTo(p[0], p[1] + 3);
  ctx.strokeStyle = color;
  ctx.lineWidth = 1.5;
  ctx.stroke();
  ctx.beginPath();
  ctx.moveTo(p[0], p[1] - 9);
  ctx.lineTo(p[0] + 7, p[1] - 6.5);
  ctx.lineTo(p[0], p[1] - 4);
  ctx.closePath();
  ctx.fillStyle = color;
  ctx.fill();
  ctx.beginPath();
  ctx.arc(p[0], p[1] + 3, 1.6, 0, Math.PI * 2);
  ctx.fill();
}

function drawOval(ctx, proj, cx, cy, sigmaD, sigmaL, opts){
  // sigmaD is the distance (y) axis sigma, sigmaL the line (x) axis sigma,
  // both in yards. Rotated by proj.rotation (the model's x/lateral axis's
  // own tilt as it lands in the aerial photo, from makeProjector) so the
  // oval sits true to the aerial's actual camera angle instead of assuming
  // the tee-to-green line renders perfectly vertical.
  var c = proj.toPx(cx, cy);
  var rx = sigmaL * proj.scale * opts.nSigma; // along the model's lateral (x) axis
  var ry = sigmaD * proj.scale * opts.nSigma; // along the model's depth (y) axis
  var rotation = proj.rotation || 0; // model x-axis's own tilt in canvas space
  ctx.beginPath();
  ctx.ellipse(c[0], c[1], Math.max(rx, 1), Math.max(ry, 1), rotation, 0, Math.PI * 2);
  if (opts.fill){ ctx.fillStyle = opts.fill; ctx.fill(); }
  ctx.strokeStyle = opts.stroke;
  ctx.lineWidth = opts.lineWidth || 1.5;
  if (opts.dashed) ctx.setLineDash([5, 4]); else ctx.setLineDash([]);
  ctx.stroke();
  ctx.setLineDash([]);
}

function label(ctx, x, y, text, color, opts){
  opts = opts || {};
  ctx.font = (opts.weight || "500") + " " + (opts.size || 11) + "px 'IBM Plex Mono', ui-monospace, monospace";
  ctx.fillStyle = color;
  ctx.textAlign = opts.align || "left";
  ctx.textBaseline = opts.baseline || "alphabetic";
  ctx.fillText(text, x, y);
}

// ---------------------------------------------------------------
// Chapter 1: "the question" -- all five tier ovals (calm), centered
// on the center-pin reference point, sigma labeled, 15/20 tagged
// MODELED.
// ---------------------------------------------------------------
function drawAllTiersFigure(canvas, data){
  var ctx = canvas.getContext("2d");
  var colors = readColors();
  var proj = makeProjector(canvas);
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  proj.drawBase(ctx);

  var ref = data.pins.center; // shared reference aim point for comparison
  var tierColors = [colors.ink, colors.blueText, colors.clayText, colors.maroon, colors.muted];
  data.tiers.forEach(function(tier, i){
    var cell = data.cells[cellKey(tier, "center", false)];
    drawOval(ctx, proj, ref.x, ref.y, cell.sigma_d_calm_yd, cell.sigma_l_calm_yd, {
      stroke: tierColors[i % tierColors.length], nSigma: 1, lineWidth: 1.75,
      dashed: tier === 15 || tier === 20
    });
  });
  drawPinMarker(ctx, proj, ref.x, ref.y, colors.ink);

  // Sigma readout, largest (tier 20) to smallest, stacked top-left, over a
  // translucent plate so it stays readable against the photo underneath.
  labelPlate(ctx, 4, 4, 186, data.tiers.length * 15 + 8, colors);
  var ty = 18;
  data.tiers.slice().reverse().forEach(function(tier){
    var cell = data.cells[cellKey(tier, "center", false)];
    var modeled = (tier === 15 || tier === 20) ? "  MODELED" : "";
    label(ctx, 10, ty, TIER_LABELS[tier] + ": σ " + fmt1(cell.sigma_d_calm_yd) + " x " +
      fmt1(cell.sigma_l_calm_yd) + " yd" + modeled, colors.inkSoft, {size: 10.5});
    ty += 15;
  });
}

// ---------------------------------------------------------------
// Chapters 2-4 (pin walks): oval at the published aim, ghosted
// oval at the pin itself, water/green stat chips.
// ---------------------------------------------------------------
function drawPinFigure(canvas, data, pin, tier, wind){
  var ctx = canvas.getContext("2d");
  var colors = readColors();
  var proj = makeProjector(canvas);
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  proj.drawBase(ctx);

  var p = data.pins[pin];
  var cell = data.cells[cellKey(tier, pin, wind)];

  // Ghosted at-pin oval (aiming straight at the flag).
  drawOval(ctx, proj, p.x, p.y, cell.sigma_d_yd, cell.sigma_l_yd, {
    stroke: colors.muted, nSigma: 1, dashed: true, lineWidth: 1.25
  });
  // Published (full-shot) aim oval.
  drawOval(ctx, proj, cell.aim.x, cell.aim.y, cell.sigma_d_yd, cell.sigma_l_yd, {
    stroke: colors.clayText, fill: hexA(colors.clay, 0.12), nSigma: 1, lineWidth: 2
  });

  drawPinMarker(ctx, proj, p.x, p.y, colors.ink);
  var aimPx = proj.toPx(cell.aim.x, cell.aim.y);
  ctx.beginPath();
  ctx.arc(aimPx[0], aimPx[1], 3, 0, Math.PI * 2);
  ctx.fillStyle = colors.clayText;
  ctx.fill();

  labelPlate(ctx, 4, 4, 210, 18, colors);
  label(ctx, 10, 18, PIN_LABELS[pin] + " · " + TIER_LABELS[tier] + (wind ? " · wind" : ""),
    colors.inkSoft, {size: 10.5});
  labelPlate(ctx, 4, canvas.height - 22, 260, 18, colors);
  label(ctx, 10, canvas.height - 12,
    "aim: " + fmt1(cell.aim.lateral_offset_yd) + " lat / " + fmt1(cell.aim.carry_adjustment_yd) + " carry yd",
    colors.muted, {size: 9.5});
}

// ---------------------------------------------------------------
// Chapter 5 (wind): calm vs windy oval overlay, one tier, Sunday
// pin.
// ---------------------------------------------------------------
function drawWindFigure(canvas, data, tier, showWind){
  var ctx = canvas.getContext("2d");
  var colors = readColors();
  var proj = makeProjector(canvas);
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  proj.drawBase(ctx);

  var p = data.pins.sunday;
  var calmCell = data.cells[cellKey(tier, "sunday", false)];
  drawOval(ctx, proj, p.x, p.y, calmCell.sigma_d_calm_yd, calmCell.sigma_l_calm_yd, {
    stroke: colors.clayText, fill: hexA(colors.clay, 0.1), nSigma: 1, lineWidth: 2
  });

  if (showWind){
    var windCell = data.cells[cellKey(tier, "sunday", true)];
    var windCenterY = p.y - data.wind.carry_penalty_yd;
    drawOval(ctx, proj, p.x, windCenterY, windCell.sigma_d_yd, windCell.sigma_l_yd, {
      stroke: colors.blueText, fill: hexA(colors.blue, 0.12), nSigma: 1, lineWidth: 2
    });
  }

  drawPinMarker(ctx, proj, p.x, p.y, colors.ink);
  labelPlate(ctx, 4, 4, 190, 18, colors);
  label(ctx, 10, 18, "Sunday pin · " + TIER_LABELS[tier], colors.inkSoft, {size: 10.5});
  var windLine = showWind ? "clay = calm oval, blue = windy oval (shifted " + data.wind.carry_penalty_yd + " yd short, "
      + data.wind.dispersion_inflation + "x wider)"
      : "clay = calm oval";
  ctx.font = "500 9.5px 'IBM Plex Mono', ui-monospace, monospace";
  labelPlate(ctx, 4, canvas.height - 22, Math.min(canvas.width - 8, ctx.measureText(windLine).width + 14), 18, colors);
  label(ctx, 10, canvas.height - 12, windLine, colors.muted, {size: 9.5});
}

// ---------------------------------------------------------------
// Chapter 7: per-year bar chart with the model's season mean line.
// Static figures the article states in prose (Anchor 9 / VALIDATION_
// NOTES.md), not part of data/003_chapters.json -- this chapter is
// about the Tour oval's own validation record, not an aim verdict.
// ---------------------------------------------------------------
var HOLE12_YEARS = [
  {year: 2019, avg: 3.053}, {year: 2021, avg: 3.11}, {year: 2022, avg: 3.233},
  {year: 2023, avg: 3.058}, {year: 2024, avg: 3.198}, {year: 2025, avg: 3.139}
];
var MODEL_SEASON_MEAN = 3.1188;

function drawYearBarChart(canvas){
  var ctx = canvas.getContext("2d");
  var colors = readColors();
  var w = canvas.width, h = canvas.height;
  ctx.clearRect(0, 0, w, h);

  var padL = 42, padR = 16, padT = 40, padB = 30;
  var plotW = w - padL - padR, plotH = h - padT - padB;
  var vMin = 3.0, vMax = 3.3;
  function yFor(v){ return padT + plotH * (1 - (v - vMin) / (vMax - vMin)); }

  // Legend, fixed in the top margin so it never competes with a bar's own
  // value label for vertical space (the model's own mean sits close enough
  // to two of the six published years that an in-line label collided with
  // their value labels).
  ctx.setLineDash([5, 4]);
  ctx.strokeStyle = colors.blueText;
  ctx.lineWidth = 1.75;
  ctx.beginPath(); ctx.moveTo(padL, 14); ctx.lineTo(padL + 22, 14); ctx.stroke();
  ctx.setLineDash([]);
  label(ctx, padL + 28, 17, "model season mean, " + MODEL_SEASON_MEAN.toFixed(4), colors.blueText, {size: 10.5});

  ctx.strokeStyle = colors.line;
  ctx.lineWidth = 1;
  ctx.beginPath(); ctx.moveTo(padL, padT); ctx.lineTo(padL, padT + plotH); ctx.lineTo(padL + plotW, padT + plotH); ctx.stroke();

  var barW = plotW / HOLE12_YEARS.length * 0.6;
  var step = plotW / HOLE12_YEARS.length;
  HOLE12_YEARS.forEach(function(d, i){
    var x = padL + step * i + (step - barW) / 2;
    var y0 = yFor(vMin), y1 = yFor(d.avg);
    ctx.fillStyle = colors.clayText;
    ctx.fillRect(x, y1, barW, y0 - y1);
    label(ctx, x + barW / 2, padT + plotH + 16, String(d.year), colors.inkSoft, {size: 10.5, align: "center"});
    label(ctx, x + barW / 2, y1 - 5, d.avg.toFixed(3), colors.ink, {size: 9.5, align: "center"});
  });

  var lineY = yFor(MODEL_SEASON_MEAN);
  ctx.setLineDash([5, 4]);
  ctx.strokeStyle = colors.blueText;
  ctx.lineWidth = 1.75;
  ctx.beginPath(); ctx.moveTo(padL, lineY); ctx.lineTo(padL + plotW, lineY); ctx.stroke();
  ctx.setLineDash([]);

  [3.0, 3.1, 3.2, 3.3].forEach(function(v){
    label(ctx, padL - 6, yFor(v) + 3, v.toFixed(1), colors.muted, {size: 9.5, align: "right"});
  });
}

// ---------------------------------------------------------------
// Step -> figure wiring per chapter.
// ---------------------------------------------------------------
function renderStep(chapterEl, stepEl){
  if (!chaptersData) return;
  var canvas = chapterEl.querySelector("canvas");
  if (!canvas) return;
  var kind = chapterEl.getAttribute("data-figure");
  var tier = parseInt(stepEl.getAttribute("data-tier"), 10);
  var wind = stepEl.getAttribute("data-wind") === "1";
  var pin = stepEl.getAttribute("data-pin");

  if (kind === "all-tiers"){
    drawAllTiersFigure(canvas, chaptersData);
  } else if (kind === "pin-walk"){
    drawPinFigure(canvas, chaptersData, pin, tier, wind);
    updateStatChips(chapterEl, chaptersData, pin, tier, wind);
  } else if (kind === "wind"){
    drawWindFigure(canvas, chaptersData, isNaN(tier) ? 15 : tier, wind);
  } else if (kind === "bar-chart"){
    drawYearBarChart(canvas);
  }
}

function updateStatChips(chapterEl, data, pin, tier, wind){
  var cell = data.cells[cellKey(tier, pin, wind)];
  if (!cell) return;
  var waterEl = chapterEl.querySelector('[data-stat="water"]');
  var greenEl = chapterEl.querySelector('[data-stat="green"]');
  var deltaEl = chapterEl.querySelector('[data-stat="delta"]');
  if (waterEl) waterEl.textContent = fmtPct(cell.p_water_at_aim) + " (pin " + fmtPct(cell.p_water_at_pin) + ")";
  if (greenEl) greenEl.textContent = fmtPct(cell.p_green_at_aim) + " (pin " + fmtPct(cell.p_green_at_pin) + ")";
  if (deltaEl) deltaEl.textContent = cell.delta_vs_at_pin_strokes.toFixed(3) + " strokes";
}

function setActiveStep(chapterEl, stepEl, stepIndex){
  var steps = chapterEl.querySelectorAll(".step");
  steps.forEach(function(s){ s.classList.remove("is-active"); });
  stepEl.classList.add("is-active");
  renderStep(chapterEl, stepEl);
  var chapterIndex = parseInt(chapterEl.getAttribute("data-chapter"), 10);
  window.__chapterState = {chapter: chapterIndex, step: stepIndex};
}

function wireScrolly(){
  var chapters = document.querySelectorAll(".chapter[data-figure]");
  chapters.forEach(function(chapterEl){
    var steps = chapterEl.querySelectorAll(".step");
    if (!steps.length) return;

    // Render the first step immediately so the figure is never blank
    // before the observer fires (also covers reduced-motion / no-IO
    // environments).
    setActiveStep(chapterEl, steps[0], 0);

    if (!("IntersectionObserver" in window)) return;
    var io = new IntersectionObserver(function(entries){
      entries.forEach(function(entry){
        if (entry.isIntersecting){
          var idx = Array.prototype.indexOf.call(steps, entry.target);
          setActiveStep(chapterEl, entry.target, idx);
        }
      });
    }, {threshold: 0.5, rootMargin: "-15% 0px -35% 0px"});
    steps.forEach(function(s){ io.observe(s); });
  });
}

// ---------------------------------------------------------------
// Deterministic capture mode: ?chapter=N&step=M
// ---------------------------------------------------------------
function buildCaptureCard(chapterEl, stepEl){
  document.body.classList.add("capture-mode");
  chapterEl.classList.add("is-captured");

  var kicker = chapterEl.querySelector(".chapter-kicker");
  var h2 = chapterEl.querySelector("h2");
  var captionSource = stepEl.querySelector(".verdict-line") || stepEl.querySelector("p");
  var caption = captionSource ? captionSource.textContent.trim() : "";

  var card = document.createElement("div");
  card.className = "capture-card";
  card.innerHTML =
    '<div class="capture-kicker">' + (kicker ? kicker.textContent : "Dogleg Data") + '</div>' +
    '<div class="capture-title">' + (h2 ? h2.textContent : "") + '</div>' +
    '<div class="capture-figure"></div>' +
    '<div class="capture-caption"></div>' +
    '<div class="capture-wordmark">Dogleg Data · doglegdata.com/augusta-12</div>';
  document.body.insertBefore(card, document.body.firstChild);

  // Native card is 1080 CSS px wide (see chapters.css); a 968px canvas
  // (card width minus its 56px side padding) renders every figure at 1:1
  // pixel density or better at the export's deviceScaleFactor 1 capture,
  // never upscaled the way the old 640px canvas was inside the old 420px
  // card (which the social export then upscaled again to 1080, softening
  // it twice over).
  var CAPTURE_CANVAS_PX = 968;
  var figureHost = card.querySelector(".capture-figure");
  var canvas = document.createElement("canvas");
  canvas.width = CAPTURE_CANVAS_PX; canvas.height = CAPTURE_CANVAS_PX;
  figureHost.appendChild(canvas);
  card.querySelector(".capture-caption").textContent = caption;

  var origCanvas = chapterEl.querySelector("canvas");
  var kind = chapterEl.getAttribute("data-figure");
  var tier = parseInt(stepEl.getAttribute("data-tier"), 10);
  var wind = stepEl.getAttribute("data-wind") === "1";
  var pin = stepEl.getAttribute("data-pin");
  if (origCanvas) origCanvas.remove();

  if (kind === "all-tiers"){
    drawAllTiersFigure(canvas, chaptersData);
  } else if (kind === "pin-walk"){
    drawPinFigure(canvas, chaptersData, pin, tier, wind);
  } else if (kind === "wind"){
    drawWindFigure(canvas, chaptersData, isNaN(tier) ? 15 : tier, wind);
  } else if (kind === "bar-chart"){
    drawYearBarChart(canvas);
  }

  window.__chapterState = {
    chapter: parseInt(chapterEl.getAttribute("data-chapter"), 10),
    step: Array.prototype.indexOf.call(chapterEl.querySelectorAll(".step"), stepEl)
  };
  // hero.js owns this same global for its own settled-state hook and
  // resets it to false once its own (async-loaded, off-screen in capture
  // mode but still running) animation assets finish loading -- a race
  // that can stomp this capture's own "true" shortly after it is set,
  // well after the QA/social-export reader has already moved on. Pin the
  // flag read-only true from here on, once chapters capture mode has
  // settled, so a later hero.js write can never flip it back.
  try {
    Object.defineProperty(window, "__phaseComplete", {
      configurable: true, enumerable: true,
      get: function(){ return true; },
      set: function(){ /* ignored: capture mode has already settled */ }
    });
  } catch (e) {
    window.__phaseComplete = true;
  }
}

function maybeRenderCaptureMode(){
  var chapterN = qs.get("chapter");
  var stepN = qs.get("step");
  if (chapterN === null) return false;
  var chapterEl = document.querySelector('.chapter[data-chapter="' + chapterN + '"]');
  if (!chapterEl) return false;
  var steps = chapterEl.querySelectorAll(".step");
  var idx = stepN === null ? 0 : parseInt(stepN, 10);
  var stepEl = steps[idx] || steps[0];
  if (!stepEl) return false;
  buildCaptureCard(chapterEl, stepEl);
  return true;
}

// ---------------------------------------------------------------
// Boot
// ---------------------------------------------------------------
function sizeCanvases(){
  document.querySelectorAll(".chapter-figure canvas, .capture-figure canvas").forEach(function(c){
    if (!c.width) c.width = 640;
    if (!c.height) c.height = 640;
  });
}

function loadAerialImage(){
  return new Promise(function(resolve, reject){
    var img = new Image();
    img.onload = function(){ resolve(img); };
    img.onerror = function(){ reject(new Error("failed to load " + AERIAL_IMG_URL)); };
    img.src = AERIAL_IMG_URL;
  });
}

function init(){
  sizeCanvases();
  Promise.all([
    fetch(DATA_URL).then(function(r){ return r.json(); }),
    fetch(AERIAL_MAP_URL).then(function(r){ return r.json(); }),
    loadAerialImage()
  ]).then(function(results){
    chaptersData = results[0];
    aerialMap = results[1];
    aerialImg = results[2];
    aerialReady = true;
    var captured = maybeRenderCaptureMode();
    if (!captured) wireScrolly();
  }).catch(function(err){
    console.error("chapters: failed to load " + DATA_URL + " / " + AERIAL_MAP_URL, err);
  });
}

if (document.readyState === "loading"){
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}

})();

/* ============================================================
   Augusta 12 hero scene (issue #12).
   Canvas 2D only, no libraries. Three offscreen layers composited
   onto one visible canvas each frame:
     base    - hero art, drawn once per resize (object-fit: cover)
     trails  - accumulated flight paths, landing markers, labels,
               tee box outline, landing scatter (baked in, persists)
     overlay - the flying ball, landing impact, in-progress scatter
               fade (cleared and redrawn every frame)

   Camera projection is ported from the manifest's `camera` block: a
   thin-plate spline (TPS) fit to the accepted nano-banana art (release
   003, round six -- see analysis/003-augusta-12/art/README.md and
   art/fit_tps.py), replacing the old piecewise-homography camera
   sketch.py used through round five. A TPS registers every one of its own
   control points exactly and stays smooth in between; there is no more
   closed-form horizon/mid/tee-front breakpoints to port, only the RBF
   weights and affine terms already baked into the manifest.
   ============================================================ */
(function(){
"use strict";

var MODEL_W = 1600, MODEL_H = 900;
var MOBILE_BREAKPOINT = 640;  // matches site.css "phone width"

var STAGGER_S = 1.0;   // seconds between each shot's launch
var FLIGHT_S = 2.2;    // seconds in the air
var IMPACT_S = 0.4;    // squash-and-settle + puff fade
var SCATTER_FADE_S = 0.5;
var APEX_YD = 14;   // apex height in modeled yards, converted to px at the ball's
                    // current depth (see arcPoint) -- tuned so the arc reads as a
                    // rising flight, not a spike; see hero.js polish notes below
var MAX_ARC_LIFT_SCALE = 12.5; // safety-net cap on the px-per-yard used to convert
                    // APEX_YD to a pixel rise (see arcPoint). Round seven's
                    // perspective-backbone camera (#11) keeps pxPerYardAt far
                    // smoother across the flight than the old sparse TPS did, so
                    // this cap rarely binds any more -- kept as a guard against a
                    // future camera refit reintroducing a near-tee scale spike,
                    // not because today's fit needs it. Using one scale per shot
                    // (its own mid-flight depth) keeps the rise a clean h(t)
                    // parabola instead of fighting a scale that changes every frame.
var SCATTER_ALPHA = 0.25;
var DEPTH_CLIP_MARGIN_PX = 12; // never draw above the playfield_y_max_yd line by more than this
var SCATTER_CAP_MOBILE = 600;

var qs = new URLSearchParams(location.search);
var isDev = location.hostname === "localhost" || location.hostname === "127.0.0.1" || location.hostname === "";

// ---------------------------------------------------------------
// Camera projection: thin-plate spline, ported from manifest.camera.
// U(r) = r^2 * log(r), U(0) = 0 -- the standard TPS radial basis. Two
// independent 1-D fits (screen x, screen y) share the same control
// points; cam.weights.wx/wy are the RBF weights, cam.affine.ax/ay the
// [a0,a1,a2] affine terms.
// ---------------------------------------------------------------
function lerp(a, b, t){ return a + (b - a) * t; }
function clamp(v, lo, hi){ return Math.max(lo, Math.min(hi, v)); }

function tpsU(r){
  if (r <= 1e-12) return 0;
  return r * r * Math.log(r);
}

function tpsEval(x_yd, y_yd, controlPoints, w, a){
  var sum = a[0] + a[1] * x_yd + a[2] * y_yd;
  for (var i = 0; i < controlPoints.length; i++){
    var dx = x_yd - controlPoints[i][0];
    var dy = y_yd - controlPoints[i][1];
    sum += w[i] * tpsU(Math.sqrt(dx * dx + dy * dy));
  }
  return sum;
}

function project(x_yd, y_yd, cam){
  var cps = cam.control_points_yd;
  var px = tpsEval(x_yd, y_yd, cps, cam.weights.wx, cam.affine.ax);
  var py = tpsEval(x_yd, y_yd, cps, cam.weights.wy, cam.affine.ay);
  return [px, py];
}

// pxPerYardAt: local lateral scale, a finite difference of the TPS in x
// at (0, y_yd) -- there is no closed-form half-width function anymore, so
// this replaces sketch.py's half_width_px_for/frame_half_width_yd ratio
// with a direct derivative of the fitted warp itself.
var PX_PER_YARD_DELTA = 0.5;
function pxPerYardAt(y_yd, cam){
  var p0 = project(-PX_PER_YARD_DELTA, y_yd, cam);
  var p1 = project(PX_PER_YARD_DELTA, y_yd, cam);
  return (p1[0] - p0[0]) / (2 * PX_PER_YARD_DELTA);
}

// ---------------------------------------------------------------
// Self-test against manifest.landmarks_px -- the TPS's own fitted
// correspondences (one entry per hand-picked/detected landmark: label,
// model_yd, image_px, source), not a nested sketch.py coordinate dump.
//
// Tolerance is no longer sub-pixel (round seven, #11): the camera now fits
// with a deliberate ridge term (lambda=60, see art/fit_tps.py's
// R6_4_LAMBDA) that trades exact interpolation for a smooth-enough warp
// that flight-path arcs stop looping back on themselves. Real landmarks
// (creek/bunker/green-boundary/tee, hand-picked or detected off the art)
// land within SELF_TEST_TOL_REAL_PX; the synthetic homography-backbone
// grid (calibration scaffolding, not measured off the art) is held to the
// looser SELF_TEST_TOL_SYNTHETIC_PX -- both set a little above the worst
// error actually observed in the fit (see art/README.md, round seven).
// ---------------------------------------------------------------
var SELF_TEST_TOL_REAL_PX = 80;
var SELF_TEST_TOL_SYNTHETIC_PX = 160;

function runSelfTest(cam, landmarksPx){
  var pass = 0;
  var failures = [];
  landmarksPx.forEach(function(lm){
    var out = project(lm.model_yd[0], lm.model_yd[1], cam);
    var dx = Math.abs(out[0] - lm.image_px[0]);
    var dy = Math.abs(out[1] - lm.image_px[1]);
    var tol = lm.source === "synthetic_h0" ? SELF_TEST_TOL_SYNTHETIC_PX : SELF_TEST_TOL_REAL_PX;
    if (dx < tol && dy < tol){
      pass++;
    } else {
      failures.push({ name: lm.label, expected: lm.image_px, got: out });
    }
  });
  if (failures.length === 0){
    if (isDev) console.log("hero: projection self-test " + pass + "/" + landmarksPx.length);
  } else {
    console.error("hero: projection self-test " + pass + "/" + landmarksPx.length + " failed", failures);
  }
}

// ---------------------------------------------------------------
// Brand colors, read from the CSS custom properties so the scene
// stays in lockstep with site.css.
// ---------------------------------------------------------------
function readColors(){
  var cs = getComputedStyle(document.documentElement);
  function v(name){ return cs.getPropertyValue(name).trim(); }
  return {
    ink: v("--ink"),
    inkSoft: v("--ink-soft"),
    muted: v("--muted"),
    clay: v("--clay"),
    clayText: v("--clay-text"),
    blue: v("--blue"),
    blueText: v("--blue-text"),
    maroon: v("--maroon"),
    card: v("--card"),
    line: v("--line")
  };
}

function hexToRgb(hex){
  hex = hex.replace("#", "");
  if (hex.length === 3){
    hex = hex.split("").map(function(c){ return c + c; }).join("");
  }
  var n = parseInt(hex, 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

function withAlpha(hex, alpha){
  var rgb = hexToRgb(hex);
  return "rgba(" + rgb[0] + "," + rgb[1] + "," + rgb[2] + "," + alpha + ")";
}

// ---------------------------------------------------------------
// Boot
// ---------------------------------------------------------------
document.addEventListener("DOMContentLoaded", init);

function init(){
  var section = document.getElementById("hero-scene");
  if (!section) return;
  var wrap = document.getElementById("hero-canvas-wrap");
  var visible = document.getElementById("hero-canvas");
  var legendEl = document.getElementById("hero-legend");
  var shotLegendList = document.getElementById("hero-shot-legend-list");
  var captionButtonRow = document.getElementById("hero-replay");

  var COLORS = readColors();
  var OUTCOME_COLOR = {
    green: COLORS.ink,
    bunker: COLORS.clay,
    water: COLORS.blueText,
    short_sided: COLORS.maroon,
    long: COLORS.muted
  };
  var REGION_COLOR = [
    COLORS.ink,      // 0 green
    COLORS.clay,     // 1 front_bunker
    COLORS.clay,     // 2 back_bunker
    COLORS.blueText, // 3 creek
    COLORS.maroon,   // 4 long_trouble
    COLORS.muted,    // 5 long_rough
    COLORS.muted      // 6 greenside_rough
  ];

  function colorFor(outcomeClass){
    return OUTCOME_COLOR[outcomeClass] || COLORS.ink;
  }

  // Offscreen layers, sized on resize.
  var baseCanvas = document.createElement("canvas");
  var trailsCanvas = document.createElement("canvas");
  var overlayCanvas = document.createElement("canvas");
  var baseCtx = baseCanvas.getContext("2d");
  var trailsCtx = trailsCanvas.getContext("2d");
  var overlayCtx = overlayCanvas.getContext("2d");
  var visibleCtx = visible.getContext("2d");

  var dpr = Math.max(1, window.devicePixelRatio || 1);
  var cssW = 0, cssH = 0;
  var isMobile = false;
  var cover = { scale: 1, offsetX: 0, offsetY: 0, imgW: MODEL_W, imgH: MODEL_H };

  var heroImg = new Image();
  var heroImgMobile = new Image();
  var imagesReady = { desktop: false, mobile: false };
  heroImg.onload = function(){ imagesReady.desktop = true; onAssetReady(); };
  heroImgMobile.onload = function(){ imagesReady.mobile = true; onAssetReady(); };
  heroImg.onerror = function(){ console.error("hero: failed to load hero art (003_hero.png)"); };
  heroImgMobile.onerror = function(){ console.error("hero: failed to load mobile hero art (003_hero_mobile.png)"); };
  heroImg.src = "../assets/img/003_hero.png";
  heroImgMobile.src = "../assets/img/003_hero_mobile.png";

  var manifest = null;
  var cam = null;
  var shots = [];
  var pinHunterScatter = [];
  var ready = false;

  fetch("data/003_manifest.json")
    .then(function(r){
      if (!r.ok) throw new Error("manifest fetch failed: " + r.status);
      return r.json();
    })
    .then(function(m){
      manifest = m;
      cam = m.camera;
      shots = m.shots;
      runSelfTest(cam, m.landmarks_px);
      var pinHunter = shots.filter(function(s){ return s.id === "pin_hunter"; })[0] || shots[0];
      var key = pinHunter.tier + "|" + pinHunter.pin + "|" + (pinHunter.wind ? 1 : 0);
      var scatterSet = m.scatter[key];
      pinHunterScatter = scatterSet ? scatterSet.points : [];
      populateShotLegend(shotLegendList, shots);
      ready = true;
      onAssetReady();
    })
    .catch(function(err){
      console.error("hero: could not load manifest", err);
    });

  function onAssetReady(){
    if (!ready || !imagesReady.desktop || !imagesReady.mobile) return;
    resize();
    window.__heroState = { phase: "idle", shotsLanded: 0 };
    window.__phaseComplete = false;
    startSequence();
  }

  // ---------------------------------------------------------------
  // Sizing / cover transform
  // ---------------------------------------------------------------
  function resize(){
    var rect = wrap.getBoundingClientRect();
    cssW = Math.max(1, Math.round(rect.width));
    cssH = Math.max(1, Math.round(rect.height));
    isMobile = window.matchMedia("(max-width:" + MOBILE_BREAKPOINT + "px)").matches;

    [visible, baseCanvas, trailsCanvas, overlayCanvas].forEach(function(c){
      c.width = cssW * dpr;
      c.height = cssH * dpr;
    });
    visible.style.width = cssW + "px";
    visible.style.height = cssH + "px";

    [baseCtx, trailsCtx, overlayCtx, visibleCtx].forEach(function(ctx){
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    });

    var imgW = isMobile ? 506 : MODEL_W;
    var imgH = MODEL_H;
    var scale = Math.max(cssW / imgW, cssH / imgH);
    cover = {
      scale: scale,
      offsetX: (cssW - imgW * scale) / 2,
      offsetY: (cssH - imgH * scale) / 2,
      imgW: imgW,
      imgH: imgH
    };

    drawBase();
    rebuildTrails();
  }

  function toScreen(mx, my){
    var ix = isMobile ? mx - cam.mobile_crop_x0 : mx;
    return [cover.offsetX + ix * cover.scale, cover.offsetY + my * cover.scale];
  }

  function drawBase(){
    baseCtx.clearRect(0, 0, cssW, cssH);
    var img = isMobile ? heroImgMobile : heroImg;
    baseCtx.drawImage(img, cover.offsetX, cover.offsetY, cover.imgW * cover.scale, cover.imgH * cover.scale);
  }

  // playfieldLimitPy: the fitted image y of the (x_yd, playfield_y_max_yd)
  // line -- the TPS camera's own trusted depth limit, replacing the old
  // fixed horizon_px constant a piecewise camera could give in closed
  // form. Computed per-x since a TPS's depth line need not be flat.
  function playfieldLimitPy(x_yd, cam){
    return project(x_yd, cam.playfield_y_max_yd, cam)[1];
  }

  // ---------------------------------------------------------------
  // Flight math (model space, then projected + transformed to screen)
  // ---------------------------------------------------------------
  function arcPoint(shot, t){
    var x = lerp(shot.tee.x, shot.landing.x, t) + (shot.curve_yd || 0) * Math.sin(Math.PI * t);
    var y = lerp(shot.tee.y, shot.landing.y, t);
    // Clamp to the TPS's trusted depth (playfield_y_max_yd) so a shot
    // landing past it (or a ball whose apex would push it above that
    // line) settles at the clipped edge instead of drawing over the tree
    // line -- same rule the scatter cloud uses in bakeScatter.
    var yClamped = Math.min(y, cam.playfield_y_max_yd);
    var h = APEX_YD * 4 * t * (1 - t);
    var p = project(x, yClamped, cam);
    // liftScale is a per-shot constant (this shot's own mid-flight depth),
    // not re-evaluated every t, so the rise stays a clean h(t) parabola in
    // screen space -- see MAX_ARC_LIFT_SCALE above for why.
    var refY = Math.min((shot.tee.y + shot.landing.y) / 2, cam.playfield_y_max_yd);
    var liftScale = Math.min(pxPerYardAt(refY, cam), MAX_ARC_LIFT_SCALE);
    var py = p[1] - h * liftScale;
    py = Math.max(py, playfieldLimitPy(x, cam) - DEPTH_CLIP_MARGIN_PX);
    var screen = toScreen(p[0], py);
    return { px: screen[0], py: screen[1], x: x, y: yClamped };
  }

  // ---------------------------------------------------------------
  // Drawing helpers
  // ---------------------------------------------------------------
  function drawTeeBoxOutline(ctx){
    var tee = manifest.geometry_yd.tee_box;
    ctx.save();
    ctx.strokeStyle = withAlpha(COLORS.ink, 0.22);
    ctx.lineWidth = 1;
    ctx.beginPath();
    tee.forEach(function(pt, i){
      var proj = project(pt[0], pt[1], cam);
      var s = toScreen(proj[0], proj[1]);
      if (i === 0) ctx.moveTo(s[0], s[1]); else ctx.lineTo(s[0], s[1]);
    });
    ctx.closePath();
    ctx.stroke();
    ctx.restore();
  }

  // The accepted nano-banana art (round six) carries no painted flags --
  // the art's own single flagstick was clone-stamped out (see
  // analysis/003-augusta-12/art/README.md) so the three modeled pins
  // never look like a fourth, wrong one. The page draws all three itself,
  // at the model's own projected pin positions, so the hole locations the
  // prose discusses are visible on the hero at all.
  function drawPins(ctx){
    var pins = manifest.geometry_yd.pins;
    Object.keys(pins).forEach(function(key){
      var p = pins[key];
      var proj = project(p.x, p.y, cam);
      var base = toScreen(proj[0], proj[1]);
      var stickPx = 16 * cover.scale;
      var bx = base[0], by = base[1];
      ctx.save();
      ctx.strokeStyle = COLORS.ink;
      ctx.lineWidth = 1.25;
      ctx.beginPath();
      ctx.moveTo(bx, by);
      ctx.lineTo(bx, by - stickPx);
      ctx.stroke();
      ctx.fillStyle = COLORS.clayText;
      ctx.strokeStyle = COLORS.ink;
      ctx.lineWidth = 0.75;
      ctx.beginPath();
      ctx.moveTo(bx, by - stickPx);
      ctx.lineTo(bx + stickPx * 0.62, by - stickPx + stickPx * 0.22);
      ctx.lineTo(bx, by - stickPx + stickPx * 0.44);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
      ctx.beginPath();
      ctx.arc(bx, by, 1.75, 0, Math.PI * 2);
      ctx.fillStyle = COLORS.ink;
      ctx.fill();
      ctx.restore();
    });
  }

  function strokeTrailSegment(ctx, shot, fromT, toT, steps){
    ctx.save();
    ctx.strokeStyle = colorFor(shot.outcome_class);
    ctx.lineWidth = 2;
    ctx.lineCap = "round";
    ctx.setLineDash(shot.outcome_class === "bunker" ? [6, 4] : []);
    ctx.beginPath();
    var n = steps || 1;
    for (var i = 0; i <= n; i++){
      var t = lerp(fromT, toT, i / n);
      var pt = arcPoint(shot, t);
      if (i === 0) ctx.moveTo(pt.px, pt.py); else ctx.lineTo(pt.px, pt.py);
    }
    ctx.stroke();
    ctx.restore();
  }

  function drawBall(ctx, pt){
    ctx.save();
    ctx.fillStyle = COLORS.card;
    ctx.strokeStyle = COLORS.ink;
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.arc(pt.px, pt.py, 5, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();
    ctx.restore();
  }

  function drawImpact(ctx, shot, pt, progress){
    // progress: 0..1 across IMPACT_S. First half squashes, then a puff
    // (dust on land, a ring on water) fades over the full window.
    ctx.save();
    var squashT = clamp(progress / 0.5, 0, 1);
    var rx = lerp(5, 8, squashT < 1 ? 1 - Math.abs(0.5 - squashT) * 2 : 0);
    var ry = lerp(5, 3, squashT < 1 ? Math.abs(0.5 - squashT) * 2 : 1);
    ctx.fillStyle = COLORS.card;
    ctx.strokeStyle = COLORS.ink;
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.ellipse(pt.px, pt.py, Math.max(3, rx), Math.max(3, ry), 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();

    var puffAlpha = 1 - progress;
    if (shot.outcome_class === "water"){
      ctx.strokeStyle = withAlpha(COLORS.blueText, puffAlpha * 0.8);
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(pt.px, pt.py, lerp(3, 16, progress), 0, Math.PI * 2);
      ctx.stroke();
    } else {
      ctx.fillStyle = withAlpha(COLORS.muted, puffAlpha * 0.35);
      ctx.beginPath();
      ctx.arc(pt.px, pt.py, lerp(4, 14, progress), 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.restore();
  }

  function bakeLandingMarker(ctx, shot, pt){
    ctx.save();
    var color = colorFor(shot.outcome_class);
    if (shot.outcome_class === "short_sided"){
      var s = 9;
      ctx.fillStyle = COLORS.card;
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.fillRect(pt.px - s / 2, pt.py - s / 2, s, s);
      ctx.strokeRect(pt.px - s / 2, pt.py - s / 2, s, s);
    } else if (shot.outcome_class === "water"){
      ctx.strokeStyle = color;
      ctx.lineWidth = 1.5;
      [5, 9].forEach(function(r){
        ctx.beginPath();
        ctx.arc(pt.px, pt.py, r, 0, Math.PI * 2);
        ctx.stroke();
      });
    } else if (shot.outcome_class === "bunker"){
      ctx.fillStyle = color;
      ctx.strokeStyle = COLORS.ink;
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.arc(pt.px, pt.py, 6, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
    } else {
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(pt.px, pt.py, 5, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.restore();
  }

  function boxesOverlap(a, b){
    return !(a.x + a.w < b.x || b.x + b.w < a.x || a.y + a.h < b.y || b.y + b.h < a.y);
  }

  function bakeLabel(ctx, shot, pt, index, placedBoxes){
    ctx.save();
    if (isMobile){
      var r = 8;
      ctx.fillStyle = COLORS.ink;
      ctx.beginPath();
      ctx.arc(pt.px + 12, pt.py - 12, r, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = COLORS.card;
      ctx.font = "500 9px 'IBM Plex Mono', ui-monospace, monospace";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(String(index + 1), pt.px + 12, pt.py - 11.5);
      ctx.restore();
      return;
    }

    ctx.font = "500 11px 'IBM Plex Mono', ui-monospace, monospace";
    var text = shot.label.toUpperCase();
    var textW = ctx.measureText(text).width;
    var padX = 6, h = 16, w = textW + padX * 2;
    var leaderLen = 20; // gap between marker and label box, filled by the leader line
    // Push the label outward from the fairway's centerline -- left-of-center
    // landings get their label further left, right-of-center further right --
    // so labels spread apart instead of stacking toward the middle.
    var outward = shot.landing.x < 0 ? -1 : 1;
    var candidates = outward < 0
      ? [[-leaderLen - w, -14], [-leaderLen - w, 14], [10, -14], [10, 14], [-leaderLen - w, -32], [-leaderLen - w, 32]]
      : [[leaderLen, -14], [leaderLen, 14], [-10 - w, -14], [-10 - w, 14], [leaderLen, -32], [leaderLen, 32]];
    var chosen = candidates[0];
    for (var i = 0; i < candidates.length; i++){
      var dx = candidates[i][0], dy = candidates[i][1];
      var box = { x: pt.px + dx, y: pt.py + dy - h / 2, w: w, h: h };
      var overlaps = placedBoxes.some(function(b){ return boxesOverlap(b, box); });
      if (!overlaps){ chosen = candidates[i]; placedBoxes.push(box); break; }
      if (i === candidates.length - 1) placedBoxes.push(box);
    }
    var lx = pt.px + chosen[0], ly = pt.py + chosen[1];

    // Leader line from the marker to whichever box edge sits closest to it.
    var boxLeft = lx - padX, boxRight = lx - padX + w;
    var nearX = chosen[0] < 0 ? boxRight : boxLeft;
    ctx.strokeStyle = withAlpha(COLORS.ink, 0.4);
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(pt.px, pt.py);
    ctx.lineTo(nearX, ly);
    ctx.stroke();

    ctx.fillStyle = withAlpha(COLORS.card, 0.92);
    ctx.strokeStyle = COLORS.line;
    ctx.lineWidth = 1;
    ctx.fillRect(boxLeft, ly - h / 2, w, h);
    ctx.strokeRect(boxLeft, ly - h / 2, w, h);
    ctx.fillStyle = COLORS.inkSoft;
    ctx.textAlign = "left";
    ctx.textBaseline = "middle";
    ctx.fillText(text, lx, ly + 0.5);
    ctx.restore();
  }

  function scatterPointsForDraw(){
    var pts = pinHunterScatter;
    if (isMobile && pts.length > SCATTER_CAP_MOBILE){
      pts = pts.slice(0, SCATTER_CAP_MOBILE);
    }
    return pts;
  }

  function bakeScatter(ctx, alpha){
    scatterPointsForDraw().forEach(function(p){
      var x_yd = p[0], y_yd = p[1];
      // Drop points beyond the TPS's trusted depth (playfield_y_max_yd) or
      // that would project above that line's own fitted image -- those are
      // the dots that otherwise appear floating over the tree line.
      if (y_yd > cam.playfield_y_max_yd) return;
      var proj = project(x_yd, y_yd, cam);
      if (proj[1] < playfieldLimitPy(x_yd, cam) - DEPTH_CLIP_MARGIN_PX) return;
      if (proj[0] < 0 || proj[0] > cam.canvas.width || proj[1] > cam.canvas.height) return;
      var s = toScreen(proj[0], proj[1]);
      var color = REGION_COLOR[p[2]] || COLORS.ink;
      ctx.fillStyle = withAlpha(color, alpha);
      ctx.beginPath();
      ctx.arc(s[0], s[1], 2, 0, Math.PI * 2);
      ctx.fill();
    });
  }

  function drawScatterFading(ctx, progress){
    bakeScatter(ctx, SCATTER_ALPHA * progress);
  }

  // ---------------------------------------------------------------
  // Legend
  // ---------------------------------------------------------------
  function showLegend(){
    if (legendEl) legendEl.hidden = false;
  }

  function populateShotLegend(listEl, shotList){
    if (!listEl) return;
    listEl.innerHTML = "";
    shotList.forEach(function(shot, i){
      var li = document.createElement("li");
      var num = document.createElement("span");
      num.className = "num";
      num.textContent = String(i + 1);
      var label = document.createElement("span");
      label.textContent = shot.label;
      li.appendChild(num);
      li.appendChild(label);
      listEl.appendChild(li);
    });
  }

  // ---------------------------------------------------------------
  // State machine
  // ---------------------------------------------------------------
  var shotStates = [];
  var scatterState = { phase: "pending", startElapsed: 0 };
  var startTime = 0;
  var pausedAccum = 0;
  var pausedAt = null;
  var running = false;
  var rafId = null;
  var frameTimes = [];
  var labelBoxes = [];

  function resetState(){
    shotStates = shots.map(function(){ return { phase: "pending", t: 0, impactStart: null }; });
    scatterState = { phase: "pending", startElapsed: 0 };
    frameTimes = [];
    labelBoxes = [];
    trailsCtx.clearRect(0, 0, cssW, cssH);
    drawTeeBoxOutline(trailsCtx);
    drawPins(trailsCtx);
    if (legendEl) legendEl.hidden = true;
  }

  function elapsedSeconds(now){
    return (now - startTime - pausedAccum) / 1000;
  }

  function tick(now){
    if (!running) return;
    var frameStart = performance.now();
    var elapsed = elapsedSeconds(now);
    var shotsLanded = 0;

    shotStates.forEach(function(st, i){
      if (st.phase === "done") shotsLanded++;
    });

    shotStates.forEach(function(st, i){
      var shot = shots[i];
      var launchAt = i * STAGGER_S;
      if (st.phase === "pending" && elapsed >= launchAt){
        st.phase = "flying";
        st.t = 0;
      }
      if (st.phase === "flying"){
        var t = clamp((elapsed - launchAt) / FLIGHT_S, 0, 1);
        strokeTrailSegment(trailsCtx, shot, st.t, t, Math.max(1, Math.round((t - st.t) * 40)));
        st.t = t;
        if (t >= 1){
          st.phase = "impact";
          st.impactStart = elapsed;
        }
      }
      if (st.phase === "impact"){
        var dt = elapsed - st.impactStart;
        if (dt >= IMPACT_S){
          var pt = arcPoint(shot, 1);
          bakeLandingMarker(trailsCtx, shot, pt);
          st.phase = "done";
          shotsLanded++;
        }
      }
    });

    // labels: bake once, right after this shot's marker settles, using
    // every already-landed shot's marker box so later labels dodge earlier ones
    shotStates.forEach(function(st, i){
      if (st.phase === "done" && !st.labeled){
        var pt = arcPoint(shots[i], 1);
        bakeLabel(trailsCtx, shots[i], pt, i, labelBoxes);
        st.labeled = true;
      }
    });

    if (shotsLanded >= 1) showLegend();

    if (shotsLanded >= shots.length){
      if (scatterState.phase === "pending"){
        scatterState.phase = "fading";
        scatterState.startElapsed = elapsed;
      }
      if (scatterState.phase === "fading"){
        var sp = clamp((elapsed - scatterState.startElapsed) / SCATTER_FADE_S, 0, 1);
        if (sp >= 1){
          bakeScatter(trailsCtx, SCATTER_ALPHA);
          scatterState.phase = "done";
        }
      }
    }

    // overlay: transient stuff only, redrawn fresh every frame
    overlayCtx.clearRect(0, 0, cssW, cssH);
    shotStates.forEach(function(st, i){
      var shot = shots[i];
      if (st.phase === "flying"){
        drawBall(overlayCtx, arcPoint(shot, st.t));
      } else if (st.phase === "impact"){
        var dt2 = elapsed - st.impactStart;
        drawImpact(overlayCtx, shot, arcPoint(shot, 1), clamp(dt2 / IMPACT_S, 0, 1));
      }
    });
    if (scatterState.phase === "fading"){
      var sp2 = clamp((elapsed - scatterState.startElapsed) / SCATTER_FADE_S, 0, 1);
      drawScatterFading(overlayCtx, sp2);
    }

    compositeFrame();

    window.__heroState = {
      phase: shotsLanded >= shots.length && scatterState.phase === "done" ? "settled" : "flying",
      shotsLanded: shotsLanded
    };

    if (frameTimes.length < 30){
      frameTimes.push(performance.now() - frameStart);
      if (frameTimes.length === 30){
        var avg = frameTimes.reduce(function(a, b){ return a + b; }, 0) / 30;
        if (avg > 40){
          console.info("hero: average frame time " + avg.toFixed(1) + "ms over 30 frames, falling back to settled render");
          running = false;
          renderSettled(shots.length);
          return;
        }
      }
    }

    if (shotsLanded >= shots.length && scatterState.phase === "done"){
      running = false;
      window.__phaseComplete = true;
      return;
    }

    rafId = requestAnimationFrame(tick);
  }

  function compositeFrame(){
    visibleCtx.save();
    visibleCtx.setTransform(1, 0, 0, 1, 0, 0);
    visibleCtx.clearRect(0, 0, visible.width, visible.height);
    visibleCtx.drawImage(baseCanvas, 0, 0);
    visibleCtx.drawImage(trailsCanvas, 0, 0);
    visibleCtx.drawImage(overlayCanvas, 0, 0);
    visibleCtx.restore();
  }

  function rebuildTrails(){
    // Redraws everything baked so far from recorded shot state. Used on
    // resize, since trail pixels are baked at absolute screen coordinates.
    trailsCtx.clearRect(0, 0, cssW, cssH);
    drawTeeBoxOutline(trailsCtx);
    drawPins(trailsCtx);
    if (!shotStates.length) { compositeFrame(); return; }
    var placedBoxes = [];
    shotStates.forEach(function(st, i){
      var shot = shots[i];
      if (st.phase === "pending") return;
      var toT = st.phase === "flying" ? st.t : 1;
      strokeTrailSegment(trailsCtx, shot, 0, toT, 60);
      if (st.phase === "impact" || st.phase === "done"){
        bakeLandingMarker(trailsCtx, shot, arcPoint(shot, 1));
      }
    });
    shotStates.forEach(function(st, i){
      if (st.phase === "done"){
        bakeLabel(trailsCtx, shots[i], arcPoint(shots[i], 1), i, placedBoxes);
      }
    });
    if (scatterState.phase === "done"){
      bakeScatter(trailsCtx, SCATTER_ALPHA);
    }
    compositeFrame();
  }

  // ---------------------------------------------------------------
  // Settled render (deterministic hooks + degrade paths)
  // ---------------------------------------------------------------
  function renderSettled(n){
    resetState();
    var placedBoxes = [];
    for (var i = 0; i < n; i++){
      shotStates[i].phase = "done";
      shotStates[i].t = 1;
      strokeTrailSegment(trailsCtx, shots[i], 0, 1, 60);
      bakeLandingMarker(trailsCtx, shots[i], arcPoint(shots[i], 1));
    }
    for (var j = 0; j < n; j++){
      bakeLabel(trailsCtx, shots[j], arcPoint(shots[j], 1), j, placedBoxes);
    }
    if (n >= 1) showLegend();
    if (n >= shots.length){
      scatterState.phase = "done";
      bakeScatter(trailsCtx, SCATTER_ALPHA);
    }
    overlayCtx.clearRect(0, 0, cssW, cssH);
    compositeFrame();
    window.__heroState = { phase: "settled", shotsLanded: n };
    window.__phaseComplete = true;
  }

  // ---------------------------------------------------------------
  // Sequence start / degrade paths / replay
  // ---------------------------------------------------------------
  function startSequence(){
    var reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    var shotParam = qs.get("shot");

    if (qs.has("settled")){
      renderSettled(shots.length);
      if (captionButtonRow) captionButtonRow.hidden = true;
      return;
    }
    if (shotParam){
      var n = clamp(parseInt(shotParam, 10) || 0, 0, shots.length);
      renderSettled(n);
      if (captionButtonRow) captionButtonRow.hidden = true;
      return;
    }
    if (reducedMotion){
      renderSettled(shots.length);
      return;
    }

    setupObserver();
    playFromStart();
  }

  function playFromStart(){
    resetState();
    startTime = performance.now();
    pausedAccum = 0;
    pausedAt = null;
    running = true;
    window.__phaseComplete = false;
    rafId = requestAnimationFrame(tick);
  }

  function setupObserver(){
    if (!("IntersectionObserver" in window)) return;
    var observer = new IntersectionObserver(function(entries){
      entries.forEach(function(entry){
        if (!entry.isIntersecting){
          if (running){
            running = false;
            pausedAt = performance.now();
            if (rafId) cancelAnimationFrame(rafId);
          }
        } else {
          if (!running && pausedAt !== null && window.__heroState && window.__heroState.phase !== "settled"){
            pausedAccum += performance.now() - pausedAt;
            pausedAt = null;
            running = true;
            rafId = requestAnimationFrame(tick);
          }
        }
      });
    }, { threshold: 0.05 });
    observer.observe(section);
  }

  if (captionButtonRow){
    captionButtonRow.addEventListener("click", function(){
      if (window.matchMedia("(prefers-reduced-motion: reduce)").matches){
        renderSettled(shots.length);
        return;
      }
      if (rafId) cancelAnimationFrame(rafId);
      playFromStart();
    });
  }

  window.addEventListener("resize", debounce(function(){
    if (!ready || !imagesReady.desktop || !imagesReady.mobile) return;
    resize();
  }, 150));

  function debounce(fn, ms){
    var timer = null;
    return function(){
      var args = arguments;
      clearTimeout(timer);
      timer = setTimeout(function(){ fn.apply(null, args); }, ms);
    };
  }
}
})();

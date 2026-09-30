/*
 * The five delivery sliders. Settings come from the slider block of each METRICS
 * entry in tiles.js. Each slider is a native range input (keyboard, touch and
 * screen reader support come with it) plus a visible readout, plus and minus
 * buttons that repeat while held, and a green zone on the track for the ideal band.
 *
 * The readout is aria-hidden: the input carries aria-valuetext, so a screen
 * reader hears one value, not two.
 */
import { METRICS, SLIDER_METRICS, MINUS, DEG, fmt } from "./tiles.js";
import { clamp, snap, round3 } from "./state.js";


/**
 * hooks.live() runs after every change (redraw the numbers and preview the shot).
 * hooks.commitNow() and hooks.commitSoon(ms) fly the shot.
 */
export function createSliders({ model, store, containers, hooks }) {
  const { state } = store;
  const sliders = {};

  function build(metric, container) {
    const m = METRICS[metric];
    const cfg = m.slider;
    const key = cfg.stateKey;
    const label = cfg.label || m.label;
    const id = "sl-" + key;
    const [lo, hi] = model.domain[cfg.dom];
    const unitWord = m.unit === DEG ? " degrees" : " mph";
    const wrap = document.createElement("div");
    wrap.className = "slider";
    wrap.innerHTML = `
      <div class="slider-head"><label for="${id}">${label}</label><span class="val" aria-hidden="true"></span></div>
      <div class="slider-row">
        <button type="button" class="step" data-dir="-1" tabindex="-1" aria-label="Decrease ${label.toLowerCase()} by ${cfg.step}${unitWord}"><span aria-hidden="true">${MINUS}</span></button>
        <div class="track-wrap">
          <span class="track-base"></span><span class="band-hint"></span>${cfg.zero ? '<span class="zero-tick"></span>' : ""}
          <input type="range" id="${id}" min="${lo}" max="${hi}" step="${cfg.step}" value="0">
        </div>
        <button type="button" class="step" data-dir="1" tabindex="-1" aria-label="Increase ${label.toLowerCase()} by ${cfg.step}${unitWord}"><span aria-hidden="true">+</span></button>
      </div>
      ${cfg.hints ? '<div class="slider-hint" aria-hidden="true"><span class="hl"></span><span class="hr"></span></div>' : ""}`;
    container.appendChild(wrap);
    const input = wrap.querySelector("input");
    const val = wrap.querySelector(".val");
    const band = wrap.querySelector(".band-hint");
    const zero = wrap.querySelector(".zero-tick");
    if (zero) zero.style.left = `calc(var(--thumb) / 2 + ${(0 - lo) / (hi - lo)} * (100% - var(--thumb)))`;
    const api = { metric, cfg, key, input, val, band, wrap, lo, hi };
    sliders[metric] = api;

    const nudge = (dir) => {
      const cur = state[key];
      const q = cur / cfg.step;
      const v = clamp(round3(dir > 0 ? (Math.floor(q + 1e-9) + 1) * cfg.step : (Math.ceil(q - 1e-9) - 1) * cfg.step), lo, hi);
      if (v === cur) return;
      state[key] = v;
      store.afterSliderChange(key);
      hooks.live();
      hooks.commitSoon(380);
    };

    input.addEventListener("input", () => {
      const v = clamp(snap(parseFloat(input.value), cfg.step), lo, hi);
      if (v !== state[key]) { state[key] = v; store.afterSliderChange(key); hooks.live(); }
    });
    input.addEventListener("change", () => hooks.commitNow());
    input.addEventListener("keydown", (e) => {
      const steps = { ArrowRight: 1, ArrowUp: 1, ArrowLeft: -1, ArrowDown: -1, PageUp: 5, PageDown: -5 };
      if (e.key in steps) {
        e.preventDefault();
        const n = steps[e.key] * (e.shiftKey ? 5 : 1);
        for (let i = 0; i < Math.abs(n); i++) nudge(Math.sign(n));
      } else if (e.key === "Home" || e.key === "End") {
        e.preventDefault();
        const v = e.key === "Home" ? lo : hi;
        if (v !== state[key]) { state[key] = v; store.afterSliderChange(key); hooks.live(); hooks.commitSoon(380); }
      }
    });

    // Steppers: press, or hold to repeat. They stay out of the tab order: the
    // slider itself takes arrow keys.
    for (const btn of wrap.querySelectorAll(".step")) {
      const dir = Number(btn.dataset.dir);
      let hold = 0, rep = 0;
      const stop = () => { clearTimeout(hold); clearInterval(rep); };
      btn.addEventListener("pointerdown", (e) => {
        if (e.button !== undefined && e.button !== 0) return;
        nudge(dir);
        hold = setTimeout(() => { rep = setInterval(() => nudge(dir), 70); }, 420);
      });
      for (const ev of ["pointerup", "pointerleave", "pointercancel"]) btn.addEventListener(ev, stop);
      // Assistive tech activates with click and no pointerdown.
      btn.addEventListener("click", (e) => { if (e.detail === 0) nudge(dir); });
      btn.addEventListener("contextmenu", (e) => e.preventDefault());
    }
  }

  for (const metric of SLIDER_METRICS) {
    build(metric, METRICS[metric].slider.advanced ? containers.adv : containers.main);
  }

  // The switch that lets the dynamic loft follow the attack angle, for every club. It sits
  // under the attack slider, where the golfer is looking when it matters.
  const follow = document.createElement("div");
  follow.className = "loft-follow";
  follow.hidden = true;
  follow.innerHTML = `
    <label class="check"><input type="checkbox" id="loft-follow"> <span>Loft follows attack angle</span></label>
    <p class="follow-note" id="follow-note"></p>
    <p class="follow-hint" id="follow-hint" hidden></p>`;
  sliders.attack_deg.wrap.appendChild(follow);
  // A launch monitor reports the effective loft. Typing that reading into the slider would count the face's share twice.
  const loftHint = document.createElement("p");
  loftHint.className = "follow-hint loft-hint";
  loftHint.hidden = true;
  sliders.dyn_loft_deg.wrap.appendChild(loftHint);
  const followBox = follow.querySelector("input");
  const followNote = follow.querySelector("#follow-note");
  const followHint = follow.querySelector("#follow-hint");
  followBox.addEventListener("change", () => {
    store.setLoftFollows(followBox.checked);
    hooks.live();
    hooks.commitNow();
  });

  /** Sync every slider to the state and the computed shot c. */
  function renderMain(c, hand) {
    for (const metric of SLIDER_METRICS) {
      const api = sliders[metric];
      const m = METRICS[metric];
      const v = state[api.key];
      if (Math.abs(parseFloat(api.input.value) - v) > 1e-6) api.input.value = v;
      const entry = c.values[metric];
      const decs = m.slider.dec === undefined ? m.dec : m.slider.dec;
      const text = fmt(v, decs, m.signed) + (m.unit === DEG ? DEG : " " + m.unit);
      let word = m.words ? m.words(entry.rh, entry.disp, entry) : "";
      // The loft slider reads the loft with the face square to the path. The face note lives on the tile.
      if (metric === "dyn_loft_deg") word = state.loftFollows ? "follows attack" : "";
      api.val.innerHTML = "";
      api.val.append(text);
      if (word) {
        const w = document.createElement("span");
        w.className = "w";
        w.textContent = word;
        api.val.append(w);
      }
      api.input.setAttribute("aria-valuetext", word ? `${text}, ${word}` : text);
      if (metric === "dyn_loft_deg") {
        const off = Math.abs(entry.faceToPathRh) >= 0.05;
        loftHint.hidden = !off;
        if (off) loftHint.textContent = `TrackMan shows the effective loft: ${fmt(entry.disp, 1)}${DEG} here. Enter the loft you would have with the face square to the path.`;
      }
      const b = c.bands[metric];
      if (b) {
        const span = api.hi - api.lo;
        // The loft band is for the effective loft. The slider is the input loft, so shift the band by the difference.
        const shift = metric === "dyn_loft_deg" ? state.dynLoft - entry.disp : 0;
        const l = b.lo === null ? api.lo : b.lo + shift;
        const h = b.hi === null ? api.hi : b.hi + shift;
        api.band.style.setProperty("--p1", clamp((l - api.lo) / span, 0, 1));
        api.band.style.setProperty("--p2", clamp((h - api.lo) / span, 0, 1));
      }
      if (m.slider.hints) {
        const [a, z] = m.slider.hints(hand);
        api.wrap.querySelector(".hl").textContent = a;
        api.wrap.querySelector(".hr").textContent = z;
      }
    }
  }

  const perAttack = model.data.model.coupling.loft_per_attack;

  /** Keep the loft switch and its notes current. The switch shows for every club. */
  const MODELED = ' <span class="badge-modeled">modeled</span>';
  function renderFollow() {
    follow.hidden = false;
    const driver = state.club === "driver";
    followBox.checked = state.loftFollows;
    const chart = store.chartLoft();
    if (state.loftFollows && driver) {
      const off = state.loftOffset;
      const chartTxt = `Chart loft is ${fmt(chart.dynLoft, 1)}${DEG}`;
      let tail = ".";
      if (Math.abs(off) >= 0.05) {
        // Words the golfer's own change differently from a delivery that simply sits off the chart.
        tail = state.loftOffsetIsMine
          ? `, and you added ${fmt(off, 1, true)}${DEG}.`
          : `; this delivery sits ${fmt(Math.abs(off), 1)}${DEG} ${off > 0 ? "above" : "below"} it.`;
      }
      followNote.innerHTML = `${`Loft ${fmt(state.dynLoft, 1)}${DEG} now. ${chartTxt}${tail}`}${MODELED}`;
    } else if (state.loftFollows) {
      const mine = state.loftOffsetIsMine && Math.abs(state.loftOffset) >= 0.05 ? ` You added ${fmt(state.loftOffset, 1, true)}${DEG}.` : "";
      followNote.innerHTML = `${`Loft follows attack: ${perAttack}${DEG} per degree, hitting up adds loft.${mine}`}${MODELED}`;
    } else {
      followNote.textContent = `Loft is fixed at ${fmt(state.dynLoft, 1)}${DEG}.`;
    }
    const notes = [];
    if (driver && state.loftFollows && chart.extrapolated) notes.push(`Attack is outside the chart (${MINUS}5${DEG} to +5${DEG}), so the loft is extended along the chart's slope.`);
    if (driver && state.loftFollows && chart.speedClamped) notes.push("Club speed is outside the chart (75 to 120 mph), so the loft is held at the chart's edge.");
    followHint.hidden = notes.length === 0;
    followHint.textContent = notes.join(" ");
  }

  return { render(c, hand) { renderMain(c, hand); renderFollow(); }, sliders };
}

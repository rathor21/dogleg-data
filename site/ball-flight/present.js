/*
 * Presentation mode for a TV or projector. The Fullscreen API when the browser
 * allows it, and a class on <html> and <body> either way, so the layout works
 * even where fullscreen is refused (an iframe, an older browser). Escape exits.
 * tool.css lays the page out for it: range across the screen, big shot label and
 * key tiles, and the controls in one slim bar at the bottom.
 *
 * options: onChange(on), focusEl (element or selector to focus on entering, the
 * first control in the bar), returnEl (focus on exit, the button that started it).
 */
export function createPresenter({ onChange, focusEl, returnEl }) {
  const btn = document.querySelector("#present-btn");
  const exitBtn = document.querySelector("#exit-present");
  const root = document.documentElement;
  const pick = (x) => (typeof x === "string" ? document.querySelector(x) : x);
  const fsElement = () => document.fullscreenElement || document.webkitFullscreenElement;
  const leaveFullscreen = () => {
    if (!fsElement()) return;
    const out = document.exitFullscreen || document.webkitExitFullscreen;
    try { Promise.resolve(out.call(document)).catch(() => {}); } catch (e) { /* already out */ }
  };
  let on = false;
  let usedFullscreen = false;

  async function enter() {
    if (on) return;
    on = true;
    root.classList.add("presenting");
    document.body.classList.add("presenting");
    usedFullscreen = false;
    try {
      const req = root.requestFullscreen || root.webkitRequestFullscreen;
      if (req) {
        await req.call(root);
        // The request can settle after the user has already left. Do not stay in fullscreen then.
        if (!on) { leaveFullscreen(); return; }
        usedFullscreen = !!fsElement();
      }
    } catch (e) { /* refused: the class still gives the presentation layout */ }
    if (!on) return;
    window.scrollTo(0, 0);
    onChange(true);
    const first = pick(focusEl);
    if (first) first.focus({ preventScroll: true });
  }

  function exit() {
    if (!on) return;
    on = false;
    root.classList.remove("presenting");
    document.body.classList.remove("presenting");
    leaveFullscreen();
    usedFullscreen = false;
    onChange(false);
    const back = pick(returnEl) || btn;
    if (back) back.focus({ preventScroll: true });
  }

  btn.addEventListener("click", () => (on ? exit() : enter()));
  exitBtn.addEventListener("click", exit);
  // Leaving fullscreen with the browser's own Escape ends the mode too.
  document.addEventListener("fullscreenchange", () => {
    if (on && usedFullscreen && !fsElement()) exit();
  });
  // Real fullscreen already exits on Escape, so this mostly covers the class-only fallback.
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && on) { e.preventDefault(); exit(); }
  });

  return { enter, exit, get on() { return on; } };
}

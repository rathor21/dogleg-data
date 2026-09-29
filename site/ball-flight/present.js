/*
 * Presentation mode for a TV or projector. The Fullscreen API when the browser
 * allows it, and a class on <html> and <body> either way, so the layout works
 * even where fullscreen is refused (an iframe, an older browser). Escape exits.
 * tool.css lays the page out for it: range across the screen, big shot label and
 * key tiles, and the controls in one slim bar at the bottom.
 */
export function createPresenter({ onChange }) {
  const btn = document.querySelector("#present-btn");
  const exitBtn = document.querySelector("#exit-present");
  const root = document.documentElement;
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
        usedFullscreen = !!(document.fullscreenElement || document.webkitFullscreenElement);
      }
    } catch (e) { /* refused: the class still gives the presentation layout */ }
    window.scrollTo(0, 0);
    onChange(true);
    const first = document.querySelector("#hit-btn-2");
    if (first) first.focus({ preventScroll: true });
  }

  function exit() {
    if (!on) return;
    on = false;
    root.classList.remove("presenting");
    document.body.classList.remove("presenting");
    const fs = document.fullscreenElement || document.webkitFullscreenElement;
    if (fs) {
      const out = document.exitFullscreen || document.webkitExitFullscreen;
      try { Promise.resolve(out.call(document)).catch(() => {}); } catch (e) { /* already out */ }
    }
    usedFullscreen = false;
    onChange(false);
    btn.focus({ preventScroll: true });
  }

  btn.addEventListener("click", () => (on ? exit() : enter()));
  exitBtn.addEventListener("click", exit);
  // Leaving fullscreen with the browser's own Escape ends the mode too.
  document.addEventListener("fullscreenchange", () => {
    if (on && usedFullscreen && !document.fullscreenElement) exit();
  });
  // Real fullscreen already exits on Escape, so this mostly covers the class-only fallback.
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && on) { e.preventDefault(); exit(); }
  });

  return { enter, exit, get on() { return on; } };
}

/*
 * Club, player, hand and playback-speed controls. All are radio groups: one
 * tab stop per group, arrow keys and Home/End move and pick.
 *
 * The specific-club chips are built once per club group and updated in place
 * after that, so a click or arrow key keeps focus on the chip.
 */
const GROUP_LABEL = { wedge: "Wedges" };
const PLAYER_LABEL = { amateur: "Amateur" };

export function radioGroup(container, onPick) {
  const items = () => [...container.querySelectorAll('[role="radio"]')];
  container.addEventListener("click", (e) => {
    const b = e.target.closest('[role="radio"]');
    if (b && container.contains(b)) onPick(b);
  });
  container.addEventListener("keydown", (e) => {
    const list = items();
    const i = list.indexOf(document.activeElement);
    if (i < 0) return;
    let j;
    if (e.key === "ArrowRight" || e.key === "ArrowDown") j = (i + 1) % list.length;
    else if (e.key === "ArrowLeft" || e.key === "ArrowUp") j = (i - 1 + list.length) % list.length;
    else if (e.key === "Home") j = 0;
    else if (e.key === "End") j = list.length - 1;
    else return;
    e.preventDefault();
    list[j].focus();
    onPick(list[j]);
  });
  return {
    set(pred) {
      for (const b of items()) {
        const on = pred(b);
        b.setAttribute("aria-checked", String(on));
        b.tabIndex = on ? 0 : -1;
      }
    },
  };
}

/**
 * hooks: onClub(id), onGroup(id), onPlayer(id), onHand(h), onSpeed(n).
 * render() reads the store and updates the controls.
 */
export function createControls({ model, store, hooks }) {
  const $ = (s) => document.querySelector(s);
  const groupChips = $("#group-chips");
  const clubChips = $("#club-chips");
  const playerSeg = $("#player-seg");
  const handSeg = $("#hand-seg");
  const speedSeg = $("#speed-seg");
  const noteEl = $("#preset-note");
  const { state } = store;

  groupChips.innerHTML = model.groups
    .map((g) => `<button type="button" class="chip" role="radio" aria-checked="false" data-group="${g.id}">${GROUP_LABEL[g.id] || g.name}</button>`)
    .join("");
  playerSeg.innerHTML = model.players
    .map((p) => `<button type="button" role="radio" aria-checked="false" data-player="${p.id}" title="${p.name}">${PLAYER_LABEL[p.id] || p.name}</button>`)
    .join("");

  const groupRadio = radioGroup(groupChips, (b) => hooks.onGroup(b.dataset.group));
  const clubRadio = radioGroup(clubChips, (b) => hooks.onClub(b.dataset.club));
  const playerRadio = radioGroup(playerSeg, (b) => hooks.onPlayer(b.dataset.player));
  const handRadio = radioGroup(handSeg, (b) => hooks.onHand(b.dataset.hand));
  const speedRadio = radioGroup(speedSeg, (b) => {
    speedRadio.set((x) => x === b);
    hooks.onSpeed(Number(b.dataset.speed));
  });
  speedRadio.set((b) => b.dataset.speed === "1");

  let builtGroup = null;

  function render() {
    const g = store.groupOf();
    groupRadio.set((b) => b.dataset.group === g);
    if (g !== builtGroup) {
      builtGroup = g;
      const clubs = model.clubs.filter((c) => c.group === g);
      clubChips.innerHTML = clubs.length > 1
        ? clubs.map((c) => `<button type="button" class="chip" role="radio" aria-checked="false" data-club="${c.id}">${c.name}</button>`).join("")
        : "";
    }
    clubRadio.set((b) => b.dataset.club === state.club);
    playerRadio.set((b) => b.dataset.player === state.player);
    handRadio.set((b) => b.dataset.hand === state.hand);
    const note = model.preset(state.club, state.player).note;
    noteEl.hidden = !note;
    noteEl.textContent = note || "";
  }

  return { render };
}

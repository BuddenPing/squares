// The homepage changes complete canonical Atlas rows through the shared FLIP engine.
// Every case link and reserved SVG drawing arrives in the server-rendered markup.
(() => {
  const grid = document.querySelector("[data-atlas-preview]");
  const cells = grid?.querySelector(".site-atlas-cells");
  const rest = cells?.querySelector("[data-atlas-rest]");
  const toggle = document.querySelector("[data-homepage-atlas-toggle]");
  const label = toggle?.querySelector("[data-homepage-atlas-label]");
  const chevron = toggle?.querySelector(".site-icon-arrow");
  const status = document.querySelector("[data-homepage-atlas-status]");
  if (
    !(grid instanceof HTMLElement) ||
    !(cells instanceof HTMLElement) ||
    !(rest instanceof HTMLElement) ||
    !(toggle instanceof HTMLButtonElement) ||
    !(label instanceof HTMLElement) ||
    !(status instanceof HTMLElement)
  ) {
    return;
  }
  if (!globalThis.SiteAtlasView) {
    status.textContent =
      "Use Explore the atlas to open the complete page; the preview is still available.";
    status.hidden = false;
    return;
  }
  const rows = [...cells.querySelectorAll(".site-atlas-row")];
  const initialCount = Number(grid.dataset.atlasCount);
  let count = initialCount;

  const relabel = () => {
    const full = count === 324;
    const next = count < 100 ? 100 : 324;
    grid.dataset.atlasCount = String(count);
    toggle.setAttribute("aria-expanded", String(count > initialCount));
    toggle.setAttribute(
      "aria-label",
      full
        ? `Show less: collapse from ${count} to ${initialCount} cases (${Math.sqrt(initialCount)} rows)`
        : `Show more: expand from ${count} to ${next} cases (${Math.sqrt(next)} rows)`,
    );
    label.textContent = full ? "Show Less" : "Show More";
    if (chevron instanceof HTMLElement) {
      chevron.dataset.arrow = full ? "double-up" : "double-down";
    }
  };
  const views = SiteAtlasView.mount({
    block: grid,
    cells,
    tabs: null,
    sizes: null,
    scoped: true,
  });
  toggle.addEventListener("click", () => {
    const next = count < 100 ? 100 : count < 324 ? 324 : initialCount;
    views.change(() => {
      if (next > count) {
        rest.before(...rows.slice(Math.sqrt(count), Math.sqrt(next)));
      } else {
        rest.prepend(...rows.slice(Math.sqrt(next), Math.sqrt(count)));
      }
      count = next;
      const finalRow = rows[Math.sqrt(count) - 1];
      cells.style.setProperty("--site-atlas-widest", String(SiteAtlasView.widest(count)));
      cells.style.setProperty(
        "--site-atlas-extra",
        finalRow?.querySelector('[data-atlas-segment="non-grid"]:not([data-empty])') ? "1" : "0",
      );
      relabel();
      if (count === initialCount) {
        views.arrange();
        toggle.scrollIntoView({ block: "nearest", behavior: "instant" });
      }
    });
  });
  relabel();
  grid.dataset.atlasReady = "true";
  toggle.hidden = false;
})();

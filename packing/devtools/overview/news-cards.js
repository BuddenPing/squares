// News entry cards keep their actual articles; presses only change the visible height.
// Without this enhancement, the complete articles and their ordinary links stay visible.
(() => {
  /** @type {Map<Element, (open: boolean) => void>} */
  const cards = new Map();
  for (const card of document.querySelectorAll("[data-news-day]")) {
    const button = card.querySelector(".site-news-expand");
    const body = card.querySelector(".site-news-body");
    if (
      !(card instanceof HTMLElement) ||
      !(button instanceof HTMLButtonElement) ||
      !(body instanceof HTMLElement)
    ) {
      continue;
    }
    const date = card.querySelector("time")?.textContent ?? card.dataset.newsDay;
    const setOpen = (/** @type {boolean} */ open, animate = true) => {
      if (card.dataset.newsEnhanced && (button.getAttribute("aria-expanded") === "true") === open) {
        return;
      }
      if (animate) {
        body.style.maxBlockSize = `${body.getBoundingClientRect().height}px`;
        // Commit the current height so rapid presses reverse from the visible frame.
        body.getBoundingClientRect();
      }
      card.classList.toggle("is-collapsed", !open);
      body.style.maxBlockSize = open ? `${body.scrollHeight}px` : "10lh";
      if (open && window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
        body.style.removeProperty("max-block-size");
      }
      button.setAttribute("aria-expanded", String(open));
      button.setAttribute("aria-label", `${open ? "Collapse" : "Expand"} news for ${date}`);
      const arrow = button.querySelector("[data-arrow]");
      arrow?.setAttribute("data-arrow", open ? "double-up" : "double-down");
    };
    body.addEventListener("transitionend", (event) => {
      if (
        event.target === body &&
        ["max-block-size", "max-height"].includes(event.propertyName) &&
        button.getAttribute("aria-expanded") === "true"
      ) {
        body.style.removeProperty("max-block-size");
      }
    });
    setOpen(false, false);
    if (body.scrollHeight <= body.clientHeight) {
      setOpen(true, false);
      continue;
    }
    const toggle = () => setOpen(button.getAttribute("aria-expanded") !== "true");
    button.addEventListener("click", toggle);
    card.querySelector(".site-news-body")?.addEventListener("focusin", () => setOpen(true));
    card.addEventListener("click", (event) => {
      if (
        !(event.target instanceof Element) ||
        event.target.closest(
          "a, button, input, select, textarea, summary, details, [contenteditable]",
        ) ||
        window.getSelection()?.isCollapsed === false
      ) {
        return;
      }
      toggle();
    });
    cards.set(card, setOpen);
    card.dataset.newsEnhanced = "true";
    button.hidden = false;
  }
  const reveal = () => {
    const card = document.getElementById(location.hash.slice(1))?.closest("[data-news-day]");
    if (card) {
      cards.get(card)?.(true);
    }
  };
  reveal();
  window.addEventListener("hashchange", reveal);
})();

// Daily News disclosures open inline. Hover/focus expansion is transient until a
// reader pins it with a press or uses the body; native details works without this file.
(() => {
  for (const card of document.querySelectorAll("[data-news-day]")) {
    const summary = card.querySelector("summary");
    if (!(card instanceof HTMLDetailsElement) || !(summary instanceof HTMLElement)) {
      continue;
    }
    const expand = () => {
      if (!card.open) {
        card.dataset.newsTransient = "true";
        card.open = true;
      }
    };
    const leave = () => {
      if (
        card.dataset.newsTransient === "true" &&
        card.dataset.newsPinned !== "true" &&
        !card.matches(":hover") &&
        !card.contains(document.activeElement)
      ) {
        card.open = false;
        delete card.dataset.newsTransient;
      }
    };
    card.addEventListener("pointerenter", (event) => {
      if (event.pointerType !== "touch" && window.matchMedia("(hover: hover)").matches) {
        expand();
      }
    });
    card.addEventListener("pointerleave", leave);
    card.addEventListener("focusin", (event) => {
      if (event.target === summary) {
        expand();
      } else {
        card.dataset.newsPinned = "true";
      }
    });
    card.addEventListener("focusout", () => queueMicrotask(leave));
    summary.addEventListener("click", (event) => {
      if (card.open && card.dataset.newsTransient === "true" && event.detail > 0) {
        event.preventDefault();
        card.dataset.newsPinned = "true";
        delete card.dataset.newsTransient;
      } else {
        card.dataset.newsPinned = String(!card.open);
      }
    });
    card.addEventListener("click", (event) => {
      if (event.target instanceof Node && !summary.contains(event.target)) {
        card.dataset.newsPinned = "true";
      }
    });
    card.addEventListener("toggle", () => {
      if (!card.open) {
        delete card.dataset.newsPinned;
        delete card.dataset.newsTransient;
      }
    });
  }
  const reveal = () => {
    const target = document.getElementById(location.hash.slice(1));
    const card = target?.closest("[data-news-day]");
    if (card instanceof HTMLDetailsElement) {
      card.open = true;
      card.dataset.newsPinned = "true";
      delete card.dataset.newsTransient;
    }
  };
  reveal();
  window.addEventListener("hashchange", reveal);
})();

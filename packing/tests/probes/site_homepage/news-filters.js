// The archive's actual facets, disclosed cards, centered controls and shared meters.
/** @param {{ meters?: string } | null} options */
(options) => {
  const { meters = "" } = options ?? {};
  const controls = document.querySelector("[data-news-filters]");
  const specimen = document.createElement("div");
  specimen.innerHTML = meters;
  document.querySelector(".site-page")?.append(specimen);
  const samples = [...specimen.querySelectorAll(".site-significance")].map((meter) => {
    const style = getComputedStyle(meter);
    const bars = [...meter.querySelectorAll(".site-significance-bar")];
    return {
      level: Number(meter.getAttribute("data-level")),
      label: meter.getAttribute("aria-label"),
      width: meter.getBoundingClientRect().width,
      font: Number.parseFloat(style.fontSize),
      border: Number.parseFloat(style.borderTopWidth),
      filled: bars.filter((bar) => bar.getAttribute("data-filled") === "true").length,
      bars: bars.map((bar) => ({
        height: bar.getBoundingClientRect().height,
        width: bar.getBoundingClientRect().width,
        fill: getComputedStyle(bar).backgroundColor,
        border: Number.parseFloat(getComputedStyle(bar).borderTopWidth),
        filled: bar.getAttribute("data-filled") === "true",
      })),
    };
  });
  specimen.remove();
  return {
    scores: [
      ...(controls?.querySelectorAll('button[data-news-score][aria-pressed="true"]') ?? []),
    ].map((button) => button.getAttribute("data-news-score")),
    topics: [
      ...(controls?.querySelectorAll('button[data-news-topic][aria-pressed="true"]') ?? []),
    ].map((button) => button.getAttribute("data-news-topic")),
    controls_hidden: controls instanceof HTMLElement && controls.hidden,
    count: controls?.querySelector("[data-news-count]")?.textContent,
    empty:
      controls?.querySelector("[data-news-empty]") instanceof HTMLElement &&
      !controls.querySelector("[data-news-empty]")?.hasAttribute("hidden"),
    cards: [...document.querySelectorAll("[data-news-day]")].map((card) => {
      const box = card.getBoundingClientRect();
      const button = card.querySelector(".site-news-expand");
      const buttonBox = button?.getBoundingClientRect();
      const body = card.querySelector(".site-news-body");
      return {
        id: card.id,
        visible: card.getClientRects().length > 0,
        score: Number(card.getAttribute("data-news-score")),
        topics: (card.getAttribute("data-news-topics") || "").split(" ").filter(Boolean),
        expanded: button?.getAttribute("aria-expanded"),
        button_hidden: button instanceof HTMLButtonElement && button.hidden,
        center_offset: buttonBox
          ? (buttonBox.left + buttonBox.right - box.left - box.right) / 2
          : null,
        full: body instanceof HTMLElement && body.clientHeight >= body.scrollHeight - 1,
      };
    }),
    samples,
    overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
  };
};

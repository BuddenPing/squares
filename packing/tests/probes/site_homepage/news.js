// The native News destinations and the actual daily card typography and bounds.
() => {
  const news = document.querySelector("[data-news]");
  const heading = document.querySelector("#news.site-title");
  if (!(news instanceof HTMLElement) || !(heading instanceof HTMLElement)) {
    throw new Error("News content and its shared heading must be present");
  }
  const headingStyle = getComputedStyle(heading);
  return {
    family: getComputedStyle(news).fontFamily,
    heading: { family: headingStyle.fontFamily, transform: headingStyle.textTransform },
    entries: [...news.querySelectorAll("[data-news-entry]")].map((item) =>
      item.getAttribute("data-news-entry"),
    ),
    days: [...news.querySelectorAll("[data-news-day]")].map((day) => {
      const style = getComputedStyle(day);
      const box = day.getBoundingClientRect();
      const body = day.querySelector(".site-news-item p");
      return {
        date: day.getAttribute("data-news-day"),
        family: style.fontFamily,
        body_family: body ? getComputedStyle(body).fontFamily : null,
        border: Number.parseFloat(style.borderTopWidth),
        left: box.left,
        right: box.right,
      };
    }),
    overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
  };
};

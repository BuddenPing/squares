// The native News destinations and the actual entry card typography and bounds.
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
      const body = day.querySelector(".site-news-body");
      const prose = day.querySelector(".site-news-item p");
      const title = day.querySelector(".site-news-item h3");
      const date = day.querySelector("time");
      const button = day.querySelector(".site-news-expand");
      const arrow = button?.querySelector("[data-arrow]");
      return {
        id: day.id,
        date: day.getAttribute("data-news-day"),
        family: style.fontFamily,
        body_family: prose ? getComputedStyle(prose).fontFamily : null,
        body_height: body?.clientHeight ?? 0,
        body_scroll: body?.scrollHeight ?? 0,
        inline_height: body instanceof HTMLElement ? body.style.maxBlockSize : null,
        line_height: body ? Number.parseFloat(getComputedStyle(body).lineHeight) : 0,
        height: box.height,
        expanded: button?.getAttribute("aria-expanded"),
        button_hidden: button instanceof HTMLButtonElement && button.hidden,
        button_top: button?.getBoundingClientRect().top ?? 0,
        body_bottom: body?.getBoundingClientRect().bottom ?? 0,
        fade: body ? getComputedStyle(body, "::before").opacity : null,
        height_transition: body ? getComputedStyle(body).transitionProperty : null,
        arrow_transition: arrow ? getComputedStyle(arrow).transitionProperty : null,
        date_transform: date ? getComputedStyle(date).textTransform : null,
        title_transform: title ? getComputedStyle(title).textTransform : null,
        date_size: date ? Number.parseFloat(getComputedStyle(date).fontSize) : 0,
        title_size: title ? Number.parseFloat(getComputedStyle(title).fontSize) : 0,
        border: Number.parseFloat(style.borderTopWidth),
        left: box.left,
        right: box.right,
      };
    }),
    overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
  };
};

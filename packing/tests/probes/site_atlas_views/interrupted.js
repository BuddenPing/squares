// Press one control of the atlas, let the move it starts get `wait` milliseconds into its
// course, and press another, as a reader who changes their mind does. Each control takes
// the focus as it is pressed, as a pointer's press gives it in Chromium. Reports how many
// tiles were in a move just before the second press and just after it, and the farthest
// the drawing of any tile then in the window jumped across that press, in CSS pixels: a
// second change starts from where the first had got to, so nothing a reader can see
// jumps. `first` and `second` are the controls' selectors.
//
// `wait` is counted on the move's own clock, not the wall's. A move Chromium has created
// but not yet started is pending, its tiles still where they were, and under load it
// stays so for longer than a timer would wait: a second press then finds nothing to turn
// round. A timer that fires late can find the move over. So the probe waits until every
// move the first press started is under way (`ready`), sets each still running to `wait`
// milliseconds into its course, as `measure_atlas_views/hold` sets a move for a picture,
// and reads and presses in that same task, in which the timeline does not advance: the
// page reads the tiles exactly there.
async (/** @type {{first: string, second: string, wait: number}} */ { first, second, wait }) => {
  const one = document.querySelector(first);
  const two = document.querySelector(second);
  if (!(one instanceof HTMLElement) || !(two instanceof HTMLElement)) {
    return null;
  }
  const moves = () =>
    document
      .getAnimations()
      .filter(
        (animation) =>
          !(animation instanceof CSSTransition) && animation.effect instanceof KeyframeEffect,
      );
  const moving = () =>
    moves().filter(
      (animation) =>
        animation.effect instanceof KeyframeEffect &&
        animation.effect.target?.matches(".site-atlas-cell") === true &&
        animation.playState === "running",
    ).length;
  const drawings = () =>
    [...document.querySelectorAll(".site-atlas-cells .site-atlas-cell :is(svg, img)")].map(
      (drawing) => drawing.getBoundingClientRect(),
    );
  one.focus();
  one.click();
  const started = moves();
  await Promise.allSettled(started.map((move) => move.ready));
  for (const move of started) {
    if (move.playState === "running") {
      move.currentTime = wait;
    }
  }
  const before = { moving: moving(), drawings: drawings() };
  two.focus();
  two.click();
  const after = { moving: moving(), drawings: drawings() };
  let jump = 0;
  let watched = 0;
  for (const [index, was] of before.drawings.entries()) {
    const is = after.drawings[index];
    if (is !== undefined && was.width > 0 && was.bottom > 0 && was.top < window.innerHeight) {
      watched += 1;
      jump = Math.max(
        jump,
        Math.abs(is.left - was.left),
        Math.abs(is.top - was.top),
        Math.abs(is.width - was.width),
      );
    }
  }
  return {
    moving_before: before.moving,
    moving_after: after.moving,
    watched,
    jump: Math.round(jump * 100) / 100,
  };
};

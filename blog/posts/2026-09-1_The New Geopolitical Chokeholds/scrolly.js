/* Synchronize editorial SVG states with Quarto Closeread narrative steps. */
document.addEventListener("DOMContentLoaded", () => {
  // Explicit query hooks support reproducible visual QA without affecting readers.
  const preview = new URLSearchParams(window.location.search);
  if (preview.get("visual-theme") === "dark") {
    document.body.classList.remove("quarto-light");
    document.body.classList.add("quarto-dark");
    document.documentElement.dataset.bsTheme = "dark";
  }
  if (preview.get("visual-motion") === "reduce") {
    document.body.classList.add("visual-reduced-motion");
  }

  const steps = Array.from(
    document.querySelectorAll(".new-trigger[data-focus-on][data-scene]")
  );

  if (!steps.length) return;

  let currentStep = null;
  let scheduled = false;

  function figureFor(step) {
    const target = step.dataset.focusOn;
    if (!target) return null;
    const sticky = document.getElementById(target);
    return sticky?.querySelector(".geo-scrolly") ?? null;
  }

  function activate(step) {
    if (!step || step === currentStep) return;
    const figure = figureFor(step);
    if (!figure) return;

    currentStep?.removeAttribute("data-visual-active");
    currentStep = step;
    currentStep.setAttribute("data-visual-active", "true");

    figure.dataset.state = step.dataset.scene;
    const title = step.dataset.sceneTitle || step.dataset.scene.replaceAll("-", " ");
    figure.dataset.mobileTitle = title;
    const mobileState = figure.querySelector(".mobile-state");
    if (mobileState) mobileState.textContent = title;
  }

  function update() {
    scheduled = false;
    const midpoint = window.innerHeight * .5;
    let nearest = null;
    let nearestDistance = Number.POSITIVE_INFINITY;

    for (const step of steps) {
      const rect = step.getBoundingClientRect();
      const distance = rect.top <= midpoint && rect.bottom >= midpoint
        ? 0
        : Math.min(Math.abs(rect.top - midpoint), Math.abs(rect.bottom - midpoint));
      if (distance < nearestDistance) {
        nearest = step;
        nearestDistance = distance;
      }
    }

    activate(nearest);
  }

  function scheduleUpdate() {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(update);
  }

  for (const figure of document.querySelectorAll(".geo-scrolly[data-default-state]")) {
    figure.dataset.state = figure.dataset.defaultState;
    const mobileState = figure.querySelector(".mobile-state");
    if (mobileState) mobileState.textContent = figure.dataset.defaultTitle || "";
  }

  window.addEventListener("scroll", scheduleUpdate, { passive: true });
  window.addEventListener("resize", scheduleUpdate);
  scheduleUpdate();
});

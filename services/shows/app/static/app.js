// Small touches for the pages. No rules live here: every setlist check is
// done in Python, and every page works the same without JavaScript.

// 1. Ask before actions that are easy to click by mistake.
// A form with data-confirm="Some question?" only submits if the user
// clicks OK.
document.addEventListener("submit", function (event) {
  var question = event.target.dataset.confirm;
  if (question && !window.confirm(question)) {
    event.preventDefault();
  }
});

// 2. A shout floats up from the pointer on every click. Text only.
var SHOUTS = ["Hee-hee!", "Shamone!", "Pouw!", "Aaow!", "Hoo!", "Dah!"];

// Users who asked their system for less motion get no shouts.
var reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

document.addEventListener("click", function (event) {
  // detail is 0 for a "click" made with the keyboard (Enter or Space),
  // which has no pointer position to start from.
  if (reducedMotion.matches || event.detail === 0) {
    return;
  }
  var shout = document.createElement("span");
  shout.className = "shout";
  shout.textContent = SHOUTS[Math.floor(Math.random() * SHOUTS.length)];
  shout.setAttribute("aria-hidden", "true");
  shout.style.left = event.clientX + "px";
  shout.style.top = event.clientY + "px";
  document.body.appendChild(shout);
  // The CSS animation fades it out; then it is taken off the page.
  shout.addEventListener("animationend", function () {
    shout.remove();
  });
});

/* Deck behaviour: reveal.js setup, full-screen fill, count-up numbers,
   inline river-network schematic. Animations are skipped in ?print-pdf so
   the PDF always shows every slide in its final state. */
(function () {
  "use strict";

  var PRINT = /print-pdf/i.test(window.location.search);
  var RECEIVER = /receiver/i.test(window.location.search) || window.self !== window.top;

  /* ---------- inline the generated river-network SVG ---------- */
  function injectNetworks() {
    if (!window.NETWORK_SVG) return;
    document.querySelectorAll("[data-network]").forEach(function (host) {
      host.innerHTML = window.NETWORK_SVG;
      var svg = host.querySelector("svg");
      svg.setAttribute("class", "netsvg");
      svg.setAttribute("role", "img");
      svg.setAttribute("aria-label", "Schematic directed river network with a few gauged reaches");
      var g = host.getAttribute("data-gauges-fragment");
      var h = host.getAttribute("data-held-fragment");
      if (g !== null) { var eg = svg.querySelector(".gauges"); eg.classList.add("fragment", "zoom-in"); eg.setAttribute("data-fragment-index", g); }
      if (h !== null) { var eh = svg.querySelector(".held"); eh.classList.add("fragment", "zoom-in"); eh.setAttribute("data-fragment-index", h); }
    });
  }

  /* ---------- count-up numbers ---------- */
  // <span data-count="58834" data-dec="0">58,834</span>; the markup keeps the
  // final value so print, overview and no-JS all show the real number.
  function fmt(v, dec, sep) {
    var s = v.toFixed(dec);
    if (!sep) return s;
    var parts = s.split(".");
    parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    return parts.join(".");
  }
  function countUp(el) {
    // disabled: numbers are shown directly (the markup already holds the final value)
    return;
    if (PRINT) return;
    var target = parseFloat(el.getAttribute("data-count"));
    var dec = parseInt(el.getAttribute("data-dec") || "0", 10);
    var sep = el.getAttribute("data-sep") !== "no";
    var dur = parseFloat(el.getAttribute("data-dur") || "1100");
    var t0 = null;
    if (el._raf) cancelAnimationFrame(el._raf);
    function step(ts) {
      if (t0 === null) t0 = ts;
      var k = Math.min(1, (ts - t0) / dur);
      var e = 1 - Math.pow(1 - k, 3); // ease-out cubic
      el.textContent = fmt(target * e, dec, sep);
      if (k < 1) el._raf = requestAnimationFrame(step);
      else el.textContent = fmt(target, dec, sep);
    }
    el._raf = requestAnimationFrame(step);
  }
  function countVisibleIn(root, onlyOutsideFragments) {
    root.querySelectorAll("[data-count]").forEach(function (el) {
      var frag = el.closest(".fragment");
      if (onlyOutsideFragments && frag && frag !== root) return;
      countUp(el);
    });
  }

  /* ---------- fill the whole screen (no letterbox bars) ---------- */
  // reveal keeps 16:9 and centres the slide; on 16:10 / 4:3 screens we paint
  // the leftover margin with the slide's own colours, so the green title bar
  // and the title slide's columns run to the screen edges, as in PowerPoint.
  function syncBackdrop() {
    if (PRINT) return;
    var rev = document.querySelector(".reveal");
    var W = rev.offsetWidth, H = rev.offsetHeight, s = Reveal.getScale();
    var left = (W - 1920 * s) / 2, top = (H - 1080 * s) / 2;
    var root = document.documentElement.style;
    root.setProperty("--fill-bar", (top + 92 * s).toFixed(1) + "px");
    root.setProperty("--fill-left", (left + 400 * s).toFixed(1) + "px");
  }
  function tagBackgrounds() {
    document.querySelectorAll(".reveal .slides > section").forEach(function (sec) {
      var bg = Reveal.getSlideBackground(sec);
      if (!bg) return;
      if (sec.classList.contains("title-slide")) bg.classList.add("fill-title");
      else if (sec.classList.contains("divider")) bg.classList.add("fill-green");
      else bg.classList.add("fill-content");
    });
  }

  /* ---------- presentation-mode button (full screen) ---------- */
  function addPresentButton() {
    if (PRINT || RECEIVER || !document.documentElement.requestFullscreen) return;
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "present-btn";
    btn.title = "Presentation mode (full screen), or press F";
    btn.setAttribute("aria-label", "Enter presentation mode (full screen)");
    btn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
      '<rect x="2.5" y="3.5" width="19" height="13" rx="2"/><path d="M10 7.5v5l4-2.5z" fill="currentColor"/><path d="M8 21h8M12 16.5V21"/></svg>';
    btn.addEventListener("click", function (e) {
      e.stopPropagation();
      btn.blur();
      document.documentElement.requestFullscreen().catch(function () {});
    });
    document.body.appendChild(btn);
    document.addEventListener("fullscreenchange", function () {
      document.documentElement.classList.toggle("is-fs", !!document.fullscreenElement);
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    injectNetworks();

    if (window.renderMathInElement) {
      window.renderMathInElement(document.querySelector(".slides"), {
        delimiters: [
          { left: "\\(", right: "\\)", display: false },
          { left: "\\[", right: "\\]", display: true }
        ],
        throwOnError: false
      });
    }

    Reveal.initialize({
      width: 1920,
      height: 1080,
      margin: 0,
      minScale: 0.05,
      maxScale: 4,
      center: false,
      hash: true,
      controls: false,
      progress: true,
      slideNumber: "c/t",
      showSlideNumber: "all",
      transition: "fade",
      transitionSpeed: "default",
      backgroundTransition: "fade",
      pdfSeparateFragments: false,
      pdfMaxPagesPerSlide: 1,
      plugins: [RevealNotes]
    }).then(function () {
      tagBackgrounds();
      syncBackdrop();
      addPresentButton();
      countVisibleIn(Reveal.getCurrentSlide(), true);
    });

    Reveal.on("resize", syncBackdrop);
    Reveal.on("slidechanged", function (e) { countVisibleIn(e.currentSlide, true); });
    Reveal.on("fragmentshown", function (e) {
      e.fragments.forEach(function (f) {
        if (f.hasAttribute("data-count")) countUp(f);
        countVisibleIn(f, false);
      });
    });
    window.addEventListener("resize", function () { setTimeout(syncBackdrop, 50); });
    document.addEventListener("fullscreenchange", function () { setTimeout(syncBackdrop, 80); });
  });
})();

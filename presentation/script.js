/* ============================================================
   PyMart — Présentation HTML : interactions de présentation
   - coloration syntaxique Python (sans bibliothèque)
   - numéros de lignes
   - boutons « Copier »
   - onglets de code
   - menu mobile
   - navigation active + animations au défilement
   ============================================================ */

(function () {
  "use strict";

  /* ---------- Échappement HTML ---------- */
  function escapeHtml(text) {
    return text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  /* ---------- Mots-clés et fonctions courantes ---------- */
  var KEYWORDS = new Set([
    "def", "class", "return", "if", "elif", "else", "for", "while",
    "import", "from", "raise", "try", "except", "pass", "with", "yield",
    "not", "in", "is", "and", "or", "lambda", "continue", "break",
    "None", "True", "False", "as", "global"
  ]);

  var BUILTINS = new Set([
    "print", "len", "range", "int", "str", "sorted", "sum", "open",
    "enumerate", "isinstance", "min", "max", "Decimal", "date", "Path"
  ]);

  function classify(token) {
    if (token.slice(0, 3) === '"""') return "doc";
    if (token[0] === '"' || token[0] === "'") return "string";
    if (token[0] === "#") return "comment";
    if (/^\d/.test(token)) return "number";
    if (token[0] === "@") return "decorator";
    if (token.indexOf("def ") === 0) return "func";
    if (token.indexOf("class ") === 0) return "classname";
    if (token === "self") return "self";
    if (KEYWORDS.has(token)) return "keyword";
    if (BUILTINS.has(token)) return "builtin";
    return "plain";
  }

  /* ---------- Coloration syntaxique Python (simple) ---------- */
  function highlightPython(code) {
    var re = new RegExp(
      [
        '("""[\\s\\S]*?""")',                       // docstring
        '("(?:[^"\\n\\\\]|\\\\.)*")',              // chaîne double
        "('(?:[^'\\n\\\\]|\\\\.)*')",              // chaîne simple
        "(#.*$)",                                  // commentaire
        "(\\b\\d+(?:\\.\\d+)?\\b)",                // nombre
        "(@\\w+)",                                 // décorateur
        "(\\bdef\\s+\\w+)",                        // définition de fonction
        "(\\bclass\\s+\\w+)",                      // définition de classe
        "(\\bself\\b)",                            // self
        "(\\b(?:print|len|range|int|str|sorted|sum|open|enumerate|isinstance|min|max|Decimal|date|Path)\\b)", // fonctions courantes
        "(\\b(?:def|class|return|if|elif|else|for|while|import|from|raise|try|except|pass|with|yield|not|in|is|and|or|lambda|continue|break|None|True|False|as|global)\\b)" // mots-clés
      ].join("|"),
      "gm"
    );

    var out = "";
    var last = 0;
    var match;
    while ((match = re.exec(code)) !== null) {
      out += escapeHtml(code.slice(last, match.index));
      var token = match[0];
      var cls = classify(token);
      out += cls === "plain"
        ? escapeHtml(token)
        : '<span class="tok-' + cls + '">' + escapeHtml(token) + "</span>";
      last = match.index + token.length;
    }
    out += escapeHtml(code.slice(last));
    return out;
  }

  /* ---------- Numéros de lignes + coloration ---------- */
  function setupCodeBlocks() {
    var blocks = document.querySelectorAll("code[data-lang='python']");
    blocks.forEach(function (code) {
      var raw = code.textContent.replace(/^\n+|\n+$/g, "");
      var lineCount = raw.split("\n").length;
      code.innerHTML = highlightPython(raw);

      var body = code.closest(".code-body");
      if (body) {
        var gutter = body.querySelector(".line-numbers");
        if (gutter) {
          var html = "";
          for (var i = 1; i <= lineCount; i++) {
            html += "<span>" + i + "</span>";
          }
          gutter.innerHTML = html;
        }
      }
    });
  }

  /* ---------- Boutons « Copier » ---------- */
  function setupCopyButtons() {
    document.querySelectorAll(".copy-btn").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var block = btn.closest(".code-block");
        var code = block ? block.querySelector("pre") : null;
        if (!code) return;

        var text = code.textContent.replace(/^\n+|\n+$/g, "");
        copyText(text).then(function () {
          btn.textContent = "Copié ✓";
          btn.classList.add("copied");
          setTimeout(function () {
            btn.textContent = "Copier";
            btn.classList.remove("copied");
          }, 1600);
        });
      });
    });
  }

  function copyText(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(text);
    }
    return new Promise(function (resolve) {
      var textarea = document.createElement("textarea");
      textarea.value = text;
      textarea.style.position = "fixed";
      textarea.style.opacity = "0";
      document.body.appendChild(textarea);
      textarea.select();
      try {
        document.execCommand("copy");
      } catch (err) {
        /* ignore */
      }
      document.body.removeChild(textarea);
      resolve();
    });
  }

  /* ---------- Onglets ---------- */
  function setupTabs() {
    document.querySelectorAll("[data-tabs]").forEach(function (group) {
      var buttons = group.querySelectorAll(".tab-btn");
      var panels = group.querySelectorAll(".tab-panel");

      buttons.forEach(function (btn) {
        btn.addEventListener("click", function () {
          buttons.forEach(function (b) { b.classList.remove("active"); });
          panels.forEach(function (p) { p.classList.remove("active"); });
          btn.classList.add("active");
          var target = group.querySelector("#" + btn.dataset.tab);
          if (target) target.classList.add("active");
        });
      });
    });
  }

  /* ---------- Menu mobile ---------- */
  function setupMobileMenu() {
    var toggle = document.getElementById("navToggle");
    var links = document.getElementById("navLinks");
    if (!toggle || !links) return;

    toggle.addEventListener("click", function () {
      links.classList.toggle("open");
    });

    links.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", function () {
        links.classList.remove("open");
      });
    });
  }

  /* ---------- Navigation active ---------- */
  function setupScrollSpy() {
    var links = Array.prototype.slice.call(
      document.querySelectorAll(".nav-links a[href^='#']")
    );
    var sections = links
      .map(function (link) {
        return document.querySelector(link.getAttribute("href"));
      })
      .filter(Boolean);

    function update() {
      var pos = window.scrollY + 120;
      var current = sections[0];
      sections.forEach(function (section) {
        if (section.offsetTop <= pos) current = section;
      });
      if (!current) return;
      var id = "#" + current.id;
      links.forEach(function (link) {
        link.classList.toggle("active", link.getAttribute("href") === id);
      });
    }

    window.addEventListener("scroll", update, { passive: true });
    update();
  }

  /* ---------- Animations au défilement ---------- */
  function setupReveal() {
    var items = document.querySelectorAll(".reveal");
    if (!("IntersectionObserver" in window)) {
      items.forEach(function (el) { el.classList.add("visible"); });
      return;
    }
    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.08 }
    );
    items.forEach(function (el) { observer.observe(el); });
  }

  /* ---------- Initialisation ---------- */
  document.addEventListener("DOMContentLoaded", function () {
    setupCodeBlocks();
    setupCopyButtons();
    setupTabs();
    setupMobileMenu();
    setupScrollSpy();
    setupReveal();
  });
})();

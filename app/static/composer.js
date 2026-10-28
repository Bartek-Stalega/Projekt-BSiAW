/**
 * Composer w stylu forow (XenForo / Discourse rich mode):
 * - WYSIWYG: widzisz pogrubienie / listy od razu
 * - Obrazy: przycisk, drag&drop, wklejenie ze schowka
 * - Zapis jako Markdown (kompatybilny z backendem)
 */
(function () {
  function loadScript(src) {
    return new Promise((resolve, reject) => {
      if (document.querySelector('script[src="' + src + '"]')) {
        resolve();
        return;
      }
      const s = document.createElement("script");
      s.src = src;
      s.onload = () => resolve();
      s.onerror = () => reject(new Error("Nie zaladowano: " + src));
      document.head.appendChild(s);
    });
  }

  function loadCss(href) {
    if (document.querySelector('link[href="' + href + '"]')) return;
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    document.head.appendChild(link);
  }

  async function uploadBlob(blob) {
    const data = new FormData();
    const file =
      blob instanceof File
        ? blob
        : new File([blob], "paste.png", { type: blob.type || "image/png" });
    data.append("image", file);
    const res = await fetch("/api/uploads", { method: "POST", body: data });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Upload nieudany");
    }
    return (await res.json()).url;
  }

  function initOne(root) {
    const textarea = root.querySelector("textarea[data-composer]");
    if (!textarea || !window.toastui || !window.toastui.Editor) return;

    const mount = root.querySelector("[data-toast-editor]");
    if (!mount || mount.dataset.ready) return;
    mount.dataset.ready = "1";

    const initial = textarea.value || "";
    textarea.required = false;
    textarea.classList.add("composer-sync");

    const editor = new toastui.Editor({
      el: mount,
      height: root.getAttribute("data-composer-height") || "340px",
      initialValue: initial,
      initialEditType: "wysiwyg",
      previewStyle: "tab",
      hideModeSwitch: false,
      usageStatistics: false,
      placeholder: textarea.getAttribute("placeholder") || "Napisz wiadomosc...",
      toolbarItems: [
        ["heading", "bold", "italic", "strike"],
        ["hr", "quote"],
        ["ul", "ol", "task"],
        ["table", "image", "link"],
        ["code", "codeblock"],
        ["scrollSync"],
      ],
      hooks: {
        addImageBlobHook: (blob, callback) => {
          uploadBlob(blob)
            .then((url) => callback(url, "obraz"))
            .catch((err) => {
              alert(err.message || "Nie udalo sie wgrac obrazka.");
            });
        },
      },
    });

    root._foliumEditor = editor;

    const form = root.closest("form") || root;
    form.addEventListener("submit", (e) => {
      const md = (editor.getMarkdown() || "").trim();
      textarea.value = md;
      if (!md) {
        e.preventDefault();
        alert("Wpisz tresc wiadomosci.");
        editor.focus();
      }
    });
  }

  async function boot() {
    const roots = document.querySelectorAll("[data-composer-root]");
    if (!roots.length) return;

    loadCss("/static/vendor/toastui/toastui-editor.min.css");
    try {
      await loadScript("/static/vendor/toastui/toastui-editor-all.min.js");
    } catch (err) {
      console.error(err);
      return;
    }
    roots.forEach(initOne);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();

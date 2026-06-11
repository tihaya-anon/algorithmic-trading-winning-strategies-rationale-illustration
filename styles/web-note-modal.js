document.addEventListener("DOMContentLoaded", () => {
  const modal = document.getElementById("section-inline-modal");
  if (!modal) return;

  const panel = modal.querySelector(".section-inline-modal__panel");
  const frame = document.getElementById("section-inline-modal-frame");
  const markdownPanel = document.getElementById("section-inline-modal-markdown");
  const markdownCode = document.getElementById("section-inline-modal-markdown-code");
  const title = document.getElementById("section-inline-modal-title");
  const expandButton = document.getElementById("section-inline-modal-expand");
  const copyButton = document.getElementById("section-inline-modal-copy");
  const downloadButton = document.getElementById("section-inline-modal-download");
  let lastFocused = null;
  let markdownText = "";
  const pageTitle = document.querySelector(".quarto-title-block .title")?.textContent?.trim() || "Section";

  const closeModal = () => {
    modal.hidden = true;
    modal.setAttribute("aria-hidden", "true");
    document.body.classList.remove("modal-open");
    frame.src = "about:blank";
    frame.hidden = true;
    markdownPanel.hidden = true;
    copyButton.hidden = true;
    downloadButton.hidden = true;
    markdownText = "";
    if (document.fullscreenElement === panel) {
      document.exitFullscreen().catch(() => {});
    }
    if (lastFocused) lastFocused.focus();
  };

  const openIframeModal = (trigger, src, label, allowFullscreen) => {
    lastFocused = trigger;
    frame.src = src;
    frame.hidden = false;
    markdownPanel.hidden = true;
    title.textContent = label;
    expandButton.hidden = !allowFullscreen;
    copyButton.hidden = true;
    downloadButton.hidden = true;
    modal.hidden = false;
    modal.setAttribute("aria-hidden", "false");
    document.body.classList.add("modal-open");
  };

  const openMarkdownModal = async (trigger, src, label) => {
    lastFocused = trigger;
    const response = await fetch(src, { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const data = await response.json();
    markdownText = data.markdown || "";
    markdownCode.textContent = markdownText;
    frame.hidden = true;
    frame.src = "about:blank";
    markdownPanel.hidden = false;
    title.textContent = `${pageTitle} · ${label}`;
    expandButton.hidden = true;
    copyButton.hidden = false;
    downloadButton.hidden = false;
    modal.hidden = false;
    modal.setAttribute("aria-hidden", "false");
    document.body.classList.add("modal-open");
  };

  document.querySelectorAll(".section-output-links a[data-modal]").forEach((link) => {
    link.addEventListener("click", async (event) => {
      event.preventDefault();
      const label = link.getAttribute("data-label") || link.getAttribute("aria-label") || "Viewer";
      const modalType = link.getAttribute("data-modal");
      if (modalType === "markdown") {
        const src = link.getAttribute("data-markdown-src") || link.href;
        await openMarkdownModal(link, src, label);
      } else {
        const allowFullscreen = modalType === "video";
        openIframeModal(link, link.href, allowFullscreen ? `${pageTitle} · ${label}` : label, allowFullscreen);
      }
    });
  });

  modal.querySelectorAll("[data-modal-close]").forEach((node) => {
    node.addEventListener("click", closeModal);
  });

  expandButton.addEventListener("click", async () => {
    if (document.fullscreenElement === panel) {
      await document.exitFullscreen();
    } else {
      await panel.requestFullscreen();
    }
  });

  copyButton.addEventListener("click", async () => {
    await navigator.clipboard.writeText(markdownText);
  });

  downloadButton.addEventListener("click", () => {
    const blob = new Blob([markdownText], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "section.md";
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !modal.hidden) {
      closeModal();
    }
  });
});

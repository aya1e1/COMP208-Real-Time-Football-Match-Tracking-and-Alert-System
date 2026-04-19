(function attachPageSwitcher() {
  const sharedCards = window.KickoffFixtureCards || {};
  const escapeHtml = sharedCards.escapeHtml || ((value) => String(value ?? ""));

  function restoreScrollPosition(scrollState) {
    if (!scrollState) {
      return;
    }

    window.requestAnimationFrame(() => {
      window.requestAnimationFrame(() => {
        window.scrollTo({
          left: scrollState.left,
          top: scrollState.top,
          behavior: "auto"
        });
      });
    });
  }

  function render(container, pagination, options = {}) {
    if (!container) {
      return;
    }

    const totalPages = Number(pagination?.total_pages) || 0;
    if (!pagination || totalPages <= 1) {
      container.hidden = true;
      container.innerHTML = "";
      return;
    }

    const page = Number(pagination.page) || 1;
    const showDisabledNext = options.showDisabledNext === true;
    const buildHref = typeof options.buildHref === "function"
      ? options.buildHref
      : (pageNumber) => `?page=${pageNumber}`;
    const onSelect = typeof options.onSelect === "function"
      ? options.onSelect
      : null;
    const pages = [];
    const startPage = Math.max(1, page - 1);
    const endPage = Math.min(totalPages, page + 1);

    for (let pageNumber = startPage; pageNumber <= endPage; pageNumber += 1) {
      pages.push(pageNumber);
    }

    container.hidden = false;
    container.innerHTML =
      '<div class="fixture-h2h-group left">' +
        (pagination.has_previous
          ? `<a class="fixture-h2h-link" href="${escapeHtml(buildHref(page - 1))}" data-page="${page - 1}">Previous</a>`
          : "") +
      '</div>' +
      '<div class="fixture-h2h-group right">' +
        pages.map((pageNumber) => {
          if (pageNumber === page) {
            return `<span class="fixture-h2h-link active" aria-current="page">${escapeHtml(pageNumber)}</span>`;
          }

          return `<a class="fixture-h2h-link" href="${escapeHtml(buildHref(pageNumber))}" data-page="${pageNumber}">${escapeHtml(pageNumber)}</a>`;
        }).join("") +
        (pagination.has_next
          ? `<a class="fixture-h2h-link" href="${escapeHtml(buildHref(page + 1))}" data-page="${page + 1}">Next</a>`
          : (showDisabledNext ? '<span class="fixture-h2h-link" aria-disabled="true">Next</span>' : "")) +
      '</div>';

    if (!onSelect) {
      return;
    }

    container.querySelectorAll("[data-page]").forEach((link) => {
      link.addEventListener("click", (event) => {
        event.preventDefault();
        const nextPage = Number(link.getAttribute("data-page"));
        if (!Number.isFinite(nextPage) || nextPage < 1 || nextPage === page) {
          return;
        }

        const scrollState = {
          left: window.scrollX,
          top: window.scrollY
        };

        Promise.resolve()
          .then(() => onSelect(nextPage, link))
          .catch(() => {
            // Let page-specific handlers manage their own error UI.
          })
          .finally(() => {
            restoreScrollPosition(scrollState);
          });
      });
    });
  }

  window.KickoffPageSwitcher = {
    render
  };
})();

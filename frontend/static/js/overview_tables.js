(function attachOverviewTables() {
  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function renderAttributes(cell) {
    const attributes = [];

    if (cell.colspan) {
      attributes.push(`colspan="${escapeHtml(cell.colspan)}"`);
    }

    if (cell.rowspan) {
      attributes.push(`rowspan="${escapeHtml(cell.rowspan)}"`);
    }

    if (cell.scope) {
      attributes.push(`scope="${escapeHtml(cell.scope)}"`);
    }

    return attributes.length ? ` ${attributes.join(" ")}` : "";
  }

  function normalizeCell(cell, defaultTag = "td") {
    if (cell && typeof cell === "object" && !Array.isArray(cell)) {
      return {
        tag: cell.tag || defaultTag,
        className: cell.className || "",
        content: cell.content ?? "",
        raw: Boolean(cell.raw),
        colspan: cell.colspan,
        rowspan: cell.rowspan,
        scope: cell.scope
      };
    }

    return {
      tag: defaultTag,
      className: "",
      content: cell ?? "",
      raw: false
    };
  }

  function renderCell(cell, defaultTag) {
    const normalized = normalizeCell(cell, defaultTag);
    const className = normalized.className ? ` class="${escapeHtml(normalized.className)}"` : "";
    const content = normalized.raw
      ? String(normalized.content ?? "")
      : escapeHtml(normalized.content);

    return `<${normalized.tag}${className}${renderAttributes(normalized)}>${content}</${normalized.tag}>`;
  }

  function renderHead(headers) {
    if (!Array.isArray(headers) || !headers.length) {
      return "";
    }

    return `
      <thead>
        <tr>${headers.map((cell) => renderCell(cell, "th")).join("")}</tr>
      </thead>
    `;
  }

  function renderRows(rows) {
    return rows.map((row) => `<tr>${row.map((cell) => renderCell(cell, "td")).join("")}</tr>`).join("");
  }

  function renderTable(options = {}) {
    const headers = Array.isArray(options.headers) ? options.headers : [];
    const rows = Array.isArray(options.rows) ? options.rows : [];
    const className = options.className || "overview-table";
    const wrapClassName = options.wrapClassName || "";
    const tableMarkup = `
      <table class="${escapeHtml(className)}">
        ${renderHead(headers)}
        <tbody>${renderRows(rows)}</tbody>
      </table>
    `;

    if (!wrapClassName) {
      return tableMarkup;
    }

    return `<div class="${escapeHtml(wrapClassName)}">${tableMarkup}</div>`;
  }

  window.KickoffOverviewTables = {
    renderTable
  };
})();

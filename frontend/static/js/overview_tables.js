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
    let attributes = "";

    if (cell.colspan) {
      attributes += ` colspan="${escapeHtml(cell.colspan)}"`;
    }

    if (cell.rowspan) {
      attributes += ` rowspan="${escapeHtml(cell.rowspan)}"`;
    }

    if (cell.scope) {
      attributes += ` scope="${escapeHtml(cell.scope)}"`;
    }

    return attributes;
  }

  function renderCell(cell, defaultTag) {
    let tag = defaultTag;
    let className = "";
    let content = cell ?? "";
    let raw = false;
    let attributes = "";

    if (cell && typeof cell === "object" && !Array.isArray(cell)) {
      tag = cell.tag || defaultTag;
      className = cell.className || "";
      content = cell.content ?? "";
      raw = Boolean(cell.raw);
      attributes = renderAttributes(cell);
    }

    const classAttribute = className ? ` class="${escapeHtml(className)}"` : "";
    const cellContent = raw ? String(content) : escapeHtml(content);
    return `<${tag}${classAttribute}${attributes}>${cellContent}</${tag}>`;
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

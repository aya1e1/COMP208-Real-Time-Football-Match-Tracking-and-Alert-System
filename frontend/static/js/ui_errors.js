(function attachUiErrors() {
  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function render(message) {
    return `<p class="ui-error-message" role="alert">${escapeHtml(message)}</p>`;
  }

  function resolveMessage(errorOrMessage, fallbackMessage = "Unable to load this content.") {
    const message = typeof errorOrMessage === "string"
      ? errorOrMessage
      : errorOrMessage?.message;

    if (!message) {
      return fallbackMessage;
    }

    const normalized = String(message).trim();
    const lower = normalized.toLowerCase();

    if (
      lower.includes("networkerror")
      || lower.includes("failed to fetch")
      || lower.includes("load failed")
      || lower.includes("network request failed")
      || lower.includes("fetch resource")
    ) {
      return fallbackMessage;
    }

    return normalized;
  }

  window.KickoffUIErrors = {
    render,
    resolveMessage
  };
})();

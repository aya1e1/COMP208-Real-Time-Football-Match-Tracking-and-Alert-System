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

    return String(message).trim() || fallbackMessage;
  }

  window.KickoffUIErrors = {
    render,
    resolveMessage
  };
})();

(function attachFixtureCards() {
  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function formatDateTime(dateString, options = {}) {
    if (!dateString) {
      return { date: "TBC", time: "" };
    }

    const date = new Date(dateString);
    if (Number.isNaN(date.getTime())) {
      return { date: escapeHtml(dateString), time: "" };
    }

    const dateOptions = options.dateOptions || {
      day: "numeric",
      month: "short"
    };
    const timeOptions = options.timeOptions || {
      hour: "2-digit",
      minute: "2-digit"
    };

    return {
      date: date.toLocaleDateString("en-GB", dateOptions),
      time: date.toLocaleTimeString("en-GB", timeOptions)
    };
  }

  function renderTeamLogo(url, alt, className) {
    if (!url) {
      return "";
    }

    return `<img src="${escapeHtml(url)}" alt="${escapeHtml(alt)}" class="${escapeHtml(className)}" loading="lazy">`;
  }

  function getFixtureOutcomeClasses(fixture) {
    const homeScore = Number(fixture?.HomeScore);
    const awayScore = Number(fixture?.AwayScore);

    if (!Number.isFinite(homeScore) || !Number.isFinite(awayScore) || homeScore === awayScore) {
      return {
        home: "",
        away: ""
      };
    }

    return homeScore > awayScore
      ? { home: "is-winner", away: "is-loser" }
      : { home: "is-loser", away: "is-winner" };
  }

  function renderUpcomingFixtureCard(fixture) {
    const kickoff = formatDateTime(fixture?.MatchDate);

    return `
      <a href="/fixtures/${fixture.FixtureID}" class="card dashboard-fixture-card">
        <div class="card-body">
          <div class="dashboard-fixture-meta">
            <div class="dashboard-fixture-kickoff">${escapeHtml(kickoff.date)} @ ${escapeHtml(kickoff.time || "TBC")}</div>
            <div class="dashboard-fixture-status">${escapeHtml(fixture.Status || "NS")}</div>
          </div>
          <div class="dashboard-upcoming-layout">
            <div class="dashboard-upcoming-team">
              ${renderTeamLogo(fixture.HomeTeamLogoURL, `${fixture.HomeTeam} logo`, "dashboard-upcoming-team-logo")}
              <div class="dashboard-upcoming-team-name">${escapeHtml(fixture.HomeTeam)}</div>
            </div>
            <div class="dashboard-vs-pill">vs</div>
            <div class="dashboard-upcoming-team away">
              ${renderTeamLogo(fixture.AwayTeamLogoURL, `${fixture.AwayTeam} logo`, "dashboard-upcoming-team-logo")}
              <div class="dashboard-upcoming-team-name">${escapeHtml(fixture.AwayTeam)}</div>
            </div>
          </div>
          <div class="dashboard-fixture-league">${escapeHtml(fixture.LeagueName || "League fixture")}</div>
        </div>
      </a>
    `;
  }

  function renderUpcomingFixtures(container, fixtures, options = {}) {
    if (!container) {
      return;
    }

    const items = Array.isArray(fixtures) ? fixtures : [];
    const emptyMessage = options.emptyMessage || "No upcoming fixtures available";
    const emptyClassName = options.emptyClassName || "dashboard-empty-card";

    if (!items.length) {
      container.innerHTML = `<div class="${escapeHtml(emptyClassName)}">${escapeHtml(emptyMessage)}</div>`;
      return;
    }

    container.innerHTML = items.map((fixture) => renderUpcomingFixtureCard(fixture)).join("");
  }

  window.KickoffFixtureCards = {
    escapeHtml,
    formatDateTime,
    getFixtureOutcomeClasses,
    renderTeamLogo,
    renderUpcomingFixtureCard,
    renderUpcomingFixtures
  };
})();

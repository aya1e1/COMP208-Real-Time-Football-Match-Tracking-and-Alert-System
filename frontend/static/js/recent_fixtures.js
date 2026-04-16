(function attachRecentFixturesRenderer() {
  const sharedCards = window.KickoffFixtureCards || {};
  const escapeHtml = sharedCards.escapeHtml || ((value) => String(value ?? ""));
  const formatDateTime = sharedCards.formatDateTime || ((value) => ({ date: value || "TBC", time: "" }));
  const getFixtureOutcomeClasses = sharedCards.getFixtureOutcomeClasses || (() => ({ home: "", away: "" }));
  const renderTeamLogo = sharedCards.renderTeamLogo || (() => "");

  function getTeamPerspectiveClass(fixture, teamId) {
    const currentTeamId = Number(teamId);
    const homeTeamId = Number(fixture?.HomeTeamID);
    const awayTeamId = Number(fixture?.AwayTeamID);
    const homeScore = Number(fixture?.HomeScore);
    const awayScore = Number(fixture?.AwayScore);

    if (
      !Number.isFinite(currentTeamId)
      || !Number.isFinite(homeTeamId)
      || !Number.isFinite(awayTeamId)
      || !Number.isFinite(homeScore)
      || !Number.isFinite(awayScore)
      || homeScore === awayScore
    ) {
      return "";
    }

    const isHomeTeam = currentTeamId === homeTeamId;
    const isAwayTeam = currentTeamId === awayTeamId;

    if (!isHomeTeam && !isAwayTeam) {
      return "";
    }

    const teamWon = isHomeTeam ? homeScore > awayScore : awayScore > homeScore;
    return teamWon ? "is-win" : "is-loss";
  }

  function renderFixtureCard(fixture, fallbackLeagueName, options = {}) {
    const kickoff = formatDateTime(fixture.MatchDate);
    const status = fixture.Status || "FT";
    const outcomeClasses = getFixtureOutcomeClasses(fixture);
    const perspectiveClass = getTeamPerspectiveClass(fixture, options.teamId);
    const cardClassName = perspectiveClass || "";

    return `
      <a href="/fixtures/${fixture.FixtureID}" class="card dashboard-fixture-card ${cardClassName}">
        <div class="card-body">
          <div class="dashboard-fixture-meta">
            <div class="dashboard-fixture-kickoff">${escapeHtml(kickoff.date)} @ ${escapeHtml(kickoff.time || "TBC")}</div>
            <div class="dashboard-fixture-status">${escapeHtml(status)}</div>
          </div>
          <div class="dashboard-score-layout">
            <div class="dashboard-score-side ${perspectiveClass ? "" : outcomeClasses.home}">
              ${renderTeamLogo(fixture.HomeTeamLogoURL, `${fixture.HomeTeam} logo`, "dashboard-score-logo")}
              <div class="dashboard-score-value">${fixture.HomeScore ?? "-"}</div>
              <div class="dashboard-score-team-name">${escapeHtml(fixture.HomeTeam)}</div>
            </div>
            <div class="dashboard-score-divider">vs</div>
            <div class="dashboard-score-side ${perspectiveClass ? "" : outcomeClasses.away}">
              ${renderTeamLogo(fixture.AwayTeamLogoURL, `${fixture.AwayTeam} logo`, "dashboard-score-logo")}
              <div class="dashboard-score-value">${fixture.AwayScore ?? "-"}</div>
              <div class="dashboard-score-team-name">${escapeHtml(fixture.AwayTeam)}</div>
            </div>
          </div>
          <div class="dashboard-fixture-league">${escapeHtml(fixture.LeagueName || fallbackLeagueName || "League fixture")}</div>
        </div>
      </a>
    `;
  }

  function render(container, fixtures, options = {}) {
    if (!container) {
      return;
    }

    const items = Array.isArray(fixtures) ? fixtures : [];
    const emptyMessage = options.emptyMessage || "No recent fixtures found";
    const emptyClassName = options.emptyClassName || "dashboard-empty-card";
    const fallbackLeagueName = options.fallbackLeagueName || "League fixture";

    if (!items.length) {
      container.innerHTML = `<div class="${escapeHtml(emptyClassName)}">${escapeHtml(emptyMessage)}</div>`;
      return;
    }

    container.innerHTML = items
      .map((fixture) => renderFixtureCard(fixture, fallbackLeagueName, options))
      .join("");
  }

  window.KickoffRecentFixtures = {
    render
  };
})();

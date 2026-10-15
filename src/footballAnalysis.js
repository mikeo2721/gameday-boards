function buildAnalysisBoard() {
  return {
    issueTitle: "Football analysis for ALice's Resturant",
    restaurant: "Alice's Restaurant",
    subtitle: "Game-day board for the restaurant crowd",
    momentum: "High",
    form: "W-W-D-L-W",
    expectedGoals: 2.4,
    possession: 58,
    shotsOnTarget: 7,
    passAccuracy: 82,
    keyInsights: [
      "The midfield is creating space behind the press and controlling tempo.",
      "Wide runners are generating the clearest opportunities in transition.",
      "Defensive shape remains compact when the opponent has the ball in the final third."
    ],
    recommendedActions: [
      "Keep the press aggressive in the first 20 minutes.",
      "Target the left channel with direct passing after turnovers.",
      "Rotate full-backs late to protect the box during set pieces."
    ],
    metrics: [
      { label: 'Expected goals', value: '2.4' },
      { label: 'Possession', value: '58%' },
      { label: 'Shots on target', value: '7' },
      { label: 'Pass accuracy', value: '82%' }
    ]
  };
}

function renderBoardHtml(board = buildAnalysisBoard()) {
  const insights = board.keyInsights.map((item) => `<li>${item}</li>`).join('');
  const actions = board.recommendedActions.map((item) => `<li>${item}</li>`).join('');
  const metrics = board.metrics.map(
    (metric) => `<div class="metric"><span>${metric.label}</span><strong>${metric.value}</strong></div>`
  ).join('');

  return `<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>${board.issueTitle}</title>
    <style>
      body {
        font-family: Arial, sans-serif;
        margin: 0;
        background: #0f172a;
        color: #e2e8f0;
      }
      .board {
        max-width: 960px;
        margin: 40px auto;
        background: #111827;
        border-radius: 16px;
        padding: 32px;
        box-shadow: 0 20px 45px rgba(15, 23, 42, 0.35);
      }
      h1 { margin: 0 0 8px; }
      h2 { margin-top: 0; color: #93c5fd; }
      .metrics { display: grid; grid-template-columns: repeat(4, minmax(140px, 1fr)); gap: 16px; margin: 24px 0; }
      .metric { background: #1f2937; border-radius: 12px; padding: 16px; }
      .metric span { display: block; color: #cbd5e1; font-size: 12px; text-transform: uppercase; margin-bottom: 8px; }
      .metric strong { font-size: 24px; }
      .panel { display: grid; grid-template-columns: repeat(2, minmax(240px, 1fr)); gap: 20px; }
      ul { margin: 0; padding-left: 20px; line-height: 1.8; }
      .badge { display: inline-block; background: rgba(34, 197, 94, 0.15); color: #86efac; border: 1px solid rgba(134, 239, 172, 0.4); border-radius: 999px; padding: 6px 12px; font-weight: bold; }
    </style>
  </head>
  <body>
    <main class="board">
      <div class="badge">${board.momentum} momentum</div>
      <h1>${board.issueTitle}</h1>
      <h2>${board.restaurant}</h2>
      <p>${board.subtitle}</p>
      <div class="metrics">${metrics}</div>
      <div class="panel">
        <section>
          <h3>Key insights</h3>
          <ul>${insights}</ul>
        </section>
        <section>
          <h3>Recommended actions</h3>
          <ul>${actions}</ul>
        </section>
      </div>
    </main>
  </body>
</html>`;
}

module.exports = {
  buildAnalysisBoard,
  renderBoardHtml
};

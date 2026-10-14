const { buildAnalysisBoard, renderBoardHtml } = require('./src/footballAnalysis');

if (require.main === module) {
  const board = buildAnalysisBoard();
  process.stdout.write(renderBoardHtml(board));
}

module.exports = {
  buildAnalysisBoard,
  renderBoardHtml
};

const test = require('node:test');
const assert = require('node:assert/strict');

const { buildAnalysisBoard, renderBoardHtml } = require('../index');

test('buildAnalysisBoard returns Alice\'s Restaurant football analysis details', () => {
  const board = buildAnalysisBoard();

  assert.equal(board.restaurant, "Alice's Restaurant");
  assert.equal(board.issueTitle, "Football analysis for ALice's Resturant");
  assert.equal(board.momentum, 'High');
  assert.equal(board.form, 'W-W-D-L-W');
  assert.equal(board.metrics.length, 4);
  assert.ok(board.keyInsights.length >= 3);
});

test('renderBoardHtml includes board title and insight content', () => {
  const html = renderBoardHtml();

  assert.match(html, /Football analysis for ALice's Resturant/i);
  assert.match(html, /Alice's Restaurant/i);
  assert.match(html, /Key insights/i);
  assert.match(html, /Recommended actions/i);
});

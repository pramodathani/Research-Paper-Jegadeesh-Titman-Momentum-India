'use strict';

const COLOURS = {
  blue: '#4285f4',
  red: '#ea4335',
  yellow: '#fbbc05',
  green: '#34a853',
  grey: '#5f6368',
  light: '#f1f3f4',
};
const FONT = "'Times New Roman', Tinos, 'Liberation Serif', serif";
const GST = 0.18;
const LEG_NAMES = {
  long_short: 'Winners minus losers',
  buy: 'Winners only',
  sell: 'Losers only',
};
const UNIVERSE_NAMES = {
  U1: 'all NSE shares',
  U2: 'top 500 by traded value',
  U3: 'top 200 by traded value',
};
const PAPER_TABLE = {
  3: {Sell: [[0.0108, 2.16], [0.0091, 1.87], [0.0092, 1.92], [0.0087, 1.87]],
      Buy: [[0.0140, 3.57], [0.0149, 3.78], [0.0152, 3.83], [0.0156, 3.89]],
      'Buy − sell': [[0.0032, 1.10], [0.0058, 2.29], [0.0061, 2.69], [0.0069, 3.53]]},
  6: {Sell: [[0.0087, 1.67], [0.0079, 1.56], [0.0072, 1.48], [0.0080, 1.66]],
      Buy: [[0.0171, 4.28], [0.0174, 4.33], [0.0174, 4.31], [0.0166, 4.13]],
      'Buy − sell': [[0.0084, 2.44], [0.0095, 3.07], [0.0102, 3.76], [0.0086, 3.36]]},
  9: {Sell: [[0.0077, 1.47], [0.0065, 1.29], [0.0071, 1.43], [0.0082, 1.66]],
      Buy: [[0.0186, 4.56], [0.0186, 4.53], [0.0176, 4.30], [0.0164, 4.03]],
      'Buy − sell': [[0.0109, 3.03], [0.0121, 3.78], [0.0105, 3.47], [0.0082, 2.89]]},
  12: {Sell: [[0.0060, 1.17], [0.0065, 1.29], [0.0075, 1.48], [0.0087, 1.74]],
       Buy: [[0.0192, 4.63], [0.0179, 4.36], [0.0168, 4.10], [0.0155, 3.81]],
       'Buy − sell': [[0.0131, 3.74], [0.0114, 3.40], [0.0093, 2.95], [0.0068, 2.25]]},
};

let snapshot = null;
const charts = {};
const state = {
  j: 6,
  k: 6,
  skip: 0,
  universe: 'U2',
  leg: 'long_short',
  costs: 'net',
  impact: 0.10,
  brokerage: 0,
  fee: 0,
  flat: 0.5,
  sample: '2005-01|2026-10', // replaced by the snapshot's last month on load
  impactTouched: false,
};

function percent(value, places = 2) {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return '';
  }
  return (value * 100).toFixed(places);
}

function signed(value, places = 2) {
  if (!Number.isFinite(value)) {
    return '';
  }
  return value.toFixed(places);
}

function cell(value, tValue) {
  const shown = percent(value);
  const tText = Number.isFinite(tValue) ? `(${tValue.toFixed(2)})` : '';
  const tone = value > 0 ? 'positive' : value < 0 ? 'negative' : '';
  return `<td><span class="${tone}">${shown}</span><span class="t">${tText}</span></td>`;
}

function decode(values) {
  return values.map((value) => (value === null ? null : value / snapshot.scale));
}

function seriesKey(universe, skip, j, k, leg) {
  return `${universe}|${skip}|${j}|${k}|${leg}`;
}

function defaultImpact(universe) {
  return snapshot.impact[universe];
}

function turnover(universe, skip, j, k, leg) {
  if (leg !== 'long_short') {
    const entry = snapshot.series[seriesKey(universe, skip, j, k, leg)];
    return decode(entry.t);
  }
  const buy = turnover(universe, skip, j, k, 'buy');
  const sell = turnover(universe, skip, j, k, 'sell');
  return buy.map((value, index) => (value || 0) + (sell[index] || 0));
}

function returns(universe, skip, j, k, leg, costs) {
  const entry = snapshot.series[seriesKey(universe, skip, j, k, leg)];
  if (!entry) {
    return null;
  }
  if (costs === 'gross') {
    return decode(entry.g);
  }
  const net = decode(entry.n);
  const traded = turnover(universe, skip, j, k, leg);
  const extraImpact = state.impact / 100 - defaultImpact(universe);
  const brokerage = (state.brokerage / 100) * (1 + GST);
  const fee = leg === 'long_short' ? state.fee / 100 / 12 : 0;
  return net.map((value, index) => {
    if (value === null) {
      return null;
    }
    const trade = traded[index] || 0;
    return value - (extraImpact + brokerage) * trade - fee;
  });
}

function sampleIndices() {
  const [start, end] = state.sample.split('|');
  const indices = [];
  snapshot.months.forEach((month, index) => {
    if (month >= start && month <= end) {
      indices.push(index);
    }
  });
  return indices;
}

function mean(values) {
  return values.reduce((total, value) => total + value, 0) / values.length;
}

function neweyWestT(values) {
  const count = values.length;
  if (count < 3) {
    return NaN;
  }
  const average = mean(values);
  const errors = values.map((value) => value - average);
  const lags = Math.max(1, Math.floor(4 * Math.pow(count / 100, 2 / 9)));
  let sum = errors.reduce((total, value) => total + value * value, 0);
  for (let lag = 1; lag <= lags; lag += 1) {
    let product = 0;
    for (let time = lag; time < count; time += 1) {
      product += errors[time] * errors[time - lag];
    }
    sum += 2 * (1 - lag / (lags + 1)) * product;
  }
  const variance = (sum / (count * count)) * (count / (count - 1));
  return average / Math.sqrt(variance);
}

function statistics(values, indices, leg, marketKey = 'market') {
  const months = [];
  const picked = [];
  indices.forEach((index) => {
    if (values[index] !== null && values[index] !== undefined) {
      picked.push(values[index]);
      months.push(index);
    }
  });
  const count = picked.length;
  if (count < 3) {
    return {count};
  }
  const average = mean(picked);
  const deviation = Math.sqrt(
    picked.reduce((total, value) => total + (value - average) ** 2, 0) / (count - 1),
  );
  let wealth = 1;
  let peak = 1;
  let worstDrawdown = 0;
  picked.forEach((value) => {
    wealth *= 1 + value;
    peak = Math.max(peak, wealth);
    worstDrawdown = Math.min(worstDrawdown, wealth / peak - 1);
  });
  const result = {
    count,
    mean: average,
    plainT: average / (deviation / Math.sqrt(count)),
    neweyWestT: neweyWestT(picked),
    cagr: Math.pow(wealth, 12 / count) - 1,
    volatility: deviation * Math.sqrt(12),
    worstDrawdown,
    worstMonth: Math.min(...picked),
    positive: picked.filter((value) => value > 0).length / count,
  };
  const market = decode(snapshot.benchmarks[marketKey]);
  const riskFree = decode(snapshot.benchmarks.rf);
  const xs = [];
  const ys = [];
  months.forEach((index, position) => {
    if (market[index] !== null && riskFree[index] !== null) {
      xs.push(market[index] - riskFree[index]);
      ys.push(leg === 'long_short' ? picked[position] : picked[position] - riskFree[index]);
    }
  });
  if (xs.length > 3) {
    const meanX = mean(xs);
    const meanY = mean(ys);
    let covariance = 0;
    let varianceX = 0;
    xs.forEach((x, index) => {
      covariance += (x - meanX) * (ys[index] - meanY);
      varianceX += (x - meanX) ** 2;
    });
    const beta = covariance / varianceX;
    const alpha = meanY - beta * meanX;
    let residual = 0;
    xs.forEach((x, index) => {
      residual += (ys[index] - alpha - beta * x) ** 2;
    });
    const scale = residual / (xs.length - 2);
    const alphaError = Math.sqrt(scale * (1 / xs.length + (meanX * meanX) / varianceX));
    result.alpha = alpha;
    result.alphaT = alpha / alphaError;
    result.beta = beta;
    result.alphaMonths = xs.length;
  }
  return result;
}

function readHash() {
  const hash = window.location.hash.replace('#', '');
  if (!hash) {
    return;
  }
  hash.split('-').forEach((part) => {
    if (/^j(3|6|9|12)$/.test(part)) state.j = Number(part.slice(1));
    else if (/^k(3|6|9|12)$/.test(part)) state.k = Number(part.slice(1));
    else if (/^skip[01]$/.test(part)) state.skip = Number(part.slice(4));
    else if (part === 'all') state.universe = 'U1';
    else if (part === 'top500') state.universe = 'U2';
    else if (part === 'ls') state.leg = 'long_short';
    else if (part === 'long') state.leg = 'buy';
    else if (part === 'losers') state.leg = 'sell';
    else if (part === 'net' || part === 'gross') state.costs = part;
    else if (/^impact[\d.]+$/.test(part)) {
      state.impact = Number(part.slice(6));
      state.impactTouched = true;
    } else if (/^brokerage[\d.]+$/.test(part)) state.brokerage = Number(part.slice(9));
    else if (/^fee[\d.]+$/.test(part)) state.fee = Number(part.slice(3));
    else if (/^flat[\d.]+$/.test(part)) state.flat = Number(part.slice(4));
    else if (/^from\d{4}\.\d{2}to\d{4}\.\d{2}$/.test(part)) {
      const start = part.slice(4, 11).replace('.', '-');
      const end = part.slice(13).replace('.', '-');
      state.sample = `${start}|${end}`;
    }
  });
  if (!state.impactTouched) {
    state.impact = defaultImpact(state.universe) * 100;
  }
}

function writeHash() {
  const universe = state.universe === 'U1' ? 'all' : 'top500';
  const leg = {long_short: 'ls', buy: 'long', sell: 'losers'}[state.leg];
  const [start, end] = state.sample.split('|');
  const parts = [
    `j${state.j}`,
    `k${state.k}`,
    `skip${state.skip}`,
    universe,
    leg,
    state.costs,
  ];
  if (state.impactTouched) parts.push(`impact${state.impact}`);
  if (state.brokerage) parts.push(`brokerage${state.brokerage}`);
  if (state.fee) parts.push(`fee${state.fee}`);
  if (state.flat !== 0.5) parts.push(`flat${state.flat}`);
  if (state.sample !== defaultSample()) {
    parts.push(`from${start.replace('-', '.')}to${end.replace('-', '.')}`);
  }
  const hash = `#${parts.join('-')}`;
  if (window.location.hash !== hash) {
    history.replaceState(null, '', hash);
  }
}

function syncControls() {
  document.getElementById('control-j').value = String(state.j);
  document.getElementById('control-k').value = String(state.k);
  document.getElementById('control-skip').value = String(state.skip);
  document.getElementById('control-universe').value = state.universe;
  document.getElementById('control-leg').value = state.leg;
  document.getElementById('control-costs').value = state.costs;
  document.getElementById('control-impact').value = Number(state.impact).toFixed(2);
  document.getElementById('control-brokerage').value = Number(state.brokerage).toFixed(2);
  document.getElementById('control-fee').value = String(state.fee);
  document.getElementById('control-flat').value = String(state.flat);
  const sample = document.getElementById('control-sample');
  if ([...sample.options].some((option) => option.value === state.sample)) {
    sample.value = state.sample;
  }
}

function bindControls() {
  const bind = (id, handler) => {
    document.getElementById(id).addEventListener('change', (event) => {
      handler(event.target.value);
      update();
    });
  };
  bind('control-j', (value) => { state.j = Number(value); });
  bind('control-k', (value) => { state.k = Number(value); });
  bind('control-skip', (value) => { state.skip = Number(value); });
  bind('control-universe', (value) => {
    state.universe = value;
    if (!state.impactTouched) {
      state.impact = defaultImpact(value) * 100;
    }
  });
  bind('control-leg', (value) => { state.leg = value; });
  bind('control-costs', (value) => { state.costs = value; });
  bind('control-impact', (value) => {
    state.impact = Math.max(0, Number(value) || 0);
    state.impactTouched = Math.abs(state.impact - defaultImpact(state.universe) * 100) > 1e-9;
  });
  bind('control-brokerage', (value) => { state.brokerage = Math.max(0, Number(value) || 0); });
  bind('control-fee', (value) => { state.fee = Math.max(0, Number(value) || 0); });
  bind('control-flat', (value) => { state.flat = Math.max(0, Number(value) || 0); });
  bind('control-sample', (value) => { state.sample = value; });
  window.addEventListener('hashchange', () => {
    readHash();
    update();
  });
  document.getElementById('copy-citation').addEventListener('click', () => {
    const text = document.getElementById('citation-text').textContent;
    navigator.clipboard.writeText(text).then(() => {
      document.getElementById('copy-citation').textContent = 'Copied';
    });
  });
}

function renderSummary() {
  const [start, end] = state.sample.split('|');
  const costText = state.costs === 'gross'
    ? 'before costs'
    : `after costs (impact ${Number(state.impact).toFixed(2)}% and brokerage ${Number(state.brokerage).toFixed(2)}% per side${state.leg === 'long_short' && state.fee ? `, borrowing fee ${state.fee}% a year` : ''})`;
  const gap = state.skip ? 'one-week gap' : 'no gap';
  document.getElementById('spec-summary').innerHTML =
    `<b>J = ${state.j}, K = ${state.k}</b>, ${gap}, ${UNIVERSE_NAMES[state.universe]}, ` +
    `${LEG_NAMES[state.leg].toLowerCase()}, ${costText}, ${start} to ${end}. ` +
    `Link to this view: <code>${window.location.hash || '#'}</code>`;
}

function renderHeadline(indices) {
  const rows = [];
  const legs = state.leg === 'long_short' ? ['long_short', 'buy', 'sell'] : [state.leg];
  legs.forEach((leg) => {
    ['gross', 'net'].forEach((costs) => {
      const values = returns(state.universe, state.skip, state.j, state.k, leg, costs);
      const stats = statistics(values, indices, leg);
      rows.push({label: `${LEG_NAMES[leg]}, ${costs === 'gross' ? 'before' : 'after'} costs`, stats, chosen: leg === state.leg && costs === state.costs});
    });
  });
  const market = statistics(decode(snapshot.benchmarks.market), indices, 'buy');
  rows.push({label: 'Indian market (IIMA)', stats: market, chosen: false});
  let html = '<thead><tr><th>Portfolio</th><th>Months</th><th>Mean, %<br>(NW <i>t</i>)</th><th>CAGR, %</th><th>Worst drawdown, %</th><th>Alpha, %<br>(<i>t</i>)</th><th>Beta</th></tr></thead><tbody>';
  rows.forEach((row) => {
    const s = row.stats;
    html += `<tr class="${row.chosen ? 'highlight' : ''}"><th>${row.label}</th>` +
      `<td>${s.count}</td>${cell(s.mean, s.neweyWestT)}` +
      `<td>${percent(s.cagr, 1)}</td>` +
      `<td>${percent(s.worstDrawdown, 1)}</td>` +
      `${row.label.startsWith('Indian') ? '<td></td>' : cell(s.alpha, s.alphaT)}` +
      `<td>${row.label.startsWith('Indian') ? '' : signed(s.beta)}</td></tr>`;
  });
  html += '</tbody>';
  document.getElementById('table-headline').innerHTML = html;
}

function wealthCurve(values, indices) {
  const points = [];
  let wealth = null;
  indices.forEach((index) => {
    const value = values[index];
    if (value === null || value === undefined) {
      if (wealth !== null) points.push([snapshot.months[index], wealth]);
      return;
    }
    wealth = (wealth === null ? 1 : wealth) * (1 + value);
    points.push([snapshot.months[index], wealth]);
  });
  return points;
}

function narrow() {
  return window.innerWidth < 600;
}

function dateAxis() {
  return {
    type: 'category',
    boundaryGap: false,
    axisLabel: {interval: narrow() ? 59 : 23, formatter: (value) => value.slice(0, 4)},
  };
}

function baseOptions() {
  return {
    textStyle: {fontFamily: FONT, fontSize: 13, color: '#202124'},
    animation: false,
    grid: {left: 56, right: 18, top: narrow() ? 78 : 44, bottom: 36},
    tooltip: {trigger: 'axis', axisPointer: {type: 'cross'}},
    legend: {top: 0, itemGap: narrow() ? 12 : 28, textStyle: {fontFamily: FONT, fontSize: 13}},
  };
}

function chart(id) {
  if (!charts[id]) {
    charts[id] = echarts.init(document.getElementById(id), null, {renderer: 'svg'});
  }
  return charts[id];
}

function renderGrowth(indices) {
  const lines = [];
  const chosen = returns(state.universe, state.skip, state.j, state.k, state.leg, state.costs);
  lines.push({name: `${LEG_NAMES[state.leg]} (chosen)`, data: wealthCurve(chosen, indices), colour: COLOURS.blue, width: 2.6});
  if (state.leg !== 'buy') {
    lines.push({name: 'Winners', data: wealthCurve(returns(state.universe, state.skip, state.j, state.k, 'buy', state.costs), indices), colour: COLOURS.green, width: 1.6});
  }
  if (state.leg !== 'sell') {
    lines.push({name: 'Losers', data: wealthCurve(returns(state.universe, state.skip, state.j, state.k, 'sell', state.costs), indices), colour: COLOURS.red, width: 1.6});
  }
  lines.push({name: 'Indian market', data: wealthCurve(decode(snapshot.benchmarks.market), indices), colour: COLOURS.grey, width: 1.6});
  const options = baseOptions();
  options.xAxis = dateAxis();
  options.yAxis = {type: 'log', logBase: 10, name: 'Growth of ₹1', nameTextStyle: {fontFamily: FONT}, axisLabel: {formatter: (value) => (value >= 1 ? value.toFixed(0) : value.toFixed(2))}, splitLine: {lineStyle: {color: '#e8eaed'}}};
  options.tooltip.valueFormatter = (value) => (Number.isFinite(value) ? value.toFixed(2) : '');
  options.series = lines.map((line) => ({name: line.name, type: 'line', showSymbol: false, data: line.data, lineStyle: {width: line.width, color: line.colour}, itemStyle: {color: line.colour}}));
  chart('chart-growth').setOption(options, true);
}

function renderDrawdown(indices) {
  const values = returns(state.universe, state.skip, state.j, state.k, state.leg, state.costs);
  const points = [];
  let wealth = 1;
  let peak = 1;
  indices.forEach((index) => {
    const value = values[index];
    if (value === null || value === undefined) return;
    wealth *= 1 + value;
    peak = Math.max(peak, wealth);
    points.push([snapshot.months[index], (wealth / peak - 1) * 100]);
  });
  const options = baseOptions();
  options.legend = {show: false};
  options.grid.top = 16;
  options.xAxis = dateAxis();
  options.yAxis = {type: 'value', max: 0, axisLabel: {formatter: '{value}%'}, splitLine: {lineStyle: {color: '#e8eaed'}}};
  options.tooltip.valueFormatter = (value) => `${value.toFixed(1)}%`;
  options.series = [{name: 'Drawdown', type: 'line', showSymbol: false, data: points, lineStyle: {width: 1.2, color: COLOURS.red}, areaStyle: {color: 'rgba(234, 67, 53, 0.18)'}, itemStyle: {color: COLOURS.red}}];
  chart('chart-drawdown').setOption(options, true);
}

function renderGrid(indices) {
  const legs = [['sell', 'Sell'], ['buy', 'Buy'], ['long_short', 'Buy − sell']];
  let html = '<thead><tr><th><i>J</i></th><th class="text">Portfolio</th><th><i>K</i> = 3</th><th><i>K</i> = 6</th><th><i>K</i> = 9</th><th><i>K</i> = 12</th></tr></thead><tbody>';
  const heat = [];
  [3, 6, 9, 12].forEach((j, row) => {
    legs.forEach(([leg, label], position) => {
      const chosenRow = j === state.j && leg === state.leg;
      html += `<tr class="${position === 0 ? 'group-start' : ''} ${chosenRow ? 'highlight' : ''}"><th>${position === 0 ? j : ''}</th><th>${label}</th>`;
      [3, 6, 9, 12].forEach((k, column) => {
        const values = returns(state.universe, state.skip, j, k, leg, state.costs);
        const stats = statistics(values, indices, leg);
        html += cell(stats.mean, stats.neweyWestT);
        if (leg === state.leg) {
          heat.push([column, 3 - row, Number.isFinite(stats.mean) ? stats.mean * 100 : null]);
        }
      });
      html += '</tr>';
    });
  });
  html += '</tbody>';
  document.getElementById('table-grid').innerHTML = html;
  const shown = heat.map((point) => point[2]).filter((value) => value !== null);
  const lowest = Math.min(...shown);
  const highest = Math.max(...shown);
  const diverging = lowest < 0;
  const largest = Math.max(Math.abs(lowest), Math.abs(highest), 0.1);
  const options = baseOptions();
  options.legend = {show: false};
  options.tooltip = {};
  options.grid = {left: 70, right: 90, top: 16, bottom: 48};
  options.xAxis = {type: 'category', data: ['K = 3', 'K = 6', 'K = 9', 'K = 12'], splitArea: {show: true}};
  options.yAxis = {type: 'category', data: ['J = 12', 'J = 9', 'J = 6', 'J = 3'], splitArea: {show: true}};
  options.visualMap = diverging
    ? {min: -largest, max: largest, calculable: false, orient: 'vertical', right: 0, top: 'middle', inRange: {color: [COLOURS.red, COLOURS.light, COLOURS.blue]}, text: ['higher', 'lower'], textStyle: {fontFamily: FONT}}
    : {min: Math.max(0, lowest - 0.15), max: highest, calculable: false, orient: 'vertical', right: 0, top: 'middle', inRange: {color: ['#e8f0fe', COLOURS.blue]}, text: ['higher', 'lower'], textStyle: {fontFamily: FONT}};
  options.series = [{type: 'heatmap', data: heat, label: {show: true, formatter: (point) => (point.value[2] === null ? '' : point.value[2].toFixed(2)), fontFamily: FONT, fontSize: 14}}];
  options.tooltip.formatter = (point) => `${['J = 12', 'J = 9', 'J = 6', 'J = 3'][point.value[1]]}, ${['K = 3', 'K = 6', 'K = 9', 'K = 12'][point.value[0]]}: ${point.value[2].toFixed(2)}% a month`;
  chart('chart-heat').setOption(options, true);
}

function renderCalendar(indices) {
  const values = returns(state.universe, state.skip, state.j, state.k, state.leg, state.costs);
  const sums = Array(12).fill(0);
  const counts = Array(12).fill(0);
  const positives = Array(12).fill(0);
  indices.forEach((index) => {
    const value = values[index];
    if (value === null || value === undefined) return;
    const month = Number(snapshot.months[index].slice(5, 7)) - 1;
    sums[month] += value;
    counts[month] += 1;
    if (value > 0) positives[month] += 1;
  });
  const names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const averages = sums.map((total, index) => (counts[index] ? (total / counts[index]) * 100 : null));
  const options = baseOptions();
  options.legend = {show: false};
  options.grid.top = 20;
  options.tooltip = {trigger: 'axis', formatter: (points) => {
    const index = points[0].dataIndex;
    return `${names[index]}: ${averages[index].toFixed(2)}% average, positive in ${Math.round((positives[index] / counts[index]) * 100)}% of ${counts[index]} years`;
  }};
  options.xAxis = {type: 'category', data: names};
  options.yAxis = {type: 'value', axisLabel: {formatter: '{value}%'}, splitLine: {lineStyle: {color: '#e8eaed'}}};
  options.series = [{type: 'bar', data: averages.map((value) => ({value, itemStyle: {color: value >= 0 ? COLOURS.blue : COLOURS.red}})), label: {show: true, position: 'top', formatter: (point) => `${Math.round((positives[point.dataIndex] / counts[point.dataIndex]) * 100)}%`, fontFamily: FONT, fontSize: 11, color: COLOURS.grey}}];
  chart('chart-calendar').setOption(options, true);
}

function renderPaper() {
  let html = '<thead><tr><th><i>J</i></th><th class="text">Portfolio</th><th><i>K</i> = 3</th><th><i>K</i> = 6</th><th><i>K</i> = 9</th><th><i>K</i> = 12</th></tr></thead><tbody>';
  Object.entries(PAPER_TABLE).forEach(([j, legs]) => {
    Object.entries(legs).forEach(([label, values], position) => {
      html += `<tr class="${position === 0 ? 'group-start' : ''}"><th>${position === 0 ? j : ''}</th><th>${label}</th>`;
      values.forEach(([value, tValue]) => { html += cell(value, tValue); });
      html += '</tr>';
    });
  });
  document.getElementById('table-paper').innerHTML = `${html}</tbody>`;
}

function liveEntry(universe, skip, j, k) {
  return snapshot.live[`${universe}|${skip}|${j}|${k}`];
}

function renderDeciles() {
  const rows = liveEntry(state.universe, state.skip, state.j, state.k).joint.All.deciles;
  let html = '<thead><tr><th>Decile</th><th>Mean, %</th><th>Beta</th><th>Alpha, %</th><th>Traded value, ₹ crore</th></tr></thead><tbody>';
  rows.forEach(([decile, mean, t, alpha, alphaT, beta, traded]) => {
    const label = decile === '10-1' ? '10 − 1' : decile === '1' ? '1 (losers)' : decile === '10' ? '10 (winners)' : decile;
    html += `<tr class="${decile === '10-1' ? 'group-start' : ''}"><th>${label}</th>${cell(mean, t)}<td>${signed(beta)}</td>${cell(alpha, alphaT)}<td>${traded === null ? '' : traded.toFixed(1)}</td></tr>`;
  });
  document.getElementById('table-deciles').innerHTML = `${html}</tbody>`;
}

function renderGroups() {
  const joint = liveEntry('U1', state.skip, state.j, state.k).joint;
  const groups = Object.keys(joint);
  let html = `<thead><tr><th></th>${groups.map((group) => `<th>${group}</th>`).join('')}</tr></thead><tbody>`;
  const pick = (group, decile) => joint[group].deciles.find((row) => row[0] === decile);
  html += `<tr class="group-start"><th colspan="${groups.length + 1}"><i>Panel A: average monthly return, %</i></th></tr>`;
  ['1', '2', '5', '9', '10', '10-1'].forEach((decile) => {
    html += `<tr><th>${decile === '10-1' ? 'P10 − P1' : `P${decile}`}</th>`;
    groups.forEach((group) => { const row = pick(group, decile); html += cell(row[1], row[2]); });
    html += '</tr>';
  });
  html += `<tr class="group-start"><th colspan="${groups.length + 1}"><i>Panel B: alpha against the market, %</i></th></tr>`;
  ['1', '10', '10-1'].forEach((decile) => {
    html += `<tr><th>${decile === '10-1' ? 'P10 − P1' : `P${decile}`}</th>`;
    groups.forEach((group) => { const row = pick(group, decile); html += cell(row[3], row[4]); });
    html += '</tr>';
  });
  document.getElementById('table-groups').innerHTML = `${html}</tbody>`;
}

function renderEvent() {
  const first = snapshot.live.event[`U1|${state.skip}|${state.j}`];
  const second = snapshot.live.event[`U2|${state.skip}|${state.j}`];
  const options = baseOptions();
  options.xAxis = {type: 'category', name: 'Months after ranking', nameLocation: 'middle', nameGap: 26, data: first.cumulative.map((value, index) => index + 1)};
  options.yAxis = {type: 'value', axisLabel: {formatter: '{value}%'}, splitLine: {lineStyle: {color: '#e8eaed'}}};
  options.tooltip.valueFormatter = (value) => `${value.toFixed(2)}%`;
  options.series = [
    {name: 'Top 500', type: 'line', data: second.cumulative.map((value) => value * 100), lineStyle: {color: COLOURS.blue, width: 2.4}, itemStyle: {color: COLOURS.blue}, symbolSize: 4},
    {name: 'All NSE shares', type: 'line', data: first.cumulative.map((value) => value * 100), lineStyle: {color: COLOURS.green, width: 2}, itemStyle: {color: COLOURS.green}, symbolSize: 4},
  ];
  chart('chart-event').setOption(options, true);
  const months = [1, 2, 3, 4, 5, 6, 9, 12, 15, 18, 24, 30, 36];
  let html = '<thead><tr><th>Month after ranking</th><th>All NSE shares, %</th><th>Top 500, %</th></tr></thead><tbody>';
  months.forEach((month) => {
    html += `<tr><th>${month}</th>${cell(first.announce[month - 1], first.announce_t[month - 1])}${cell(second.announce[month - 1], second.announce_t[month - 1])}</tr>`;
  });
  document.getElementById('table-announcements').innerHTML = `${html}</tbody>`;
}

function renderTradeable() {
  const indices = snapshot.months.map((month, index) => index).filter((index) => snapshot.months[index] >= '2005-01');
  const rows = [];
  ['gross', 'net'].forEach((costs) => {
    const stats = statistics(returns('U2', state.skip, state.j, state.k, 'buy', costs), indices, 'buy');
    rows.push(['B', 'Top-500 winners, long only', state.j, state.k, costs, stats.count, stats.mean, stats.neweyWestT, stats.worstDrawdown, stats.alpha, stats.alphaT]);
  });
  snapshot.tables.portfolios_c_d.forEach((row) => {
    const match = row.portfolio.match(/J(\d+) K(\d+) (gross|net)$/);
    const [j, k, costs] = [Number(match[1]), Number(match[2]), match[3]];
    if (j !== state.j || k !== state.k) return;
    const isHedged = row.portfolio.startsWith('C');
    rows.push([isHedged ? 'C' : 'D', isHedged ? 'Winners hedged with NIFTY 50 futures, from 2012-03' : 'F&O shares, losers sold through futures', j, k, costs, row.periods, row.mean, row.newey_west_t, row.maximum_drawdown, row.alpha, row.alpha_t]);
  });
  let html = '<thead><tr><th></th><th class="text">Portfolio</th><th><i>J</i>/<i>K</i></th><th class="text">Costs</th><th>Months</th><th>Mean, %<br>(NW <i>t</i>)</th><th>Worst drawdown, %</th><th>Alpha, %<br>(<i>t</i>)</th></tr></thead><tbody>';
  let previous = '';
  ['B', 'C', 'D'].forEach((letter) => {
    rows.filter((row) => row[0] === letter).forEach((row) => {
      const start = row[0] !== previous;
      html += `<tr class="${start ? 'group-start' : ''}"><th>${start ? row[0] : ''}</th><th>${start ? row[1] : ''}</th><td>${row[2]}/${row[3]}</td><th>${row[4] === 'net' ? 'after' : 'before'}</th><td>${row[5]}</td>${cell(row[6], row[7])}<td>${percent(row[8], 1)}</td>${cell(row[9], row[10])}</tr>`;
      previous = row[0];
    });
  });
  document.getElementById('table-tradeable').innerHTML = `${html}</tbody>`;
}

function renderRobustness() {
  const rows = snapshot.tables.robustness.filter((row) => row.formation_months === state.j && row.holding_months === state.k);
  const find = (check, universe, leg) => rows.find((row) => row.check === check && row.universe === universe && row.leg === leg);
  const checks = [
    ['base', 'Base case'],
    ['trade one day after formation', 'Trade one day after the ranking close'],
    ['brokerage 0.03% per side', 'Brokerage of 0.03% per side'],
    ['all shares at 0.6% impact per side', 'Market impact doubled to 0.6% (all shares)'],
    ['delisting stress -30%', '−30% charged after a share stops trading'],
    ['delisting stress -100%', '−100% charged after a share stops trading'],
    ['short borrow fee 3% a year', 'Borrowing fee of 3% a year on the short leg'],
    ['top 200 universe', 'Top 200 in place of the top 500'],
  ];
  let html = '<thead><tr><th>Assumption</th><th>All shares, W − L, %</th><th>Top 500, W − L, %</th><th>Top 500, winners, %</th></tr></thead><tbody>';
  const base = [find('base', 'U1', 'long_short'), find('base', 'U2', 'long_short'), find('base', 'U2', 'buy')];
  html += `<tr><th>Base case, before costs</th>${base.map((row) => cell(row.gross_mean, row.gross_newey_west_t)).join('')}</tr>`;
  checks.forEach(([check, label]) => {
    const topUniverse = check === 'top 200 universe' ? 'U3' : 'U2';
    const parts = [find(check, 'U1', 'long_short'), find(check, topUniverse, 'long_short'), find(check, topUniverse, 'buy')];
    html += `<tr><th>${label}</th>${parts.map((row) => (row ? cell(row.net_mean, row.net_newey_west_t) : '<td></td>')).join('')}</tr>`;
  });
  document.getElementById('table-robustness').innerHTML = `${html}</tbody>`;
}

function mainIndices() {
  const indices = [];
  snapshot.months.forEach((month, index) => {
    if (month >= snapshot.main_sample[0] && month <= snapshot.main_sample[1]) {
      indices.push(index);
    }
  });
  return indices;
}

function reversedInJanuary(universe, skip, j, k, costs, series) {
  // Reversing a position in January trades the opposite book: the gross
  // return changes sign but the trading cost does not.
  const gross = returns(universe, skip, j, k, 'long_short', 'gross');
  return series.map((value, index) => {
    if (value === null || !snapshot.months[index].endsWith('-01')) {
      return value;
    }
    const cost = gross[index] - value;
    return -gross[index] - cost;
  });
}

function renderJanuaryCharts(indices, series) {
  const flipped = reversedInJanuary(state.universe, state.skip, state.j, state.k, state.costs, series);
  const years = [];
  const bars = [];
  indices.forEach((index) => {
    if (series[index] !== null && snapshot.months[index].endsWith('-01')) {
      years.push(snapshot.months[index].slice(0, 4));
      bars.push(series[index] * 100);
    }
  });
  let options = baseOptions();
  options.legend = {show: false};
  options.grid.top = 20;
  options.xAxis = {type: 'category', data: years, axisLabel: {fontFamily: FONT}};
  options.yAxis = {type: 'value', axisLabel: {formatter: '{value}%'}, splitLine: {lineStyle: {color: '#e8eaed'}}};
  options.tooltip.valueFormatter = (value) => `${value.toFixed(2)}%`;
  options.series = [{
    name: 'January return of the strategy', type: 'bar',
    data: bars.map((value) => ({value, itemStyle: {color: value >= 0 ? COLOURS.green : COLOURS.red}})),
  }];
  chart('chart-january-years').setOption(options, true);
  options = baseOptions();
  options.xAxis = dateAxis();
  options.yAxis = {type: 'log', logBase: 10, name: 'Growth of ₹1', nameTextStyle: {fontFamily: FONT}, axisLabel: {formatter: (value) => (value >= 1 ? value.toFixed(0) : value.toFixed(2))}, splitLine: {lineStyle: {color: '#e8eaed'}}};
  options.tooltip.valueFormatter = (value) => (Number.isFinite(value) ? value.toFixed(2) : '');
  options.series = [
    {name: 'As ranked', type: 'line', showSymbol: false, data: wealthCurve(series, indices), lineStyle: {width: 2.4, color: COLOURS.blue}, itemStyle: {color: COLOURS.blue}},
    {name: 'Reversed in every January', type: 'line', showSymbol: false, data: wealthCurve(flipped, indices), lineStyle: {width: 2.4, color: COLOURS.red}, itemStyle: {color: COLOURS.red}},
  ];
  chart('chart-january-growth').setOption(options, true);
}

function renderFurther(indices) {
  const universeName = state.universe === 'U1' ? 'All shares' : 'Top 500';
  const cells = [3, 6, 9, 12];
  const live = snapshot.live;
  const pct = (value, places = 2) => (Number.isFinite(value) ? (value * 100).toFixed(places) : '');
  const num = (value, places = 2) => (Number.isFinite(value) ? value.toFixed(places) : '');
  const pv = (value) => (!Number.isFinite(value) ? '' : value < 0.001 ? '<0.001' : value.toFixed(3));
  const fill = (id, html) => {
    document.getElementById(id).innerHTML = html;
  };
  const mark = (j, k) => (j === state.j && k === state.k ? ' class="highlight"' : '');
  const costs = state.costs;

  // Table 9: January reversal at every J and K.
  let html = '<thead><tr><th>J/K</th><th>Normal, % a month</th><th>Reversed, % a month</th><th>Normal, % a year</th><th>Reversed, % a year</th><th>Average January spread, %</th><th>Reversal loses / gains</th><th><i>t</i></th></tr></thead><tbody>';
  cells.forEach((j) => {
    cells.forEach((k) => {
      const series = returns(state.universe, state.skip, j, k, 'long_short', costs);
      const flipped = reversedInJanuary(state.universe, state.skip, j, k, costs, series);
      const januaries = [];
      const spreads = [];
      indices.forEach((index) => {
        if (series[index] !== null && snapshot.months[index].endsWith('-01')) {
          januaries.push(flipped[index]);
          spreads.push(series[index]);
        }
      });
      const normal = statistics(series, indices, 'long_short');
      const changed = statistics(flipped, indices, 'long_short');
      const average = mean(januaries);
      const spread = Math.sqrt(januaries.reduce((total, value) => total + (value - average) ** 2, 0) / (januaries.length - 1));
      const t = average / (spread / Math.sqrt(januaries.length));
      html += `<tr${mark(j, k)}><th>${j}/${k}</th><td>${pct(normal.mean)}</td><td>${pct(changed.mean)}</td><td>${pct(normal.cagr, 1)}</td><td>${pct(changed.cagr, 1)}</td><td>${pct(mean(spreads))}</td><td>${januaries.filter((value) => value < 0).length} / ${januaries.filter((value) => value > 0).length}</td><td>${num(t)}</td></tr>`;
    });
  });
  fill('table-january', `${html}</tbody>`);
  renderJanuaryCharts(indices, returns(state.universe, state.skip, state.j, state.k, 'long_short', costs));

  // Table 10: Section III, looked up.
  const entry = live[`${state.universe}|${state.skip}|${state.j}|${state.k}`];
  const three = entry.section3;
  html = `<thead><tr><th>Panel A. ${universeName}, ${state.j}/${state.k}${state.skip ? ', one-week gap' : ''}</th><th>Months</th><th>Mean, % per ${state.k} months</th><th>NW <i>t</i></th></tr></thead><tbody>`;
  [['wrss', 'Weighted relative strength strategy'], ['deciles', 'Decile winners minus losers']].forEach(([name, label]) => {
    const row = three.series[name];
    html += `<tr><th>${label}</th><td>${row.months}</td><td>${pct(row.mean)}</td><td>${num(row.t)}</td></tr>`;
  });
  html += `<tr><th>Correlation of the two</th><td></td><td>${num(three.correlation)}</td><td></td></tr>`;
  html += '</tbody><thead><tr><th>Panel B</th><th>Total</th><th>Dispersion</th><th>Factor</th><th>Idiosyncratic</th></tr></thead><tbody>';
  three.decomposition.forEach((row) => {
    html += `<tr><th>${row.label}</th><td>${pct(row.total)}</td><td>${pct(row.dispersion)}</td><td>${pct(row.factor)}</td><td>${pct(row.idiosyncratic)}</td></tr>`;
  });
  html += '</tbody><thead><tr><th>Panel C</th><th>Sample</th><th>&theta;</th><th><i>t</i></th></tr></thead><tbody>';
  [['wrss', 'Weighted relative strength'], ['deciles', 'Decile spread']].forEach(([name, label]) => {
    three.series[name].lead_lag.forEach((part) => {
      html += `<tr><th>${label}</th><td>${part.sample}</td><td>${num(part.theta)}</td><td>${num(part.t)}</td></tr>`;
    });
  });
  fill('table-section3', `${html}</tbody>`);

  // Table 11: flat charge on every side.
  html = '<thead><tr><th>J/K</th><th>Before the charge, % a month</th><th>After the charge, % a month</th><th>Alpha a year, % (<i>t</i>)</th></tr></thead><tbody>';
  cells.forEach((j) => {
    cells.forEach((k) => {
      const gross = returns(state.universe, state.skip, j, k, 'long_short', 'gross');
      const traded = turnover(state.universe, state.skip, j, k, 'long_short');
      const net = gross.map((value, index) => (value === null ? null : value - (state.flat / 100) * (traded[index] || 0)));
      const before = statistics(gross, indices, 'long_short');
      const after = statistics(net, indices, 'long_short');
      html += `<tr${mark(j, k)}><th>${j}/${k}</th><td>${pct(before.mean)}</td><td>${pct(after.mean)}</td>${cell(after.alpha * 12, after.alphaT)}</tr>`;
    });
  });
  fill('table-flat', `${html}</tbody>`);

  // Table 12: alphas against two markets for the chosen strategy.
  html = '<thead><tr><th>Portfolio</th><th>Market</th><th>Alpha, % a month (<i>t</i>)</th><th>Beta</th></tr></thead><tbody>';
  ['long_short', 'buy', 'sell'].forEach((leg) => {
    const series = returns(state.universe, state.skip, state.j, state.k, leg, costs);
    [['market', 'Value weighted (IIMA)'], ['equal_market', 'Equally weighted (all shares)']].forEach(([key, label]) => {
      const result = statistics(series, indices, leg, key);
      html += `<tr><th>${LEG_NAMES[leg]}</th><td>${label}</td>${cell(result.alpha, result.alphaT)}<td>${num(result.beta)}</td></tr>`;
    });
  });
  fill('table-alpha', `${html}</tbody>`);

  // Table 13: buy-and-hold against rebalanced, main sample.
  const main = mainIndices();
  html = '<thead><tr><th>J/K</th><th>Bought and held, % a month (<i>t</i>)</th><th>Rebalanced, % a month (<i>t</i>)</th></tr></thead><tbody>';
  cells.forEach((j) => {
    cells.forEach((k) => {
      const held = live[`${state.universe}|${state.skip}|${j}|${k}`].hold;
      const rebalanced = statistics(returns(state.universe, state.skip, j, k, 'long_short', 'gross'), main, 'long_short');
      html += `<tr${mark(j, k)}><th>${j}/${k}</th>${cell(held.mean, held.t)}${cell(rebalanced.mean, rebalanced.neweyWestT)}</tr>`;
    });
  });
  fill('table-hold', `${html}</tbody>`);

  // Table 14: joint tests, looked up.
  html = `<thead><tr><th>${universeName}, ${state.j}/${state.k}${state.skip ? ', one-week gap' : ''}</th><th>Equal returns, F (<i>p</i>)</th><th>Zero alphas, F (<i>p</i>)</th><th>Same in every month, F (<i>p</i>)</th><th>Same, February to December, F (<i>p</i>)</th></tr></thead><tbody>`;
  const show = (pair) => `${num(pair[0])} (${pv(pair[1])})`;
  Object.entries(entry.joint).forEach(([group, row]) => {
    html += `<tr><th>${group}</th><td>${show(row.equal)}</td><td>${show(row.alpha)}</td><td>${show(row.calendar)}</td><td>${show(row.calendar_feb_dec)}</td></tr>`;
  });
  fill('table-joint', `${html}</tbody>`);
}

function defaultSample() {
  return `${snapshot.main_sample[0]}|${snapshot.main_sample[1]}`;
}

function fillProse() {
  const end = snapshot.main_sample[1];
  const endYear = end.slice(0, 4);
  const fixed = (key, leg) => decode(snapshot.series[`${key}|${leg}`].g);
  const netFixed = (key, leg) => decode(snapshot.series[`${key}|${leg}`].n);
  const main = mainIndices();
  const gross = statistics(fixed('U2|0|6|6', 'long_short'), main, 'long_short');
  const net = statistics(netFixed('U2|0|6|6', 'long_short'), main, 'long_short');
  const all = statistics(netFixed('U1|0|6|6', 'long_short'), main, 'long_short');
  const values = {
    end_label: snapshot.prose.end_label,
    end_year: endYear,
    iima_end: snapshot.prose.iima_end,
    data_to: snapshot.prose.data_to,
    months: String(main.length),
    trading_days: snapshot.prose.trading_days,
    symbols: snapshot.prose.symbols,
    u2_gross: (gross.mean * 100).toFixed(2),
    u2_net: (net.mean * 100).toFixed(2),
    u2_t: net.neweyWestT.toFixed(2),
    u1_net: (all.mean * 100).toFixed(2),
  };
  document.querySelectorAll('[data-fill]').forEach((node) => {
    const value = values[node.dataset.fill];
    if (value !== undefined) {
      node.textContent = value;
    }
  });
  const sample = document.getElementById('control-sample');
  const first = snapshot.main_sample[0];
  const monthsInSample = snapshot.months.filter((month) => month >= first && month <= end);
  const middle = Math.floor(monthsInSample.length / 2);
  const label = (month) => month.slice(0, 4);
  [...sample.options].forEach((option) => {
    if (option.dataset.half === 'first') {
      option.value = `${first}|${monthsInSample[middle - 1]}`;
      option.textContent = `${label(first)} to ${label(monthsInSample[middle - 1])} (first half)`;
    } else if (option.dataset.half === 'second') {
      option.value = `${monthsInSample[middle]}|${end}`;
      option.textContent = `${label(monthsInSample[middle])} to ${endYear} (second half)`;
    } else {
      option.value = option.value.replace('2026-10', end);
      option.textContent = option.textContent.replace('2026', endYear);
    }
  });
}

function update() {
  syncControls();
  writeHash();
  const indices = sampleIndices();
  renderSummary();
  renderHeadline(indices);
  renderGrowth(indices);
  renderDrawdown(indices);
  renderGrid(indices);
  renderCalendar(indices);
  renderFurther(indices);
  renderDeciles();
  renderGroups();
  renderEvent();
  renderTradeable();
  renderRobustness();
}

async function start() {
  const response = await fetch('data/snapshot.json');
  snapshot = await response.json();
  document.getElementById('generated').textContent = snapshot.generated;
  state.sample = defaultSample();
  fillProse();
  state.impact = defaultImpact(state.universe) * 100;
  readHash();
  bindControls();
  renderPaper();
  update();
  window.addEventListener('resize', () => Object.values(charts).forEach((item) => item.resize()));
}

start();

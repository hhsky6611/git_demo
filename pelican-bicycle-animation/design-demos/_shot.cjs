const pw = require('/tmp/pwrun/node_modules/playwright');
(async () => {
  const jobs = [['d1-memphis-roulette.html', [1.15, 2.6]],
                ['d2-deadpan-field-notes.html', [1.4, 3.2]],
                ['d3-chomet-gouache.html', [1.6, 3.4]]];
  const b = await pw.chromium.launch();
  for (const [f, ts] of jobs) {
    const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
    const errs = [];
    p.on('pageerror', e => errs.push('PAGEERROR ' + e.message));
    p.on('console', m => { if (m.type() === 'error') errs.push('CONSOLE ' + m.text()); });
    await p.goto('file://' + __dirname + '/' + f, { waitUntil: 'load' });
    await p.waitForFunction(() => window.__ready === true, { timeout: 15000 }).catch(() => errs.push('NO __ready'));
    for (const t of ts) {
      await p.evaluate(tt => { window.__pause && window.__pause(); window.__seek(tt); }, t);
      await p.waitForTimeout(250);
      await p.screenshot({ path: f.replace('.html', '') + '-t' + t + '.png' });
    }
    console.log(f, '::', errs.length ? errs.slice(0, 3).join(' | ') : 'no console errors');
    await p.close();
  }
  await b.close();
})();

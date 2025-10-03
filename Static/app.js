// UI logic for TradeBot
const symbolSelect = document.getElementById("symbolSelect");
const monthsSelect = document.getElementById("monthsSelect");
const intervalSelect = document.getElementById("intervalSelect");
const runBtn = document.getElementById("runBtn");
const uploadCsvBtn = document.getElementById("uploadCsv");
const csvFile = document.getElementById("csvFile");
const statsDiv = document.getElementById("stats");
const tradesTbody = document.querySelector("#tradesTable tbody");
const balanceEl = document.getElementById("balance");
let chart;

async function loadSymbols(){
  try{
    const res = await fetch("/api/status");
    const j = await res.json();
    const syms = j.symbols || ["ETHUSDT"];
    symbolSelect.innerHTML = syms.map(s=>`<option value="${s}">${s}</option>`).join("");
    balanceEl.innerText = `رصيد افتراضي: $${(j.balance||10).toFixed(2)}`;
  }catch(e){
    console.error(e);
  }
}
loadSymbols();

runBtn.onclick = async ()=>{
  const symbol = symbolSelect.value;
  const months = parseInt(monthsSelect.value);
  const interval = intervalSelect.value;
  statsDiv.innerText = "جاري تشغيل المحاكاة...";
  const payload = {symbol, months, interval, initial_balance:10.0};
  try{
    const res = await fetch("/api/backtest", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if(data.error){ statsDiv.innerText = "خطأ: " + data.error; return; }
    const stats = data.stats;
    const trades = data.trades || [];
    statsDiv.innerHTML = `البداية: $${stats.initial_balance} — النهاية: $${stats.final_balance} — صفقات: ${stats.trades} — فوز: ${stats.wins} — خسارة: ${stats.losses} — نسبة فوز: ${stats.win_rate}%`;
    balanceEl.innerText = `رصيد افتراضي: $${stats.final_balance}`;
    updateTrades(trades);
    // fetch recent candles to draw chart
    const c = await fetch(`/api/candles?symbol=${symbol}&limit=500&interval=${interval}`).then(r=>r.json());
    if(!c.error) buildChart(c.candles);
  }catch(e){
    statsDiv.innerText = "خطأ في السيرفر: " + e.toString();
  }
};

uploadCsvBtn.onclick = ()=> csvFile.click();
csvFile.onchange = async (e)=>{
  const f = e.target.files[0];
  if(!f) return;
  const fd = new FormData();
  fd.append("csv", f);
  try{
    const res = await fetch("/api/backtest", {method:"POST", body: fd});
    const data = await res.json();
    if(data.error){ alert("Upload error: "+data.error); return; }
    alert("تم رفع CSV وتشغيل المحاكاة. انظر النتائج بالواجهة.");
    const stats = data.stats; const trades = data.trades || [];
    statsDiv.innerHTML = `البداية: $${stats.initial_balance} — النهاية: $${stats.final_balance} — صفقات: ${stats.trades}`;
    updateTrades(trades);
  }catch(e){
    alert("Upload failed: "+e.toString());
  }
};

function updateTrades(trades){
  tradesTbody.innerHTML = trades.slice().reverse().map(t=>`<tr>
    <td>${new Date(t.time).toLocaleString()}</td>
    <td>${t.entry?.toFixed(6)||''}</td>
    <td>${t.exit?.toFixed(6)||''}</td>
    <td class="${t.profit>=0?'green':'red'}">${t.profit?.toFixed(6)||''}</td>
    <td>${t.balance_after?.toFixed(6)||''}</td>
    <td>${t.reason||''}</td>
  </tr>`).join('');
}

function buildChart(candles){
  const ds = candles.map(c=>({x:new Date(c.time), o:c.open, h:c.high, l:c.low, c:c.close}));
  const ctx = document.getElementById("chart").getContext("2d");
  if(chart) chart.destroy();
  chart = new Chart(ctx, {
    type:'candlestick',
    data:{datasets:[{label:'Price', data:ds}]},
    options:{plugins:{legend:{display:false}}, scales:{x:{time:{unit:'minute'}}}}
  });
}

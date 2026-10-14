const form = document.querySelector('#search-form');
const stationInput = document.querySelector('#station');
const startInput = document.querySelector('#start');
const endInput = document.querySelector('#end');
const searchButton = document.querySelector('#search-button');
const exportButton = document.querySelector('#export-button');
const statusText = document.querySelector('#status');
const errorBox = document.querySelector('#error');
const tbody = document.querySelector('#table-body');
const countText = document.querySelector('#count');
let records = [];
let sortState = {key: 'date', ascending: true};

function applyDateMask(input) {
  const digits = input.value.replace(/\D/g, '').slice(0, 8);
  let value = digits;
  if (digits.length > 4) value = `${digits.slice(0,2)}/${digits.slice(2,4)}/${digits.slice(4)}`;
  else if (digits.length > 2) value = `${digits.slice(0,2)}/${digits.slice(2)}`;
  input.value = value;
}
document.querySelectorAll('.date-mask').forEach(input => {
  input.addEventListener('input', () => applyDateMask(input));
  input.addEventListener('keydown', event => {
    if (event.key.length === 1 && !/\d/.test(event.key) && !event.ctrlKey && !event.metaKey) event.preventDefault();
  });
});
function parseDate(value) { const [d,m,y] = value.split('/').map(Number); return new Date(y, m-1, d); }
function compareRecords(a,b,key) {
  if (key === 'date') return parseDate(a.date) - parseDate(b.date);
  if (key === 'time') return (a.time || '').localeCompare(b.time || '');
  if (key === 'rain') {
    const num = value => { const n = Number(String(value).trim().replace(/\s/g,'').replace(',','.')); return Number.isFinite(n) ? n : -Infinity; };
    return num(a.rain) - num(b.rain);
  }
  return String(a[key] ?? '').localeCompare(String(b[key] ?? ''), 'pt-BR', {numeric:true, sensitivity:'base'});
}
function renderTable() {
  const sorted = [...records].sort((a,b) => compareRecords(a,b,sortState.key) * (sortState.ascending ? 1 : -1));
  document.querySelectorAll('.sort').forEach(button => {
    const active = button.dataset.key === sortState.key;
    button.querySelector('span').textContent = active ? (sortState.ascending ? '▲' : '▼') : '';
    button.setAttribute('aria-label', `${button.textContent.trim()}${active ? (sortState.ascending ? ', ordem crescente' : ', ordem decrescente') : ', ordenar'}`);
  });
  tbody.replaceChildren();
  if (!sorted.length) {
    const tr = document.createElement('tr'); tr.className = 'empty'; const td = document.createElement('td'); td.colSpan = 4; td.textContent = 'Nenhum registro para exibir.'; tr.append(td); tbody.append(tr);
  } else {
    sorted.forEach(record => {
      const tr = document.createElement('tr');
      [record.station, record.date, record.time, record.rain].forEach((value, index) => {
        const td = document.createElement('td'); td.textContent = value ?? '';
        if (index === 3) td.className = 'numeric-cell';
        tr.append(td);
      }); tbody.append(tr);
    });
  }
  countText.textContent = `${records.length} registro${records.length === 1 ? '' : 's'}`;
  exportButton.disabled = records.length === 0;
}
document.querySelectorAll('.sort').forEach(button => button.addEventListener('click', () => {
  const key = button.dataset.key;
  if (sortState.key === key) sortState.ascending = !sortState.ascending;
  else sortState = {key, ascending:true};
  renderTable();
}));
form.addEventListener('submit', async event => {
  event.preventDefault(); errorBox.hidden = true; searchButton.disabled = true; searchButton.textContent = 'Consultando…'; exportButton.disabled = true;
  statusText.textContent = 'Consultando a API da ANA…'; records = []; renderTable();
  try {
    const response = await fetch('/api/consultar', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({station:stationInput.value.trim(), start:startInput.value.trim(), end:endInput.value.trim()})});
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'Falha na consulta.');
    records = result.records || []; sortState = {key:'date', ascending:true}; renderTable(); statusText.textContent = result.message || 'Consulta concluída.';
  } catch (error) {
    statusText.textContent = 'Não foi possível concluir a consulta.'; errorBox.textContent = error.message; errorBox.hidden = false;
  } finally { searchButton.disabled = false; searchButton.textContent = 'Consultar'; }
});
exportButton.addEventListener('click', async () => {
  if (!records.length) return;
  exportButton.disabled = true;
  try {
    const sorted = [...records].sort((a,b) => compareRecords(a,b,sortState.key) * (sortState.ascending ? 1 : -1));
    const response = await fetch('/api/exportar', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({records:sorted})});
    if (!response.ok) { const data = await response.json(); throw new Error(data.error || 'Falha ao exportar CSV.'); }
    const blob = await response.blob(); const url = URL.createObjectURL(blob); const link = document.createElement('a'); link.href = url; link.download = 'precipitacao_ana.csv'; document.body.append(link); link.click(); link.remove(); URL.revokeObjectURL(url);
  } catch (error) { errorBox.textContent = error.message; errorBox.hidden = false; }
  finally { exportButton.disabled = records.length === 0; }
});
renderTable();

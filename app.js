(function(){
'use strict';
/* ---------- 공통 ---------- */
const D = window.DASH;
const $ = id => document.getElementById(id);
const store = {
  get(k, d){ try{ const v = localStorage.getItem('ndvidash.'+k); return v ? JSON.parse(v) : d; }catch(e){ return d; } },
  set(k, v){ try{ localStorage.setItem('ndvidash.'+k, JSON.stringify(v)); }catch(e){} }
};
const css = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const fmt = (v, d=2) => (v != null && Number.isFinite(v)) ? v.toFixed(d) : '–';
const esc = s => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const ALT = ['A','B','C'];

/* ---------- 언어 ---------- */
const IT = {
  navTasks:'Verifica', navRoads:'Gerarchia stradale', navDash:'Indicatore ⑦', navCcs:'Tabella CCS', navMatrix:'Alternative',
  siteD:'Dongtan A', siteC:'Campus Cheonan',
  hdrSec:'Pianificazione urbana smart, settimana 7 — gerarchia stradale · infrastruttura verde · tabella CCS',
  hAreaL:'Superficie del confine', hNdviL:'NDVI medio nel confine', hLstL:'Temperatura superficiale media', heroBtn:'Vai alla verifica',
  hdrP:'NDVI e temperatura superficiale sono <b>valori satellitari reali</b> (Sentinel-2 L2A · Landsat 9 C2 L2). Inserendo il risultato della lettura i-Tree, la tabella e il confronto si ricalcolano.',
  tagline:'Dalla gerarchia stradale alla prima tabella CCS — i compiti ①~⑤ della settimana 7 in un’unica pagina.', tagBtn:'Esporta tabelle',
  tasksTitle:'Verifica dei compiti ①~⑤', tasksNote:'Scadenza 25.10.2026 23:59 · LMS settimana 7 · PDF + tabella (xlsx o csv) + file originale i-Tree (.itrcnpy)',
  roadsTitle:'① Gerarchia stradale · indice stradale', r1h:'Piano 1 (alternativa C della settimana 6) — tre livelli di arterie', r1t:'Regolamento artt. 10·11',
  r2h:'Sezione trasversale', r2t:'art. 10 c.7', r2s:'Larghezze di progetto con marciapiedi, piste ciclabili, spartitraffico e sosta. Interasse: principale 1.000 · secondaria 500 · di raccolta 250 m (art. 10 c.3).',
  kAccessL:'Celle edificabili entro 125 m da una strada', kComplyL:'Standard art. 11 rispettati',
  r3h:'Indice stradale per zona', r3t:'art. 11 c.1 · limite superiore escluso',
  r3n:'Indice arterie = principale + secondaria. Le strade locali non sono tracciate, quindi l’indice reale sarà più alto. Le intersezioni vanno al livello superiore. Il verde è solo attraversato: nessuno standard.',
  stepsTitle:'NDVI Sentinel-2 in 4 fasi',
  s1b:'Account e quote', s1d:'Account CDSE per studente · registro PU/crediti',
  s2b:'Selezione della scena', s2d:'Scene L2A per area, periodo e nuvole nel confine',
  s3b:'Ricezione delle bande', s3d:'Ricezione di B4 (665nm) e B8 (833nm) a 10m',
  s4b:'Calcolo NDVI', s4d:'(B8−B4)/(B8+B4) · media e distribuzione nel confine → indicatore ⑦',
  dashTitle:'③ Indicatore ⑦ — chioma · NDVI · temperatura superficiale',
  c1h:'① Account e quote', c1t:'Account CDSE gratuito',
  c1s:'Criteri: Sentinel Hub 10.000 PU/mese · 300 PU/min, openEO 10.000 crediti/mese (Quotas consultato il 2026-09-09)',
  thStu:'Studente', thPU:'PU usate', thCR:'Crediti openEO', btnAdd:'Aggiungi', phName:'Nome / matricola', phCR:'Crediti',
  lblRate:'PU stimate per richiesta · richieste al minuto (limite 300 PU/min)',
  c1n:'I valori reali sono stati scaricati dal mirror pubblico Microsoft Planetary Computer, che fornisce gli stessi prodotti senza account (ID scena identici). Il motivo della sostituzione è nel rapporto.',
  c2h:'② Selezione della scena', c2t:'nuvole nel confine',
  c2s:'Regola fissata prima: 01.06–30.09.2026 · coppia Sentinel-2 × Landsat 9 con la minore quota di nuvole/ombre nel confine · scarto ≤ 5 giorni · a parità, la più vicina al 1° agosto.',
  lblFrom:'Data inizio', lblTo:'Data fine', lblCC:'Nuvole max nel confine',
  c2n:'✓ = scena usata nei calcoli. Le nuvole della scena sono dell’intera tile; quelle nel confine sono contate con SCL (Sentinel-2) e QA_PIXEL (Landsat).',
  c3h:'③ Ricezione bande · ④ Calcolo NDVI',
  c3s:'Solo le bande a 10m B4 (rosso) e B8 (NIR) · correzione dell’offset BOA (−1000) · pixel di nuvole e ombre esclusi. Linea rossa = confine (popolazione statistica).',
  vGrid:'Griglia NDVI', vSat:'Foto satellitare', lblOp:'Opacità NDVI', lblTh:'Soglia del verde (ipotesi: ≥ 0,3)',
  kMeanL:'NDVI medio nel confine', kSdL:'Deviazione standard dei pixel', kGreenL:'Quota di pixel sopra soglia', kNL:'Pixel validi (10m)',
  histN:'Distribuzione NDVI nel confine (barre: classi di 0,05, linea blu: soglia)', lblPix:'Verifica di un pixel — riflettanza di B4 · B8',
  c4h:'Conversione della temperatura superficiale', c4s:'Valore pixel ST_B10 (DN) di Landsat 9 Collection 2 Level-2 → kelvin → Celsius',
  lblDN:'Valore pixel ST_B10 (DN)', pScL:'Scala applicata', pKL:'Kelvin (K)', pCL:'Celsius (°C)',
  kLstL:'LST media nel confine (30m)', kRL:'Correlazione NDVI–LST r',
  c4n:'Per ogni cella di 30m si media l’NDVI dei pixel di 10m (3×3) e lo si confronta con la LST della stessa cella.',
  c4i:'<b>LST ≠ temperatura dell’aria</b> — temperatura della superficie all’ora di acquisizione. Confrontare scene di date simili e indicare la data (regola della 3ª lezione). Risoluzione termica originale (100m) e ricampionamento a 30m da verificare.',
  c5h:'② Lettura i-Tree Canopy su 500 punti', c5t:'Confine = popolazione statistica',
  c5s:'Inserendo il risultato letto in i-Tree Canopy si ricalcolano indicatore ⑦, tabella CCS e confronto (salvato solo in questo browser). Registrato <b>separatamente</b> dall’NDVI per pixel.',
  lblN:'Numero di punti N', lblTree:'Punti classificati come albero', lblDate:'Data di lettura', phTree:'da inserire dopo la lettura',
  kCanL:'Copertura arborea %', kSEL:'± SE (punti %)', kCanAL:'Superficie arborea (ha)', kDiffL:'Pixel con NDVI ≥ 0,5 (riferimento)',
  btnShp:'Scarica lo shapefile del confine', btnSim:'Prova: anteprima di 500 punti casuali',
  c5n1:'SE = √(p(1−p)/N) · superficie = superficie del confine × p ± superficie × SE. L’anteprima considera albero ogni pixel con NDVI ≥ 0,5: <b>non è un valore da consegnare</b>. Procedura: caricare lo shapefile → modalità semplice (Tree/Non-Tree) → leggere 500 punti → Project › Save (.itrcnpy) · Report › Print (PDF) · Export to CSV.',
  c6t:'formule reimplementate · ipotesi indicate',
  c6s:'CC = 0,6·ombra + 0,2·albedo + 0,2·ETI; HM = il maggiore tra CC e la media pesata e^(−d/d_cool) entro l’influenza di un grande verde (> 2ha entro 450m).',
  calcSum:'Calcolatore delle formule (un pixel)', lblSh:'Quota d’ombra', lblAl:'Albedo', lblDist:'Distanza da un’area verde ≥ 2ha (m)', kCoolL:'Raffrescamento (°C)',
  ccsTitle:'④ Prima tabella dei risultati CCS', ccsT:'indicatore · valore · errore · risoluzione · fonte/data · consultazione',
  ccsS:'Solo le righe con tutte e 6 le colonne compilate passano alla matrice di confronto. Le celle vuote restano vuote con il motivo (una riga con valori inventati vale 0 in integrità).',
  ccsN:'Alternativa A stato attuale · B filari alberati (2 file lungo le arterie, chioma 8m) · C alberi + pavimentazione permeabile (30% delle strade di raccolta). NDVI e LST restano quelli della stessa scena: un progetto non si misura dal satellite.',
  mxTitle:'Modulo di confronto delle alternative', mxH:'6 righe × riferimento · alternative A · B · C', mxT:'scala a 5 punti × pesi · Hill tipo II',
  mxS:'Valore → punteggio 1–5 → × peso (somma 1,00) → totale. Se la differenza è entro l’errore, stesso punteggio del riferimento. Pesi e soglie fissati prima di compilare le alternative (da approvare in squadra).',
  revH:'Punti di inversione dei pesi',
  sigH:'Significatività', sigT:'domanda per la prossima lezione',
  sigS:'Con 500 punti, una differenza di chioma di 3 punti % tra due alternative è significativa? — regola: differenza ≥ 2 × SE → «significativa», altrimenti «nessuna differenza».',
  lblP1:'Chioma alternativa 1 (%)', lblP2:'Chioma alternativa 2 (%)',
  aeTitle:'⑤ Vista aerea', aeH:'Frase decisionale dell’alternativa C → prompt', aeT:'1 scena luminosa diurna',
  aeS:'Inserire solo impianti, tratti e quantità; nella didascalia indicare che numero di alberi e superfici nell’immagine non sono valori. Rigenerare le scene scure.',
  lblDecision:'Frase decisionale', lblPrompt:'Prompt (inglese — per lo strumento di immagini)', lblCaption:'Didascalia',
  btnCpP:'Copia prompt', btnCpC:'Copia didascalia', aePrevH:'Anteprima immagine',
  aePrevS:'Scegliere l’immagine generata per vederla con la didascalia (non viene caricata da nessuna parte).',
  toolsTitle:'Quattro strumenti · esportazione',
  c7h:'Tabella di confronto dei quattro strumenti', c7t:'Valori confrontabili solo in un’unica tabella',
  thTool:'Strumento', thOut:'Prodotto', thRes:'Risoluzione · frequenza', thAcc:'Accesso · limiti', thErr:'Fonti d’errore · stato', thVal:'Valore in questo cruscotto',
  r1a:'NDVI · riflettanza a 13 bande', r1b:'10m · 5 giorni · larghezza 290km', r1c:'Account CDSE gratuito (10.000 PU/mese)', r1d:'Data di acquisizione · nuvole · dimensione pixel',
  r2a:'Temperatura superficiale ST (K→°C) · riflettanza', r2b:'30m · 16 giorni · lanciato nel 2021', r2d:'Ora di acquisizione · stagione · nuvole',
  r3a:'Copertura % ± SE · superficie · benefici', r3b:'Punti casuali (esempio 500)', r3c:'Strumento web · .itrcnpy · PDF · CSV', r3d:'Dimensione del campione · operatore · finanziamento',
  r4b:'Risoluzione del raster di input · 3.20.2', r4c:'LULC · ET0 · tabella biofisica · AOI', r4d:'Pesi · d_cool 450m ipotizzato',
  c7src:'SentiWiki · CDSE Quotas FAQ · USGS Landsat C2 L2 · i-Tree Funding Status · InVEST User Guide · GitHub releases — tutti consultati il 2026-09-09 · account e chiavi a cura di ogni studente',
  c8h:'Esportazione', c8s:'Genera i CSV con il sito attuale e i valori i-Tree inseriti. xlsx e PDF da consegnare si generano con gli script in code/.',
  btnExCcs:'CSV tabella CCS', btnExCat:'CSV catalogo indicatore ⑦', btnExMx:'CSV confronto alternative', btnExRoad:'CSV indice stradale', btnReset:'Azzera gli inserimenti',
  foot:'Dongtan sito A · Campus di Cheonan, Sangmyung University · Sentinel-2 L2A · Landsat 9 C2 L2 · i-Tree · InVEST · OpenStreetMap'
};
const KO = {};
document.querySelectorAll('[data-i]').forEach(el => KO[el.dataset.i] = el.innerHTML);
document.querySelectorAll('[data-ip]').forEach(el => KO[el.dataset.ip] = el.placeholder);
let lang = store.get('lang', 'ko');
const tr = (ko, it) => lang === 'it' ? it : ko;
const TERM = {'캐노피 피복률':'Copertura arborea','NDVI 평균':'NDVI medio','지표온도':'Temperatura superficiale','가중 유출계수':'Coefficiente di deflusso pesato',
  '냉각 지수 HM':'Indice di raffrescamento HM','캐노피 피복률(%)':'Copertura arborea (%)','지표온도(℃)':'Temperatura superficiale (℃)',
  '조성비(백만원/ha)':'Costo di realizzazione (M₩/ha)','유지관리비(백만원/ha·년)':'Manutenzione (M₩/ha·anno)',
  '주거':'Residenziale','상업·업무':'Commerciale','공업':'Industriale','공원·녹지':'Parchi e verde','대상지 전체':'Intero sito',
  '주간선':'Arteria principale','보조간선':'Arteria secondaria','집산':'Strada di raccolta','충족':'rispettato','미달':'sotto','초과':'sopra',
  '기준 없음(통과 구간)':'nessuno standard (attraversamento)','참고':'riferimento'};
const T = s => lang === 'it' && TERM[s] ? TERM[s] : s;
// 데이터 문자열(파이썬 산출)의 자주 쓰는 구절 — 이탈리아어 보기에서만 치환
const PHR = [
  ['빈칸 사유: i-Tree 500점 판독 대기(학생 판독 후 입력)','Cella vuota: lettura i-Tree di 500 punti in attesa'],
  ['Planetary Computer 공개 미러(CDSE 대체)','mirror pubblico Planetary Computer (al posto di CDSE)'],
  ['Planetary Computer 공개 미러(USGS 대체)','mirror pubblico Planetary Computer (al posto di USGS)'],
  ['natcap.invest 미실행(Python 3.14 휠 없음)','natcap.invest non eseguito (nessuna build per Python 3.14)'],
  ['InVEST 3.20.2 User Guide 식 파이썬 재구현','formule della User Guide InVEST 3.20.2 reimplementate in Python'],
  ['생물물리 값 가정','valori biofisici ipotizzati'],['그늘 가중치','peso ombra'],['취득 시각 1회분','un solo passaggio'],
  ['화소 표준편차','dev. std. dei pixel'],['경계 안 구름','nuvole nel confine'],['동일 장면','stessa scena'],['판독일 기입','data di lettura'],
  ['500점 판독','lettura di 500 punti'],['10m 화소','pixel 10m'],['30m 격자','griglia 30m'],['용도별 면적','superficie per uso'],
  ['투수포장','pav. permeabile'],['가로수 수관','chioma dei filari'],['판독값 p','valore letto p'],['대안 C','alternativa C'],
  ['대로 1류','viale cl. 1'],['대로 3류','viale cl. 3'],['중로 1류','strada media cl. 1'],['차로','corsie'],
  ['LST ≠ 기온','LST ≠ temperatura dell’aria'],['장면','scena'],['취득','acquisizione'],['가정','ipotesi'],['판독','lettura']
];
const TT = s => { if (lang !== 'it' || s == null) return s; let t = String(s); for (const [k,v] of PHR) t = t.split(k).join(v); return t; };
function applyLang(){
  const d = lang === 'it' ? IT : KO;
  document.querySelectorAll('[data-i]').forEach(el => { const v = d[el.dataset.i]; if (v != null) el.innerHTML = v; });
  document.querySelectorAll('[data-ip]').forEach(el => { const v = d[el.dataset.ip]; if (v != null) el.placeholder = v; });
  document.documentElement.lang = lang;
  document.title = tr('위성 녹지 판독 대시보드', 'Cruscotto del verde da satellite');
  $('langBtn').textContent = tr('🇮🇹 Italiano', '🇰🇷 한국어');
}
$('langBtn').onclick = () => { lang = lang === 'it' ? 'ko' : 'it'; store.set('lang', lang); applyLang(); renderAll(); };

/* ---------- 대상지 ---------- */
let site = store.get('site', 'dongtan');
if (!D.sites[site]) site = 'dongtan';
const S = () => D.sites[site];
const siteName = () => tr(S().name, S().name_it);
document.querySelectorAll('[data-site]').forEach(b => b.onclick = () => {
  site = b.dataset.site; store.set('site', site); lastPts = null; renderAll(); fitMaps();
});

function b64u8(s){ const b = atob(s), a = new Uint8Array(b.length); for (let i=0;i<b.length;i++) a[i] = b.charCodeAt(i); return a; }
function b64u16(s){ const u = b64u8(s); return new Uint16Array(u.buffer, u.byteOffset, u.length/2); }
const cache = {};
function G(){
  if (cache[site]) return cache[site];
  const sat = S().sat, g = sat.grid10, g3 = sat.grid30;
  const q = b64u8(g.ndvi_b64), ins = b64u8(g.inside_b64);
  const ndvi = new Float32Array(q.length);
  for (let i=0;i<q.length;i++) ndvi[i] = q[i] === 255 ? NaN : q[i]/100 - 1;
  const nat = b64u8(sat.ndvi_native_b64), native = new Float32Array(nat.length);
  for (let i=0;i<nat.length;i++) native[i] = nat[i]/100 - 1;
  const ql = b64u16(g3.lst_b64), lst = new Float32Array(ql.length);
  for (let i=0;i<ql.length;i++) lst[i] = ql[i] === 65535 ? NaN : ql[i]/100;
  return cache[site] = {g, ndvi, inside: ins, native, g3, lst, inside3: b64u8(g3.inside_b64)};
}
function inBoundary(lat, lng){
  let c = false;
  for (const ring of S().boundary){
    let r = false;
    for (let i=0, j=ring.length-1; i<ring.length; j=i++){
      const [yi,xi] = ring[i], [yj,xj] = ring[j];
      if ((yi>lat) !== (yj>lat) && lng < (xj-xi)*(lat-yi)/(yj-yi)+xi) r = !r;
    }
    if (r) c = !c;
  }
  return c;
}

/* ---------- i-Tree 입력 ---------- */
let itree = store.get('itree', {});
function itreeVal(){
  const v = itree[site];
  if (v && v.n > 0 && v.tree != null && v.tree !== '' && !isNaN(v.tree)){
    const n = +v.n, k = Math.min(+v.tree, n), p = k/n;
    return {n, k, p, se: Math.sqrt(p*(1-p)/n), date: v.date || '', src: 'itree'};
  }
  const a = S().ai_canopy;     // i-Tree 입력이 없으면 AI 대체 판독(공개 표기)
  if (a){ const p = a.tree/a.n; return {n: a.n, k: a.tree, p, se: Math.sqrt(p*(1-p)/a.n), date: a.read_on, src: 'ai'}; }
  return null;
}
function loadItreeInputs(){
  const v = itree[site] || {};
  $('nPts').value = v.n || 500; $('nTree').value = v.tree ?? ''; $('itDate').value = v.date || '';
}
['nPts','nTree','itDate'].forEach(id => $(id).oninput = () => {
  itree[site] = {n: +$('nPts').value || 500, tree: $('nTree').value === '' ? null : +$('nTree').value, date: $('itDate').value};
  store.set('itree', itree); renderItree(); renderCCS(); renderMatrix(); renderTasks(); renderTools();
});

/* ---------- 색상 ---------- */
const stops = [[-1,[120,90,70]],[0,[200,190,160]],[0.2,[235,225,150]],[0.4,[150,200,100]],[0.6,[60,150,70]],[1,[10,80,40]]];
function ramp(v){
  for (let k=1; k<stops.length; k++) if (v <= stops[k][0]){
    const [a,ca] = stops[k-1], [b,cb] = stops[k], t = (v-a)/(b-a);
    return ca.map((c,i) => Math.round(c + (cb[i]-c)*t));
  }
  return stops[stops.length-1][1];
}
$('ramp').style.background = `linear-gradient(90deg,${[-1,-0.5,0,0.2,0.4,0.6,1].map(v=>`rgb(${ramp(v)})`).join(',')})`;
const LUC = {'공원·녹지':'#5f9e57','공업':'#9b7aa0','상업·업무':'#e0603a','주거':'#f2cf5b'};
const TIERC = {'주간선':['#ff3d2e',6],'보조간선':['#5b6cff',4],'집산':['#f4f4f6',2]};

/* ---------- 히어로 · 과제 점검 ---------- */
function renderHero(){
  const s = S(), sat = s.sat;
  document.querySelectorAll('[data-site]').forEach(b => b.classList.toggle('on', b.dataset.site === site));
  $('hTitle').textContent = siteName() + tr(' — 7주차 과제 대시보드', ' — cruscotto della settimana 7');
  $('hArea').textContent = s.area_ha.toFixed(1) + ' ha';
  $('hNdvi').textContent = fmt(sat.ndvi.mean, 2);
  $('hLst').textContent = fmt(sat.lst.mean, 1) + '°C';
  $('hScene').textContent = `S2 ${sat.s2.date} · L9 ${sat.l9.date} · ${tr('경계 안 구름','nuvole nel confine')} ${sat.s2.local_cloud}% / ${sat.l9.local_cloud}%`;
}
function renderTasks(){
  const s = S(), it = itreeVal(), rd = D.sites.dongtan.roads;
  const filled = 4 + (it ? 1 : 0);
  const res = rd.table.find(r => r['용도지역'] === '주거'), com = rd.table.find(r => r['용도지역'] === '상업·업무'), ind = rd.table.find(r => r['용도지역'] === '공업');
  const cards = [
    {n:'①', t:tr('도로 위계 · 도로율','Gerarchia · indice stradale'), st:'done',
     d:tr(`대안 C에 주간선·보조간선·집산 배치. 도로율 주거 ${res['도로율(%)']}% · 상업 ${com['도로율(%)']}% · 공업 ${ind['도로율(%)']}% — 제11조 기준 ${rd.compliance}/6 충족`,
          `Arterie a 3 livelli sull’alternativa C. Indice: residenziale ${res['도로율(%)']}% · commerciale ${com['도로율(%)']}% · industriale ${ind['도로율(%)']}% — ${rd.compliance}/6 standard rispettati`), href:'#roads'},
    {n:'②', t:tr('i-Tree 500점 판독','Lettura i-Tree 500 punti'), st: it ? (it.src === 'ai' ? 'wait' : 'done') : 'todo',
     d: it && it.src === 'ai' ? tr(`AI 대체 판독(i-Tree 아님): ${(100*it.p).toFixed(1)} ± ${(100*it.se).toFixed(2)}% (N=${it.n}). .itrcnpy 원본 없음.`, `Lettura sostitutiva IA (non i-Tree): ${(100*it.p).toFixed(1)} ± ${(100*it.se).toFixed(2)}%. Nessun .itrcnpy.`)
      : it ? tr(`입력됨: ${(100*it.p).toFixed(1)} ± ${(100*it.se).toFixed(2)}% (N=${it.n}). .itrcnpy·PDF·CSV를 제출 폴더에 넣으세요.`, `Inserito: ${(100*it.p).toFixed(1)} ± ${(100*it.se).toFixed(2)}% (N=${it.n}). Mettere .itrcnpy·PDF·CSV nella cartella di consegna.`)
           : tr('직접 판독 필요 — 경계 shapefile 업로드 → 500점 → .itrcnpy·PDF·CSV 저장 후 결과 입력', 'Lettura da fare — caricare lo shapefile → 500 punti → salvare .itrcnpy·PDF·CSV e inserire il risultato'), href:'#itree'},
    {n:'③', t:tr('지표 ⑦ 카탈로그','Catalogo indicatore ⑦'), st: it ? 'done' : 'wait',
     d:tr(`NDVI ${fmt(s.sat.ndvi.mean,3)} · LST ${fmt(s.sat.lst.mean,1)}℃ 실측 저장. 캐노피 ${it ? '입력됨' : '판독 대기'}.`, `NDVI ${fmt(s.sat.ndvi.mean,3)} · LST ${fmt(s.sat.lst.mean,1)}℃ misurati. Chioma ${it ? 'inserita' : 'in attesa'}.`), href:'#dash'},
    {n:'④', t:tr('CCS 1차 결과표 · 대안 비교','Tabella CCS · confronto'), st: it ? 'done' : 'wait',
     d:tr(`5개 지표 중 ${filled}개 행 완성, 대안 A·B·C 비교 ${it ? '확정' : '잠정(캐노피 제외)'}.`, `${filled} righe su 5 complete, confronto A·B·C ${it ? 'definitivo' : 'provvisorio (senza chioma)'}.`), href:'#ccs'},
    {n:'⑤', t:tr('조감 이미지','Vista aerea'), st:'wait',
     d:tr('프롬프트·캡션 준비됨 — 이미지 도구로 밝은 장면 1장 생성 필요', 'Prompt e didascalia pronti — generare 1 immagine luminosa'), href:'#aerial'}
  ];
  const lab = {done:tr('완료','Fatto'), wait:tr('진행 중','In corso'), todo:tr('직접 할 일','Da fare')};
  $('taskCards').innerHTML = cards.map(c => `<a class="step task ${c.st}" href="${c.href}"><span class="n">${c.n}</span><b>${c.t}</b>
    <span class="badge ${c.st === 'done' ? 'done' : c.st}">${lab[c.st]}</span><div class="st">${c.d}</div></a>`).join('');
}

/* ---------- 지도 공통 ---------- */
let satMap = null, roadMap = null, ndviLayer, bLayer, ptsLayer, rLayers, layerCtl;
const esri = () => window.L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
  {maxZoom: 19, attribution: 'Imagery &copy; Esri, Maxar, Earthstar Geographics'});
const gridBounds = g => [[g.north - g.h*g.dlat, g.west], [g.north, g.west + g.w*g.dlng]];
function boundaryLL(){ return S().boundary; }
function fitMaps(){
  const b = gridBounds(G().g);
  if (satMap && !$('satBox').hidden){ satMap.invalidateSize(); satMap.fitBounds(b); }
  if (roadMap){ roadMap.invalidateSize(); roadMap.fitBounds(b); }
}

/* ---------- ① 도로 위계 ---------- */
function renderRoads(){
  const rd = D.sites.dongtan.roads;
  $('roadSub').innerHTML = site === 'dongtan'
    ? tr(`배치간격 규칙을 고정하고 격자 원점만 탐색: 개발 셀 125m 접근 최대 → 제11조 충족 최대 → 도로 면적 최소. 주간선 ${(rd.lengths_m['주간선']/1000).toFixed(2)}km · 보조간선 ${(rd.lengths_m['보조간선']/1000).toFixed(2)}km · 집산 ${(rd.lengths_m['집산']/1000).toFixed(2)}km.`,
         `Interassi fissi, si cerca solo l’origine della griglia: massimo accesso entro 125m → massimo rispetto dell’art. 11 → minima superficie stradale. Principale ${(rd.lengths_m['주간선']/1000).toFixed(2)}km · secondaria ${(rd.lengths_m['보조간선']/1000).toFixed(2)}km · raccolta ${(rd.lengths_m['집산']/1000).toFixed(2)}km.`)
    : tr('과제 ①은 6주차 대안 1안(동탄 후보지 A)이 대상입니다. 천안캠퍼스에서는 대안 B·C의 가로수·투수포장 구간인 OSM 캠퍼스 도로를 보여 줍니다.',
         'Il compito ① riguarda il piano 1 della settimana 6 (Dongtan A). Per il campus si mostrano le strade OSM usate per alberi e pavimentazione permeabile (alternative B·C).');
  // 횡단 표
  const tiers = ['주간선','보조간선','집산'], cr = rd.cross;
  const rowsC = [['규모','Classe'],['폭','Larghezza (m)'],['차로','Corsie'],['중앙분리대','Spartitraffico'],['정차대','Sosta'],['자전거도로','Ciclabile'],['보도','Marciapiede'],['설계속도','Velocità di progetto']];
  $('crossTbl').innerHTML = `<thead><tr><th></th>${tiers.map(t=>`<th>${T(t)}</th>`).join('')}</tr></thead><tbody>` +
    rowsC.map(([k,ki]) => `<tr><td>${tr(k,ki)}</td>${tiers.map(t=>`<td>${TT(cr[t][k])}${k==='폭'?' m':''}</td>`).join('')}</tr>`).join('') + '</tbody>';
  $('kAccess').textContent = (100*rd.access_125m).toFixed(0) + '%';
  $('kComply').textContent = rd.compliance + ' / 6';
  // 도로율 표
  const pill = j => `<span class="pill ${j==='충족'?'ok':(j==='미달'||j==='초과')?'bad':''}">${T(j)}</span>`;
  $('ratioTbl').innerHTML = `<thead><tr><th>${tr('용도지역','Zona')}</th><th>${tr('면적','Superficie')} (ha)</th><th>${T('주간선')} (ha)</th><th>${T('보조간선')} (ha)</th><th>${T('집산')} (ha)</th>
    <th>${tr('도로율','Indice stradale')} (%)</th><th>${tr('기준','Standard')}</th><th>${tr('판정','Esito')}</th><th>${tr('간선도로율','Indice arterie')} (%)</th><th>${tr('기준','Standard')}</th><th>${tr('판정','Esito')}</th></tr></thead><tbody>` +
    rd.table.map(r => `<tr><td><b>${T(r['용도지역'])}</b></td><td>${r['면적(ha)']}</td><td>${r['주간선(ha)']}</td><td>${r['보조간선(ha)']}</td><td>${r['집산(ha)']}</td>
      <td><b>${r['도로율(%)']}</b></td><td>${r['기준 도로율(%)']}</td><td>${r['도로율 판정']==='—'?'—':pill(r['도로율 판정'])}</td>
      <td><b>${r['간선도로율(%)']}</b></td><td>${r['기준 간선도로율(%)']}</td><td>${r['간선 판정']==='—'?'—':pill(r['간선 판정'])}</td></tr>`).join('') + '</tbody>';
  // 지도
  if (!window.L){ $('roadMap').textContent = tr('지도 라이브러리를 불러오지 못했습니다.','Libreria della mappa non caricata.'); return; }
  if (!roadMap){
    roadMap = window.L.map('roadMap', {scrollWheelZoom:false});
    esri().addTo(roadMap);
    rLayers = window.L.layerGroup().addTo(roadMap);
  }
  rLayers.clearLayers();
  window.L.polygon(boundaryLL(), {color:'#ff3d2e', weight:2, fill:false, dashArray:'6 4'}).addTo(rLayers);
  if (site === 'dongtan'){
    window.L.geoJSON(rd.landuse, {style: f => ({color: LUC[f.properties.lu], weight: 0, fillColor: LUC[f.properties.lu], fillOpacity: .5})}).addTo(rLayers);
    window.L.geoJSON({type:'FeatureCollection', features: rd.geo.features.filter(f => f.properties.kind !== 'area')},
      {style: f => ({color: TIERC[f.properties.tier][0], weight: TIERC[f.properties.tier][1], opacity: .95})}).addTo(rLayers);
    $('roadLegend').innerHTML = Object.entries(LUC).map(([k,c]) => `<span class="sw" style="background:${c}"></span>${T(k)}`).join(' ') + ' &nbsp; ' +
      Object.entries(TIERC).map(([k,[c,w]]) => `<span class="ln" style="background:${c};height:${w}px"></span>${T(k)} ${rd.cross[k]['폭']}m`).join(' ');
  } else {
    window.L.geoJSON(S().campus_roads, {style: {color:'#ff9a6a', weight: 4}}).addTo(rLayers);
    $('roadLegend').innerHTML = `<span class="ln" style="background:#ff9a6a;height:4px"></span>${tr('OSM 캠퍼스 도로(대안 B·C 시설 구간)','Strade OSM del campus (tratti delle alternative B·C)')}`;
  }
}

/* ---------- ① 계정과 한도 ---------- */
const PU_MONTH = 10000, PU_MIN = 300, CR_MONTH = 10000;
let quotas = store.get('quotas', [{name:'학생 A', pu:3200, cr:1500},{name:'학생 B', pu:8700, cr:400}]);
function renderQuota(){
  const tb = $('quotaTbl').querySelector('tbody'); tb.innerHTML = '';
  quotas.forEach((q, i) => {
    const pp = Math.min(100, q.pu/PU_MONTH*100), cp = Math.min(100, q.cr/CR_MONTH*100);
    const row = document.createElement('tr');
    row.innerHTML = `<td>${esc(q.name)}</td>
      <td>${q.pu.toLocaleString()} / 10,000<div class="bar"><i class="${pp>80?'hot':''}" style="width:${pp}%"></i></div></td>
      <td>${q.cr.toLocaleString()} / 10,000<div class="bar"><i class="${cp>80?'hot':''}" style="width:${cp}%"></i></div></td>
      <td><button class="ghost" data-k="${i}" style="padding:2px 10px">${tr('삭제','Elimina')}</button></td>`;
    tb.appendChild(row);
  });
  tb.querySelectorAll('button').forEach(b => b.onclick = () => { quotas.splice(+b.dataset.k,1); store.set('quotas',quotas); renderQuota(); });
  const per = (+$('reqPU').value||0) * (+$('reqPerMin').value||0);
  $('rateMsg').innerHTML = per > PU_MIN
    ? `<span style="color:var(--accent)">${tr(`분당 ${per} PU — 분당 300 PU 한도 초과. 요청 간격을 늘리세요.`, `${per} PU/min — oltre il limite di 300 PU/min.`)}</span>`
    : tr(`분당 ${per} PU — 분당 300 PU 한도 이내.`, `${per} PU/min — entro il limite di 300 PU/min.`);
  setBadge('b1', quotas.length > 0);
}
$('qAdd').onclick = () => {
  const name = $('qName').value.trim(); if (!name) return;
  quotas.push({name, pu:+$('qPU').value||0, cr:+$('qCR').value||0});
  store.set('quotas', quotas); $('qName').value=$('qPU').value=$('qCR').value=''; renderQuota();
};
$('reqPU').oninput = $('reqPerMin').oninput = renderQuota;
function setBadge(id, ok){ const b = $(id); b.textContent = ok ? tr('완료','Fatto') : tr('대기','In attesa'); b.classList.toggle('done', ok); }

/* ---------- ② 장면 선택 ---------- */
function renderScenes(){
  const sat = S().sat, cc = +$('cc').value, from = $('dFrom').value, to = $('dTo').value;
  $('ccV').textContent = cc;
  const ok = x => x.local_cloud <= cc && (!from || x.date >= from) && (!to || x.date <= to);
  $('sceneTbl').innerHTML = `<thead><tr><th></th><th>Sentinel-2 L2A ${tr('장면 ID','ID scena')}</th><th>${tr('취득일','Data')}</th><th>${tr('장면 구름','Nuvole scena')}</th><th>${tr('경계 안 구름','Nuvole nel confine')}</th></tr></thead><tbody>` +
    sat.s2_candidates.map(x => `<tr class="${ok(x)?'':'off'} ${x.id===sat.s2.id?'sel':''}"><td>${x.id===sat.s2.id?'✓':''}</td><td class="mono">${x.id}</td><td>${x.date}</td><td>${x.scene_cloud.toFixed(1)}%</td><td><b>${x.local_cloud.toFixed(1)}%</b></td></tr>`).join('') + '</tbody>';
  $('l9Tbl').innerHTML = `<thead><tr><th></th><th>Landsat 9 C2 L2 ${tr('장면 ID','ID scena')}</th><th>${tr('취득일','Data')}</th><th>${tr('장면 구름','Nuvole scena')}</th><th>${tr('경계 안 구름','Nuvole nel confine')}</th></tr></thead><tbody>` +
    sat.l9_candidates.map(x => `<tr class="${ok(x)?'':'off'} ${x.id===sat.l9.id?'sel':''}"><td>${x.id===sat.l9.id?'✓':''}</td><td class="mono">${x.id}</td><td>${x.date}</td><td>${x.scene_cloud.toFixed(1)}%</td><td><b>${x.local_cloud.toFixed(1)}%</b></td></tr>`).join('') + '</tbody>';
  setBadge('b2', true); setBadge('b3', true);
}
$('cc').oninput = $('dFrom').onchange = $('dTo').onchange = renderScenes;

/* ---------- ③④ NDVI ---------- */
let lastPts = null;
function gridCanvas(alphaOut){
  const {g, ndvi, inside} = G();
  const c = document.createElement('canvas'); c.width = g.w; c.height = g.h;
  const x = c.getContext('2d'), img = x.createImageData(g.w, g.h);
  for (let i=0;i<g.w*g.h;i++){
    if (isNaN(ndvi[i])){ img.data.set([0,0,0,0], i*4); continue; }
    const [r,gg,b] = ramp(ndvi[i]);
    img.data.set([r,gg,b, inside[i] ? 255 : alphaOut], i*4);
  }
  x.putImageData(img, 0, 0);
  return c;
}
function renderNdvi(){
  const sat = S().sat, {g, native} = G(), th = +$('th').value;
  $('thV').textContent = th.toFixed(2);
  $('ndviTag').textContent = `S2 L2A · ${sat.s2.date}`;
  $('legGrid').textContent = tr(`격자 10m · ${g.w}×${g.h} 화소(지도 정렬)`, `griglia 10m · ${g.w}×${g.h} pixel (allineata alla mappa)`);
  const cv = $('ndviMap'), W = 360, H = Math.round(360*g.h/g.w);
  cv.width = W; cv.height = H;
  const x = cv.getContext('2d'); x.imageSmoothingEnabled = false;
  x.fillStyle = '#0b0b0f'; x.fillRect(0,0,W,H);
  x.drawImage(gridCanvas(90), 0, 0, W, H);
  const sx = W/g.w, sy = H/g.h, px = (lat,lng) => [(lng - g.west)/g.dlng*sx, (g.north - lat)/g.dlat*sy];
  x.lineWidth = 2; x.strokeStyle = '#ff3d2e';
  for (const ring of boundaryLL()){ x.beginPath(); ring.forEach(([la,ln],k) => { const [a,b] = px(la,ln); k ? x.lineTo(a,b) : x.moveTo(a,b); }); x.closePath(); x.stroke(); }
  x.fillStyle = '#fff'; x.font = 'bold 12px sans-serif'; x.fillText('N ↑', 8, 18);
  if (lastPts) lastPts.forEach(p => { const [a,b] = px(p.lat,p.lng); x.beginPath(); x.arc(a,b,2.2,0,7); x.fillStyle = p.tree ? '#3ecf8e' : '#fff'; x.fill(); });
  // 통계(원 격자)
  const st = sat.ndvi, green = native.filter(v => v >= th).length / native.length;
  $('kMean').textContent = fmt(st.mean,3); $('kSd').textContent = fmt(st.sd,3);
  $('kGreen').textContent = (100*green).toFixed(1)+'%'; $('kN').textContent = st.n.toLocaleString();
  // 히스토그램
  const h = $('hist'), hg = h.getContext('2d'); hg.clearRect(0,0,h.width,h.height);
  const bins = new Array(24).fill(0); native.forEach(v => { bins[Math.max(0, Math.min(23, Math.floor((v+0.2)/0.05)))]++; });
  const mx = Math.max(...bins), HW = h.width, HH = h.height-18, bw = HW/24;
  hg.fillStyle = '#ff7a45';
  bins.forEach((c,k) => { const bh = c/mx*(HH-6); hg.fillRect(k*bw+1, HH-bh, bw-2, bh); });
  hg.fillStyle = css('--ink2'); hg.font = '10px sans-serif';
  [-0.2,0,0.2,0.4,0.6,0.8,1.0].forEach(v => hg.fillText(v.toFixed(1), Math.min(HW-14,(v+0.2)/0.05*bw-6), HH+13));
  const tx = (th+0.2)/0.05*bw; hg.strokeStyle = '#7b86ff'; hg.lineWidth = 2; hg.beginPath(); hg.moveTo(tx,0); hg.lineTo(tx,HH); hg.stroke();
  setBadge('b4', true);
  renderSat();
}
function renderSat(){
  if (!satMap) return;
  const g = G().g;
  ndviLayer.setUrl(gridCanvas(70).toDataURL()); ndviLayer.setBounds(window.L.latLngBounds(gridBounds(g)));
  bLayer.setLatLngs(boundaryLL());
  ptsLayer.clearLayers();
  (lastPts || []).forEach(p => window.L.circleMarker([p.lat,p.lng], {radius:3, weight:1, color:'#111', fillColor: p.tree ? '#3ecf8e' : '#fff', fillOpacity:1}).addTo(ptsLayer));
}
function setView(sat){
  $('vSat').classList.toggle('on', sat); $('vGrid').classList.toggle('on', !sat);
  $('ndviMap').hidden = sat; $('satBox').hidden = !sat;
  store.set('view', sat ? 'sat' : 'grid');
  if (!sat) return;
  if (!window.L){ $('satMap').textContent = tr('지도 라이브러리를 불러오지 못했습니다.','Libreria della mappa non caricata.'); return; }
  if (!satMap){
    satMap = window.L.map('satMap', {scrollWheelZoom:false});
    esri().addTo(satMap);
    ndviLayer = window.L.imageOverlay(gridCanvas(70).toDataURL(), gridBounds(G().g), {opacity: +$('op').value/100}).addTo(satMap);
    bLayer = window.L.polygon(boundaryLL(), {color:'#ff3d2e', weight:3, fill:false}).addTo(satMap);
    ptsLayer = window.L.layerGroup().addTo(satMap);
  }
  renderSat();
  setTimeout(() => { satMap.invalidateSize(); satMap.fitBounds(gridBounds(G().g)); }, 0);
}
$('vGrid').onclick = () => setView(false);
$('vSat').onclick = () => setView(true);
$('op').oninput = () => { $('opV').textContent = $('op').value; if (ndviLayer) ndviLayer.setOpacity(+$('op').value/100); };
$('th').oninput = () => { renderNdvi(); renderPixel(); };
function renderPixel(){
  const b4 = +$('pB4').value, b8 = +$('pB8').value, n = (b8-b4)/(b8+b4), th = +$('th').value;
  const cls = n>=th ? `<b style="color:var(--ok)">${tr('녹지','verde')}</b>` : n<0 ? tr('수면 등(음수)','acqua o simili (negativo)') : tr('건물·도로 등 비녹지','non verde (edifici, strade)');
  $('pOut').innerHTML = Number.isFinite(n)
    ? `NDVI = (${b8} − ${b4}) / (${b8} + ${b4}) = <b>${n.toFixed(3)}</b> → ${cls}`
    : tr('반사도 합이 0이면 계산할 수 없습니다.', 'Impossibile calcolare se la somma è 0.');
}
$('pB4').oninput = $('pB8').oninput = renderPixel;

/* ---------- 지표온도 ---------- */
function renderLst(){
  const sat = S().sat;
  $('lstTag').textContent = `Landsat 9 · ${sat.l9.date} ${sat.l9.time_utc} UTC`;
  const dn = +$('dn').value, sc = dn*0.00341802, k = sc+149.0, c = k-273.15;
  $('pDN').textContent = dn.toLocaleString(); $('pSc').textContent = sc.toFixed(2);
  $('pK').textContent = k.toFixed(2); $('pC').textContent = c.toFixed(2);
  $('kLst').textContent = fmt(sat.lst.mean,1)+'°C'; $('kR').textContent = fmt(sat.ndvi_lst_r,2);
  $('lstCov').innerHTML = sat.lst.coverage < 0.99
    ? tr(`⚠ ST 산출 화소 ${sat.lst.n.toLocaleString()}/${sat.lst.n_total.toLocaleString()}(${(100*sat.lst.coverage).toFixed(0)}%)만 — 이 값은 경계 일부만 대표합니다. QA는 맑음이나 ST_B10 값이 없는 화소가 6~9월 모든 장면에서 나타남(원인 미확인).`,
         `⚠ Solo ${sat.lst.n.toLocaleString()}/${sat.lst.n_total.toLocaleString()} pixel ST (${(100*sat.lst.coverage).toFixed(0)}%): il valore rappresenta solo parte del confine.`)
    : tr(`ST 산출 화소 ${sat.lst.n}/${sat.lst.n_total}(100%)`, `Pixel ST ${sat.lst.n}/${sat.lst.n_total} (100%)`);
  const P = sat.ndvi_lst_pairs, cv = $('scatter'), x = cv.getContext('2d'), W = cv.width, H = cv.height, Lm = 34, B = 22;
  x.clearRect(0,0,W,H);
  const xs0 = Math.min(...P.map(p=>p[0]), 0), xs1 = Math.max(...P.map(p=>p[0]), 0.8);
  const ys0 = Math.floor(Math.min(...P.map(p=>p[1]))) - 1, ys1 = Math.ceil(Math.max(...P.map(p=>p[1]))) + 1;
  const xs = v => Lm + (v-xs0)/(xs1-xs0)*(W-Lm-8), ys = v => H-B - (v-ys0)/(ys1-ys0)*(H-B-16);
  x.strokeStyle = css('--line'); x.fillStyle = css('--ink2'); x.font = '10px sans-serif';
  const step = Math.max(1, Math.round((ys1-ys0)/5));
  for (let v = Math.ceil(ys0); v <= ys1; v += step){ x.beginPath(); x.moveTo(Lm,ys(v)); x.lineTo(W-8,ys(v)); x.stroke(); x.fillText(v+'°',4,ys(v)+3); }
  [0,0.2,0.4,0.6,0.8].filter(v => v>=xs0 && v<=xs1).forEach(v => x.fillText(v.toFixed(1), xs(v)-8, H-6));
  x.fillStyle = '#ff7a45'; x.globalAlpha = .75;
  P.forEach(p => { x.beginPath(); x.arc(xs(p[0]), ys(p[1]), 2.2, 0, 7); x.fill(); });
  x.globalAlpha = 1; x.fillStyle = css('--ink2');
  x.fillText(tr(`NDVI (x) · LST ℃ (y) · 30m 셀 ${P.length}개`, `NDVI (x) · LST ℃ (y) · ${P.length} celle 30m`), Lm+4, 11);
}
$('dn').oninput = renderLst;

/* ---------- i-Tree ---------- */
function renderItree(){
  const it = itreeVal(), A = S().area_ha, {native} = G();
  $('shpLink').href = `files/${site}_boundary.zip`;
  if (it){
    $('kCan').textContent = (100*it.p).toFixed(1)+'%'; $('kSE').textContent = '±'+(100*it.se).toFixed(2);
    $('kCanA').textContent = (A*it.p).toFixed(2)+' ±'+(A*it.se).toFixed(2);
  } else { $('kCan').textContent = $('kSE').textContent = $('kCanA').textContent = '–'; }
  $('kDiff').textContent = (100*native.filter(v => v >= 0.5).length/native.length).toFixed(1)+'%';
  $('simOut').innerHTML = it && it.src === 'ai'
    ? tr(`위 값은 <b>AI 대체 판독(i-Tree 아님)</b> — ${S().ai_canopy.method} · 판독자 ${S().ai_canopy.reader} · ${S().ai_canopy.imagery}. 위 칸에 i-Tree 판독값을 넣으면 그 값으로 바뀝니다.`,
         `Valori da <b>lettura sostitutiva IA (non i-Tree)</b>. Inserendo i valori i-Tree qui sopra, verranno usati quelli.`)
    : $('simOut').innerHTML;
}
$('simPts').onclick = () => {
  const {g, ndvi} = G(), n = 500, pts = [];
  const lat0 = g.north - g.h*g.dlat, lng0 = g.west;
  let tree = 0, guard = 0;
  while (pts.length < n && guard++ < n*200){
    const lat = lat0 + Math.random()*g.h*g.dlat, lng = lng0 + Math.random()*g.w*g.dlng;
    if (!inBoundary(lat, lng)) continue;
    const r = Math.floor((g.north-lat)/g.dlat), c = Math.floor((lng-g.west)/g.dlng), v = ndvi[r*g.w+c];
    if (isNaN(v)) continue;
    const t = v >= 0.5; pts.push({lat, lng, tree:t}); if (t) tree++;
  }
  lastPts = pts;
  const p = tree/pts.length, se = Math.sqrt(p*(1-p)/pts.length);
  $('simOut').innerHTML = tr(`연습 미리보기(제출값 아님): ${pts.length}점 중 ${tree}점 = ${(100*p).toFixed(1)} ± ${(100*se).toFixed(2)}%`,
                             `Anteprima (non da consegnare): ${tree} su ${pts.length} = ${(100*p).toFixed(1)} ± ${(100*se).toFixed(2)}%`);
  renderNdvi();
};

/* ---------- InVEST ---------- */
function renderHM(){
  const m = S().ccs.model, names = D.ccs.alts;
  $('hmTbl').innerHTML = `<thead><tr><th>${tr('대안','Alternativa')}</th><th>HM ${tr('평균','medio')}</th><th>${tr('그늘 가중치 0.6 ± 0.1','peso ombra 0,6 ± 0,1')}</th><th>${tr('기준선 대비','vs riferimento')}</th></tr></thead><tbody>` +
    ALT.map((k,i) => `<tr><td>${altName(i)}</td><td><b>${fmt(m.hm[k],3)}</b></td><td>${fmt(m.hm_range[k][0],3)}~${fmt(m.hm_range[k][1],3)}</td><td>${k==='A'?'—':(m.hm[k]-m.hm.A>=0?'+':'')+fmt(m.hm[k]-m.hm.A,3)}</td></tr>`).join('') + '</tbody>';
  $('hmNote').textContent = tr(`토지피복: ${m.lulc_basis}. 생물물리 값(그늘·Kc·알베도·녹지 여부)은 가정이며 ET0는 균일(ETI = Kc)로 두었습니다. natcap.invest는 이 PC의 Python 3.14용 배포판이 없어 User Guide 식을 파이썬으로 재구현했습니다.`,
    `Copertura: ${m.lulc_basis}. Valori biofisici ipotizzati, ET0 uniforme (ETI = Kc). natcap.invest non ha build per Python 3.14: formule della User Guide reimplementate in Python.`);
}
function renderCalc(){
  const sh=+$('sh').value, al=+$('al').value, et=+$('et').value;
  $('shV').textContent=sh.toFixed(2); $('alV').textContent=al.toFixed(2); $('etV').textContent=et.toFixed(2);
  const cc = 0.6*sh + 0.2*al + 0.2*et, d = +$('dist').value;
  const park = d <= 450 ? 0.8*Math.exp(-d/450) : 0, hm = Math.max(cc, park), tref = +$('tref').value, uhi = +$('uhi').value;
  $('kCC').textContent = cc.toFixed(2); $('kHM').textContent = hm.toFixed(2);
  $('kTair').textContent = (tref + (1-hm)*uhi).toFixed(2); $('kCool').textContent = '−'+(hm*uhi).toFixed(2);
}
['sh','al','et','tref','uhi','dist'].forEach(id => $(id).oninput = renderCalc);
const altName = i => tr(D.ccs.alts[i], ['Alternativa A · stato attuale','Alternativa B · filari alberati','Alternativa C · alberi + pavimentazione permeabile'][i]);

/* ---------- ④ CCS 결과표 ---------- */
function ccsRows(){
  const s = S(), it = itreeVal(), d = s.ccs.model.d_canopy;
  return s.ccs.ccs.map((r, i) => {
    const row = {...r, 대안: {...r.대안}};
    if (i === 0){
      if (it){
        const pB = Math.min(1, it.p + d), seB = Math.sqrt(pB*(1-pB)/it.n);
        const sig = Math.abs(pB-it.p) >= 2*Math.max(it.se, seB);
        row.값 = (100*it.p).toFixed(1)+'%';
        row['오차·가정 폭'] = `± ${(100*it.se).toFixed(2)}%p (SE, N = ${it.n})`;
        row['출처·취득일'] = it.src === 'ai'
          ? tr(`AI 대체 판독(i-Tree 아님) · ${S().ai_canopy.imagery} · 판독 ${it.date}`, `Lettura sostitutiva IA (non i-Tree) · Esri World Imagery · ${it.date}`)
          : `i-Tree Canopy · ${tr('판독','lettura')} ${it.date || tr('(판독일 기입)','(data)')}`;
        if (it.src === 'ai') row.해상도 = tr('무작위 500점(AI 판독)', '500 punti casuali (lettura IA)');
        row.조회일 = it.date || '';
        row.비고 = tr(`${it.k}/${it.n}점 수목`, `${it.k}/${it.n} punti albero`) + (it.src === 'ai' ? tr(' · i-Tree 원본(.itrcnpy) 없음 — 대체 판독', ' · nessun file .itrcnpy — lettura sostitutiva') : '');
        row.대안 = {A: `${(100*it.p).toFixed(1)} ± ${(100*it.se).toFixed(1)}`,
                    B: `${(100*pB).toFixed(1)} ± ${(100*seB).toFixed(1)} (${sig ? tr('유의','signif.') : tr('차이 없음','nessuna diff.')})`,
                    C: `${(100*pB).toFixed(1)} ± ${(100*seB).toFixed(1)} (${sig ? tr('유의','signif.') : tr('차이 없음','nessuna diff.')})`};
      } else {
        row.대안 = {A: tr('판독값 p','valore p'), B: `p + ${(100*d).toFixed(1)}%p`, C: `p + ${(100*d).toFixed(1)}%p`};
      }
    }
    return row;
  });
}
function renderCCS(){
  $('ccsH').textContent = siteName();
  const cols = ['지표','값','오차·가정 폭','해상도','출처·취득일','조회일'];
  const colsIt = ['Indicatore','Valore','Errore · ipotesi','Risoluzione','Fonte · data','Consultazione'];
  const rows = ccsRows();
  $('ccsTbl').innerHTML = `<thead><tr>${cols.map((c,i)=>`<th>${tr(c,colsIt[i])}</th>`).join('')}${ALT.map(k=>`<th class="alt">${tr('대안','Alt.')} ${k}</th>`).join('')}</tr></thead><tbody>` +
    rows.map(r => {
      const empty = r.값 == null;
      return `<tr class="${empty?'empty':''}"><td><b>${T(r.지표)}</b>${r.비고?`<div class="tiny">${esc(TT(r.비고))}</div>`:''}</td>
        <td class="num">${empty?`<span class="pill">${tr('빈칸','vuoto')}</span>`:esc(typeof r.값==='number'?(r.지표==='지표온도'?r.값.toFixed(1)+'℃':r.값):r.값)}</td>
        <td>${esc(TT(r['오차·가정 폭']))}</td><td>${esc(TT(r.해상도))}</td><td class="src2">${esc(TT(r['출처·취득일']))}</td><td>${esc(TT(r.조회일))}</td>
        ${ALT.map(k=>`<td class="alt">${esc(TT(r.대안[k]))}</td>`).join('')}</tr>`;
    }).join('') + '</tbody>';
}

/* ---------- 대안 비교 서식 ---------- */
function sc(name, v){
  const [d, cuts] = D.ccs.scale[name];
  if (v == null || !Number.isFinite(v)) return null;
  return 1 + cuts.filter(c => d === '↑' ? v >= c : v < c).length;
}
function computeMatrix(){
  const s = S(), it = itreeVal(), mr = s.ccs.matrix_rows, W = D.ccs.weights, d = s.ccs.model.d_canopy;
  const names = Object.keys(W), rows = [];
  for (const name of names){
    const r = {name, w: W[name], v: {}, s: {}, j: {}, unc: mr[name].unc, src: mr[name].src};
    if (name.startsWith('캐노피')){
      if (it){
        const pB = Math.min(1, it.p + d), seB = Math.sqrt(pB*(1-pB)/it.n);
        r.v = {기준선: 100*it.p, A: 100*it.p, B: 100*pB, C: 100*pB};
        const same = Math.abs(pB-it.p) < 2*Math.max(it.se, seB);
        r.s.기준선 = r.s.A = sc(name, 100*it.p);
        r.s.B = r.s.C = same ? r.s.A : sc(name, 100*pB);
        r.j = {B: same ? tr('차이 없음','nessuna diff.') : tr('유의','signif.'), C: same ? tr('차이 없음','nessuna diff.') : tr('유의','signif.')};
        r.unc = `± ${(100*it.se).toFixed(1)} / ${(100*seB).toFixed(1)}%p`;
      } else { r.pending = true; r.v = {기준선:null, A:null, B:null, C:null}; }
    } else {
      for (const k of ['기준선', ...ALT]){ r.v[k] = mr[name][k]; r.s[k] = sc(name, mr[name][k]); }
      if (name === '가중 유출계수'){
        const [lo, hi] = s.ccs.model.runoff_C_range, width = Math.abs(hi - lo), diff = Math.abs(r.v.C - r.v.기준선);
        if (diff < width){ r.s.C = r.s.기준선; r.j.C = tr('가정 의존','dipende da ipotesi'); }
        else r.j.C = tr('가정 폭 초과','oltre l’ipotesi');
      }
      if (name === 'NDVI 평균' || name.startsWith('지표온도')) r.j = {A: tr('동일 장면','stessa scena'), B: tr('동일 장면','stessa scena'), C: tr('동일 장면','stessa scena')};
    }
    rows.push(r);
  }
  const used = rows.filter(r => !r.pending), wsum = used.reduce((a,r) => a + r.w, 0);
  used.forEach(r => r.wn = r.w / wsum);
  const total = {}; for (const k of ALT) total[k] = used.reduce((a,r) => a + r.wn*r.s[k], 0);
  const rank = [...ALT].sort((a,b) => total[b] - total[a]);
  // 역전점
  const rev = used.map(r => {
    const top = rank[0], others = used.filter(o => o !== r);
    const T0 = k => others.reduce((a,o) => a + o.wn/(1-r.wn)*o.s[k], 0);
    let best = null;
    for (const k of ALT) if (k !== top){
      if (r.s[top] === r.s[k]) continue;          // 이 행 점수가 같으면 가중치를 바꿔도 순위가 뒤집히지 않음
      const a = T0(top) - T0(k), b = (r.s[top] - r.s[k]) - (T0(top) - T0(k));
      if (Math.abs(b) < 1e-12) continue;
      const t = -a/b;
      if (t >= 0 && t <= 1 && Math.abs(t - r.wn) > 1e-9 && (!best || Math.abs(t - r.wn) < Math.abs(best.t - r.wn))) best = {t, k};
    }
    return {name: r.name, w: r.wn, best};
  });
  return {rows, total, rank, rev, provisional: !it, wsum};
}
function renderMatrix(){
  const M = computeMatrix(), cols = ['기준선', ...ALT];
  const fv = (name, v) => v == null ? '–' : name.startsWith('NDVI') || name === '가중 유출계수' ? v.toFixed(3) : name.startsWith('조성') || name.startsWith('유지') ? v.toFixed(2) : v.toFixed(1);
  $('mxTbl').innerHTML = `<thead><tr><th>${tr('지표','Indicatore')}</th><th>${tr('가중치','Peso')}</th>${cols.map(c=>`<th>${c==='기준선'?tr('기준선','Riferimento'):tr('대안 ','Alt. ')+c}</th>`).join('')}<th>${tr('오차·출처','Errore · fonte')}</th></tr></thead><tbody>` +
    M.rows.map(r => `<tr class="${r.pending?'empty':''}"><td><b>${T(r.name)}</b> <span class="tiny">${D.ccs.scale[r.name][0]}</span></td><td>${r.pending?`<s>${r.w.toFixed(2)}</s>`:r.wn.toFixed(2)}</td>` +
      cols.map(c => r.pending ? `<td class="pend">${tr('판독 대기','in attesa')}</td>` :
        `<td><span class="sc s${r.s[c]}">${r.s[c]}</span> <span class="tiny">${fv(r.name, r.v[c])}</span>${r.j && r.j[c] ? `<div class="tiny j">${r.j[c]}</div>` : ''}</td>`).join('') +
      `<td class="tiny">${esc(TT(r.unc))} · ${esc(TT(r.src))}</td></tr>`).join('') +
    `<tr class="tot"><td><b>${tr('가중 합계','Totale pesato')}</b></td><td>1.00</td><td>—</td>${ALT.map(k=>`<td><b>${M.total[k].toFixed(2)}</b> <span class="pill ${M.rank[0]===k?'ok':''}">${M.rank.indexOf(k)+1}${tr('위','°')}</span></td>`).join('')}<td></td></tr></tbody>`;
  $('mxNote').innerHTML = (M.provisional
    ? tr(`<b>잠정 순위</b> — 캐노피 행이 i-Tree 판독 대기라 빠졌고, 나머지 가중치를 합 1.00으로 다시 나눴습니다. 판독값을 넣으면 확정됩니다.`, `<b>Classifica provvisoria</b> — la riga della chioma attende la lettura i-Tree; gli altri pesi sono stati riportati a somma 1,00.`)
    : tr('<b>순위 확정</b> — 6개 행이 모두 채워졌습니다.', '<b>Classifica definitiva</b> — tutte e 6 le righe sono compilate.')) +
    ' ' + tr(`1위 ${altName(ALT.indexOf(M.rank[0]))} (${M.total[M.rank[0]].toFixed(2)}). 조성비·유지관리비는 가정 단가 × 물량이며 단가 출처 확인이 필요합니다.`,
             `1ª ${altName(ALT.indexOf(M.rank[0]))} (${M.total[M.rank[0]].toFixed(2)}). Costi = quantità × prezzi unitari ipotizzati (fonte da verificare).`);
  $('revTbl').innerHTML = `<thead><tr><th>${tr('지표','Indicatore')}</th><th>${tr('현재 가중치','Peso attuale')}</th><th>${tr('역전 가중치','Peso di inversione')}</th><th>${tr('역전 후 1위','1ª dopo')}</th><th>${tr('여유폭','Margine')}</th></tr></thead><tbody>` +
    M.rev.map(v => `<tr><td>${T(v.name)}</td><td>${v.w.toFixed(3)}</td>${v.best ? `<td>${v.w.toFixed(3)} → <b>${v.best.t.toFixed(3)}</b> (${v.best.t > v.w ? tr('증가','aumento') : tr('감소','diminuzione')})</td><td>${altName(ALT.indexOf(v.best.k))}</td><td>${(100*Math.abs(v.best.t - v.w)).toFixed(1)}%p</td>`
      : `<td colspan="3">${tr('0~1 범위에서 역전 없음','nessuna inversione tra 0 e 1')}</td>`}</tr>`).join('') + '</tbody>';
  return M;
}

/* ---------- 유의성 ---------- */
function renderSig(){
  const p1 = (+$('sP1').value)/100, p2 = (+$('sP2').value)/100, n = +$('sN').value || 500;
  const se1 = Math.sqrt(p1*(1-p1)/n), se2 = Math.sqrt(p2*(1-p2)/n), diff = Math.abs(p2-p1), crit = 2*Math.max(se1, se2);
  const z = diff / Math.sqrt(se1*se1 + se2*se2), sig = diff >= crit;
  $('sigOut').innerHTML = tr(
    `대안 1 ${(100*p1).toFixed(1)} ± ${(100*se1).toFixed(2)}% · 대안 2 ${(100*p2).toFixed(1)} ± ${(100*se2).toFixed(2)}%<br>차이 <b>${(100*diff).toFixed(1)}%p</b> ${sig ? '≥' : '<'} SE × 2 = ${(100*crit).toFixed(2)}%p → <b>${sig ? '유의' : '차이 없음'}</b><br><span class="tiny">참고: 두 표본 z = ${z.toFixed(2)} (|z| ≥ 1.96이면 95% 유의) · 표기는 값 옆에 ± SE를 남기고 판정어를 함께 기록</span>`,
    `Alt. 1 ${(100*p1).toFixed(1)} ± ${(100*se1).toFixed(2)}% · Alt. 2 ${(100*p2).toFixed(1)} ± ${(100*se2).toFixed(2)}%<br>Differenza <b>${(100*diff).toFixed(1)} punti</b> ${sig ? '≥' : '<'} 2 × SE = ${(100*crit).toFixed(2)} → <b>${sig ? 'significativa' : 'nessuna differenza'}</b><br><span class="tiny">z a due campioni = ${z.toFixed(2)} (|z| ≥ 1,96 → significativa al 95%)</span>`);
  const pm = Math.max(p1, p2, 0.0001), need = Math.ceil(4*pm*(1-pm)/(diff*diff || 1));
  $('sigCurve').textContent = diff > 0 ? tr(`이 차이를 '유의'로 판정하려면 대상지당 약 ${need.toLocaleString()}점 이상이 필요합니다(오차를 절반으로 줄이려면 표본 4배).`,
    `Per renderla significativa servono circa ${need.toLocaleString()} punti per sito (per dimezzare l’errore, 4 volte i punti).`) : '';
}
['sP1','sP2','sN'].forEach(id => $(id).oninput = renderSig);

/* ---------- ⑤ 조감 이미지 ---------- */
function renderAerial(){
  const s = S(), q = s.ccs.model.qty, dt = site === 'dongtan';
  const km = q['가로수 연장(km)'], trees = q['가로수(주)'], perm = q['투수포장(㎡)'];
  $('aeDecision').textContent = dt
    ? tr(`대안 C — 주간선·보조간선 ${km}km 양쪽 가로수 2열(약 ${trees.toLocaleString()}주, 수관폭 8m), 집산도로 포장 ${perm.toLocaleString()}㎡(30%) 투수포장 전환, 저지대 하천변 갈대 저류지 배치.`,
         `Alternativa C — due filari di alberi lungo ${km} km di arterie (circa ${trees.toLocaleString()} alberi, chioma 8m), ${perm.toLocaleString()} m² (30%) di pavimentazione permeabile sulle strade di raccolta, bacino di ritenzione a canneto lungo il fiume.`)
    : tr(`대안 C — 캠퍼스 도로 ${km}km 양쪽 가로수 2열(약 ${trees.toLocaleString()}주, 수관폭 8m), 캠퍼스 도로 포장 ${perm.toLocaleString()}㎡(30%) 투수포장 전환, 저지대 갈대 저류지.`,
         `Alternativa C — due filari lungo ${km} km di strade del campus (circa ${trees.toLocaleString()} alberi), ${perm.toLocaleString()} m² (30%) di pavimentazione permeabile, bacino a canneto.`);
  $('aePrompt').value = dt
    ? `Bright midday bird's-eye view (45-degree aerial) of a new low-rise and mid-rise residential district on gently rolling farmland in Dongtan, Hwaseong, South Korea. A 35 m arterial boulevard and 25 m secondary arterials lined on both sides with two continuous rows of mature street trees (crown about 8 m), 20 m collector streets with light-grey permeable paving on sidewalks and parking lanes, a reed retention pond in the low ground beside a small stream, green park corridor kept between neighbourhoods. Clear blue sky, soft natural daylight, high brightness, realistic urban planning visualisation, no text, no logos, no people close-up.`
    : `Bright midday bird's-eye view (45-degree aerial) of a hillside Korean university campus (Cheonan, South Korea) with modern brick and glass buildings among forested hills. Campus roads lined on both sides with two continuous rows of mature street trees (crown about 8 m), light-grey permeable paving on plazas and parking areas, a small reed retention pond at the lowest point of the campus. Clear blue sky, soft natural daylight, high brightness, realistic visualisation, no text, no logos.`;
  if (!$('aeCaption').dataset.edited)
    $('aeCaption').value = tr(`AI 생성 이미지(도구명 · 생성일 기입) — ${siteName()} 대안 C(가로수 2열 · 투수포장 · 저류지)의 개념 시각화이며 실사가 아님. 이미지 속 수목 수·면적은 값이 아님 — 수치는 CCS 1차 결과표 참조.`,
      `Immagine generata con IA (strumento · data) — visualizzazione concettuale dell’alternativa C per ${siteName()}; non è una foto. Numero di alberi e superfici nell’immagine non sono valori — vedere la tabella CCS.`);
  $('aeFig').textContent = $('aeCaption').value;
}
$('aeCaption').oninput = () => { $('aeCaption').dataset.edited = '1'; $('aeFig').textContent = $('aeCaption').value; };
function copy(id){ const t = $(id); t.select(); try{ navigator.clipboard.writeText(t.value); }catch(e){ document.execCommand('copy'); } }
$('cpPrompt').onclick = () => copy('aePrompt');
$('cpCaption').onclick = () => copy('aeCaption');
$('aeFile').onchange = e => {
  const f = e.target.files[0]; if (!f) return;
  const url = URL.createObjectURL(f), img = $('aeImg');
  img.onload = () => {
    const c = document.createElement('canvas'), k = Math.min(1, 256/Math.max(img.naturalWidth, img.naturalHeight));
    c.width = Math.max(1, img.naturalWidth*k); c.height = Math.max(1, img.naturalHeight*k);
    const x = c.getContext('2d'); x.drawImage(img, 0, 0, c.width, c.height);
    const d = x.getImageData(0, 0, c.width, c.height).data; let sum = 0;
    for (let i=0;i<d.length;i+=4) sum += 0.299*d[i] + 0.587*d[i+1] + 0.114*d[i+2];
    const mean = sum/(d.length/4);
    $('aeBright').innerHTML = tr(`평균 밝기 <b>${mean.toFixed(0)}</b> / 255 — ${mean >= 130 ? '기준(130) 이상: 밝은 장면' : '기준(130) 미만: 다시 생성 권장'}`,
      `Luminosità media <b>${mean.toFixed(0)}</b> / 255 — ${mean >= 130 ? 'sopra la soglia (130)' : 'sotto la soglia (130): rigenerare'}`);
  };
  img.src = url;
};

/* ---------- 도구 대조표 ---------- */
function renderTools(){
  const sat = S().sat, it = itreeVal(), m = S().ccs.model;
  $('tS2').innerHTML = `NDVI ${fmt(sat.ndvi.mean,3)}<br><span class="pill">${sat.s2.date} · ${tr('경계 안 구름','nuvole')} ${sat.s2.local_cloud}%</span>`;
  $('tL9').innerHTML = `LST ${fmt(sat.lst.mean,1)}°C<br><span class="pill">${sat.l9.date} · r = ${fmt(sat.ndvi_lst_r,2)}</span>`;
  $('tIT').innerHTML = it ? `${(100*it.p).toFixed(1)}% ± ${(100*it.se).toFixed(2)}<br><span class="pill">N=${it.n}</span>` : `<span class="pill">${tr('판독 대기','in attesa')}</span>`;
  $('tIV').innerHTML = `HM ${fmt(m.hm.A,3)}<br><span class="pill">${tr('가정 폭','ipotesi')} ${fmt(m.hm_range.A[0],2)}~${fmt(m.hm_range.A[1],2)}</span>`;
}

/* ---------- 내보내기 ---------- */
function csv(name, rows){
  const t = '﻿' + rows.map(r => r.map(v => `"${String(v ?? '').replace(/"/g,'""')}"`).join(',')).join('\r\n');
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([t], {type:'text/csv'})); a.download = name; a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}
const today = () => new Date().toISOString().slice(0,10);
$('exCcs').onclick = () => {
  const rows = ccsRows();
  csv(`CCS_1차결과표_${S().short}_${today()}.csv`, [['지표','값','오차·가정 폭','해상도','출처·취득일','조회일','대안 A','대안 B','대안 C','비고'],
    ...rows.map(r => [r.지표, r.값 ?? '', r['오차·가정 폭'], r.해상도, r['출처·취득일'], r.조회일, r.대안.A, r.대안.B, r.대안.C, r.비고 || ''])]);
};
$('exCat').onclick = () => {
  const s = S(), sat = s.sat, it = itreeVal();
  csv(`지표7_카탈로그_${s.short}_${today()}.csv`, [['대상','지표','값','오차','해상도','출처','장면 ID','취득일','경계 안 구름(%)','조회일'],
    [s.name, '캐노피 피복률(%)', it ? (100*it.p).toFixed(2) : '', it ? `± ${(100*it.se).toFixed(2)}%p SE` : '빈칸 — i-Tree 판독 대기', '500점 판독', 'i-Tree Canopy', '', it ? it.date : '', '', it ? it.date : ''],
    [s.name, 'NDVI 평균', sat.ndvi.mean.toFixed(4), `화소 SD ${sat.ndvi.sd.toFixed(4)} · n ${sat.ndvi.n}`, '10m', 'Sentinel-2 L2A (Planetary Computer 미러)', sat.s2.id, sat.s2.date, sat.s2.local_cloud, D.queried_on],
    [s.name, '지표온도(℃)', sat.lst.mean.toFixed(2), `화소 SD ${sat.lst.sd.toFixed(2)} · n ${sat.lst.n}`, '30m', 'Landsat 9 C2 L2 ST_B10 (Planetary Computer 미러)', sat.l9.id, `${sat.l9.date} ${sat.l9.time_utc}UTC`, sat.l9.local_cloud, D.queried_on]]);
};
$('exMx').onclick = () => {
  const M = computeMatrix();
  csv(`대안비교서식_${S().short}_${today()}.csv`, [['지표','가중치','기준선 값','기준선 점수','대안 A 값','A 점수','대안 B 값','B 점수','대안 C 값','C 점수','오차·출처'],
    ...M.rows.map(r => [r.name, r.pending ? `${r.w}(제외)` : r.wn.toFixed(3), ...['기준선','A','B','C'].flatMap(k => [r.v[k] ?? '판독 대기', r.s[k] ?? '']), `${r.unc} · ${r.src}`]),
    ['가중 합계', '1.00', '', '', ...ALT.flatMap(k => [M.total[k].toFixed(3), `${M.rank.indexOf(k)+1}위`]), M.provisional ? '잠정(캐노피 제외)' : '확정']]);
};
$('exRoad').onclick = () => {
  const t = D.sites.dongtan.roads.table, keys = Object.keys(t[0]);
  csv(`도로율_대안1안_${today()}.csv`, [keys, ...t.map(r => keys.map(k => r[k]))]);
};
$('resetAll').onclick = () => {
  try { Object.keys(localStorage).filter(k=>k.startsWith('ndvidash.')).forEach(k=>localStorage.removeItem(k)); } catch(e){}
  location.reload();
};

/* ---------- 실행 ---------- */
function renderAll(){
  loadItreeInputs();
  renderHero(); renderTasks(); renderRoads(); renderQuota(); renderScenes(); renderNdvi(); renderPixel();
  renderLst(); renderItree(); renderHM(); renderCalc(); renderCCS(); renderMatrix(); renderSig(); renderAerial(); renderTools();
  $('dn').value = Math.round((S().sat.lst.mean + 273.15 - 149.0)/0.00341802); renderLst();
}
applyLang();
renderAll();
setTimeout(fitMaps, 0);
if (store.get('view', 'grid') === 'sat') setView(true);
})();

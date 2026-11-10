const $ = id => document.getElementById(id);
const uid = () => globalThis.crypto?.randomUUID?.() || `${Date.now().toString(36)}-${Array.from(crypto.getRandomValues(new Uint32Array(4)), n => n.toString(36)).join('-')}`;
const nativeServer = new URLSearchParams(location.search).get('server') || window.MEMO_NATIVE_DEFAULT_SERVER;
const defaultServer = nativeServer || location.origin;
const names = {all: '모든 메모', pinned: '고정한 메모', trash: '휴지통'};
const date = value => new Intl.DateTimeFormat('ko-KR', {month:'long',day:'numeric'}).format(new Date(value));
let session = null, prefs = {}, notes = [], queue = [], current = null, view = 'all', query = '', sort = 'updated';
let syncing = false, syncAgain = false, authMode = 'login', toastTimer, saveTimer, storageError = false;
let transientDraft = null, inFlight = new Set(), syncPromise = null;

function toast(message) {
  $('toast').textContent = message; $('toast').hidden = false;
  clearTimeout(toastTimer); toastTimer = setTimeout(() => $('toast').hidden = true, 4500);
}
function read(key, fallback) {
  const text = localStorage.getItem(key);
  return text === null ? fallback : JSON.parse(text);
}
function key() { return `teum:notes:${session.server}:${session.userId}`; }
function persist(nextNotes = notes, nextQueue = queue) {
  try {
    localStorage.setItem(key(), JSON.stringify({version:1, notes:nextNotes, queue:nextQueue}));
    notes = nextNotes; queue = nextQueue; storageError = false; return true;
  } catch {
    storageError = true; $('save-state').textContent = '저장 실패 · 입력을 유지하고 있어요';
    toast('기기 저장 공간을 확인해 주세요. 입력한 내용은 화면에 유지됩니다.'); updateStatus(); return false;
  }
}
function loadAccount() {
  try {
    const data = read(key(), {notes:[],queue:[]});
    if (!Array.isArray(data.notes) || !Array.isArray(data.queue)) throw new Error('format');
    notes = data.notes; queue = data.queue;
  } catch { notes = []; queue = []; storageError = true; toast('저장된 메모를 읽지 못했습니다. 원본은 유지됩니다. 다시 로그인해 주세요.'); }
}
function updateStatus(message) {
  $('sync-label').textContent = message || (storageError ? '기기 저장 실패' : syncing ? '동기화 중' : !session ? '로그인하고 동기화' : queue.length ? `${queue.length}개 변경 전송 대기` : '모든 변경 저장됨');
  $('sync-dot').className = `status-dot ${storageError ? 'error' : queue.length || !navigator.onLine ? 'pending' : ''}`;
  $('account-name').textContent = session ? session.email : '나만의 공간';
  $('account-detail').textContent = session ? '기기와 서버에 연결된 나의 기록' : '로그인하고 모든 기기에서 이어 쓰세요';
}
function render() {
  const visible = notes.filter(n => !n.purged && (view === 'trash' ? n.deleted : !n.deleted && (view !== 'pinned' || n.pinned)));
  const filtered = visible.filter(n => `${n.title}\n${n.body}`.toLocaleLowerCase().includes(query.toLocaleLowerCase()));
  filtered.sort((a,b) => (view === 'all' ? Number(b.pinned) - Number(a.pinned) : 0) || (sort === 'title' ? a.title.localeCompare(b.title,'ko') : (sort === 'created' ? b.createdAt - a.createdAt : b.updatedAt - a.updatedAt)));
  $('count-all').textContent = notes.filter(n => !n.purged && !n.deleted).length;
  $('count-pinned').textContent = notes.filter(n => !n.purged && !n.deleted && n.pinned).length;
  $('count-trash').textContent = notes.filter(n => !n.purged && n.deleted).length;
  $('view-breadcrumb').textContent = names[view]; $('view-title').replaceChildren(document.createTextNode(names[view]));
  const dot = document.createElement('span'); dot.className = 'heading-dot'; dot.textContent = '.'; $('view-title').append(dot);
  $('view-description').textContent = view === 'trash' ? '잠시 내려놓은 기록. 필요해지면 언제든 되돌릴 수 있어요.' : view === 'pinned' ? '자주 꺼내 보고 싶은 생각을 가까이 두세요.' : '잊고 싶지 않은 순간, 떠오르는 생각을 담아 두세요.';
  document.querySelectorAll('[data-view]').forEach(b => b.classList.toggle('active', b.dataset.view === view));
  $('list-count').textContent = `${filtered.length}개의 메모${query ? ' 검색됨' : ''}`;
  $('note-grid').replaceChildren(...filtered.map(card));
  $('empty').hidden = filtered.length > 0;
  $('empty-title').textContent = query ? '찾는 생각이 보이지 않아요' : view === 'trash' ? '휴지통이 비어 있어요' : view === 'pinned' ? '가까이 두고 싶은 메모가 있나요?' : '아직 비어 있는 작은 공간';
  $('empty-description').textContent = query ? '다른 단어나 짧은 문장으로 다시 찾아보세요.' : view === 'trash' ? '삭제한 메모는 이곳에서 다시 만날 수 있어요.' : view === 'pinned' ? '메모를 열고 별을 누르면 이곳에 모여요.' : '오늘의 첫 생각을 여기에 남겨 볼까요?';
  $('empty-create').hidden = !!query || view !== 'all';
  updateStatus();
}
function card(note) {
  const button = document.createElement('button'); button.className = `note-card ${note.pinned ? 'pinned' : ''}`;
  button.setAttribute('aria-label', `${note.title || '제목 없는 메모'} 열기`);
  const top = document.createElement('div'); top.className = 'card-top';
  const icon = document.createElement('span'); icon.textContent = note.pinned ? '✳︎' : '▱'; top.append(icon);
  if (note.pinned) { const badge = document.createElement('span'); badge.className = 'pin-label'; badge.textContent = '☆ 고정됨'; top.append(badge); }
  const title = document.createElement('h2'); title.textContent = note.title || '제목 없는 메모';
  const preview = document.createElement('p'); preview.className = 'note-preview'; preview.textContent = note.body || '아직 쓰이지 않은 이야기';
  const bottom = document.createElement('div'); bottom.className = 'card-bottom';
  const stamp = document.createElement('span'); stamp.textContent = date(note.updatedAt);
  const tag = document.createElement('span'); tag.className = 'card-tag'; tag.textContent = queue.some(q => q.id === note.id) ? '기기에 저장됨' : '나의 기록';
  bottom.append(stamp, tag); button.append(top, title, preview, bottom); button.onclick = () => openNote(note.id); return button;
}
function openNote(id) {
  if (!flushDraft()) return;
  const note = notes.find(n => n.id === id); if (!note) return;
  current = id; $('library').hidden = true; $('editor').hidden = false;
  $('note-title').value = note.title; $('note-body').value = note.body; renderEditor(note);
  $('note-title').focus(); history.replaceState(null,'', '#note');
}
function renderEditor(note) {
  $('note-title').readOnly = note.deleted; $('note-body').readOnly = note.deleted;
  $('trash-banner').hidden = !note.deleted; $('trash-note').hidden = note.deleted; $('pin').hidden = note.deleted;
  $('pin').classList.toggle('active', note.pinned); $('pin').setAttribute('aria-label', note.pinned ? '메모 고정 해제' : '메모 고정');
  $('pin').textContent = note.pinned ? '★' : '☆';
  $('editor-date').textContent = `${date(note.createdAt || note.updatedAt)}에 남긴 생각`;
  $('char-count').textContent = `${[...$('note-body').value].length.toLocaleString()}자`;
  $('save-state').textContent = storageError ? '저장 실패 · 입력 유지 중' : queue.some(q => q.id === note.id) ? '기기에 저장됨 · 전송 대기' : '모든 변경 저장됨';
}
function operation(note, kind = 'put') {
  return {opId:uid(), id:note.id, kind, baseRevision:note.revision || 0, title:note.title, body:note.body, pinned:note.pinned, deleted:note.deleted};
}
function save(note, kind = 'put') {
  if (!session || storageError && !notes.length) return false;
  const pending = queue.filter(q => q.id !== note.id || inFlight.has(q.opId));
  const op = operation(note, kind);
  if (!persist(notes.map(n => n.id === note.id ? note : n).concat(notes.some(n => n.id === note.id) ? [] : [note]), [...pending, op])) return false;
  updateStatus(); scheduleSync(); return true;
}
function edited() {
  if (!current) return;
  const note = notes.find(n => n.id === current); if (!note || note.deleted) return;
  transientDraft = {...note, title:$('note-title').value, body:$('note-body').value, updatedAt:Date.now()};
  $('char-count').textContent = `${[...$('note-body').value].length.toLocaleString()}자`;
  $('save-state').textContent = '저장 중…';
  // Save immediately: backgrounding or force closing must not lose a debounce window.
  flushDraft();
}
function flushDraft() {
  if (!transientDraft) return true;
  if (!save(transientDraft)) return false;
  transientDraft = null;
  if (current) renderEditor(notes.find(n => n.id === current)); return true;
}
function newNote() {
  if (!session) return showAccount();
  if (!flushDraft()) return;
  const now = Date.now(), note = {id:uid(),title:'',body:'',pinned:false,deleted:false,purged:false,revision:0,createdAt:now,updatedAt:now};
  if (save(note)) { view = 'all'; render(); openNote(note.id); }
}
function back() {
  if (!flushDraft()) return;
  current = null; $('editor').hidden = true; $('library').hidden = false; history.replaceState(null,'', '#'); render();
}
function confirmation(title, description, button = '확인') {
  return new Promise(resolve => {
    $('confirm-heading').textContent = title; $('confirm-description').textContent = description; $('confirm-ok').textContent = button;
    $('confirm-dialog').onclose = () => resolve($('confirm-dialog').returnValue === 'ok');
    $('confirm-dialog').showModal();
  });
}
function apiServer(value) {
  const url = new URL(value);
  if (url.username || url.password || url.search || url.hash || url.pathname !== '/') throw new Error('서버 주소는 경로 없이 입력해 주세요.');
  if (url.protocol !== 'https:' && !(url.protocol === 'http:' && ['localhost','127.0.0.1','10.0.2.2'].includes(url.hostname))) throw new Error('HTTPS 서버 주소를 입력해 주세요. 로컬 개발은 localhost를 사용할 수 있어요.');
  return url.origin;
}
async function request(path, data, auth = session) {
  const controller = new AbortController(), timeout = setTimeout(() => controller.abort(), 12000);
  try {
    const response = await fetch(`${auth.server}${path}`, {method:'POST', headers:{'Content-Type':'application/json', ...(auth.token ? {Authorization:`Bearer ${auth.token}`} : {})}, body:JSON.stringify(data), signal:controller.signal, credentials:'omit'});
    const result = await response.json();
    if (!response.ok) { const error = new Error(result.error || '요청을 처리하지 못했습니다.'); error.status = response.status; throw error; }
    return result;
  } finally { clearTimeout(timeout); }
}
function scheduleSync() { clearTimeout(saveTimer); saveTimer = setTimeout(() => sync(), 800); }
async function sync() {
  if (!session) return;
  if (syncing) { syncAgain = true; return syncPromise; }
  if (storageError) return updateStatus('기기 저장 오류 · 입력 확인 필요');
  syncing = true; updateStatus();
  const account = session;
  // Exactly one pending operation per note is sent; edits during the request stay queued.
  const seen = new Set(); const batch = queue.filter(op => !seen.has(op.id) && seen.add(op.id)).slice(0,10);
  inFlight = new Set(batch.map(op => op.opId));
  syncPromise = (async () => {
    try {
      const response = await request('/v1/sync', {operations:batch}, account);
      if (session !== account) return;
      const ack = new Set(response.results.map(r => r.opId)), remaining = queue.filter(op => !ack.has(op.opId)).map(op => ({...op}));
      const serverNotes = new Map(response.notes.map(n => [n.id, n]));
      for (const result of response.results) {
        const sent = batch.find(b => b.opId === result.opId);
        if (!sent) continue;
        if (result.status === 'conflict') {
          // A newer local edit belongs to the conflict copy, never the server original.
          for (const op of remaining.filter(op => op.id === sent.id)) op.id = result.noteId;
          if (current === sent.id) current = result.noteId;
        }
        if (result.status === 'saved' || result.status === 'conflict') {
          for (const op of remaining.filter(op => op.id === result.noteId)) op.baseRevision = result.revision;
        }
        if (result.status === 'purge_rejected') toast('다른 기기에서 변경된 메모여서 영구 삭제하지 않았어요. 다시 확인해 주세요.');
      }
      const merged = response.notes.filter(n => !n.purged).map(n => ({...n}));
      for (const op of remaining) {
        const local = notes.find(n => n.id === op.id) || batch.find(b => response.results.some(r => r.status === 'conflict' && r.noteId === op.id && b.opId === r.opId));
        const newer = {...local, ...op, revision:op.baseRevision, updatedAt:local?.updatedAt || Date.now(), createdAt:local?.createdAt || Date.now(), purged:op.kind === 'purge'};
        const index = merged.findIndex(n => n.id === op.id);
        if (index >= 0) merged[index] = newer; else merged.push(newer);
      }
      if (!persist(merged, remaining)) return;
      if (response.results.some(r => r.status === 'conflict')) toast('동시에 수정된 메모를 발견해 충돌 사본으로 보관했어요.');
      if (current) {
        const note = notes.find(n => n.id === current && !n.purged);
        if (!note) back();
        else {
          const pending = queue.some(op => op.id === current);
          if (!pending && ($('note-title').value !== note.title || $('note-body').value !== note.body)) {
            $('note-title').value = note.title; $('note-body').value = note.body;
          }
          renderEditor(note);
        }
      }
      render();
      if (queue.length) syncAgain = true;
    } catch (error) {
      if (session !== account) return;
      updateStatus(error.status === 401 ? '로그인 만료 · 기기 저장 유지' : '연결 대기 · 기기 저장 유지');
      if (error.status === 401) toast('다시 로그인하면 기기에 남은 변경을 이어서 동기화할 수 있어요.');
    } finally {
      syncing = false; inFlight.clear();
      if (!$('sync-label').textContent.includes('유지')) updateStatus();
      if (syncAgain) { syncAgain = false; scheduleSync(); }
    }
  })();
  return syncPromise;
}
function showAccount() {
  if (!flushDraft()) return;
  $('auth-error').textContent = ''; $('signed-out').hidden = !!session; $('signed-in').hidden = !session;
  $('email').required = !session; $('password').required = !session;
  $('server-url').value = session?.server || prefs.server || defaultServer;
  $('server-url').disabled = !!session;
  if (session) { $('signed-in-email').textContent = session.email; $('pending-description').textContent = queue.length ? `${queue.length}개의 변경이 기기에 안전하게 보관되어 있어요. 동기화 후 다른 기기에서도 볼 수 있습니다.` : '기기와 서버의 메모가 연결되어 있어요.'; }
  $('account-dialog').showModal();
}
async function authenticate(event) {
  event.preventDefault(); if (session) return;
  $('auth-submit').disabled = true; $('auth-error').textContent = '';
  try {
    const server = apiServer($('server-url').value.trim() || defaultServer);
    const result = await request(`/v1/${authMode}`, {email:$('email').value.trim(), password:$('password').value}, {server});
    const next = {...result, server};
    localStorage.setItem('teum:session', JSON.stringify(next)); localStorage.setItem('teum:prefs', JSON.stringify({server}));
    session = next; storageError = false; loadAccount(); render(); $('account-dialog').close(); $('password').value = '';
    toast(authMode === 'register' ? '나만의 틈이 생겼어요. 첫 생각을 남겨 보세요.' : '반가워요. 지난 생각을 이어 볼까요?'); sync();
  } catch (error) { $('auth-error').textContent = error.message.includes('fetch') || error.name === 'AbortError' ? '서버에 연결하지 못했습니다. 주소와 연결 상태를 확인해 주세요.' : error.message; }
  finally { $('auth-submit').disabled = false; }
}
function download(content, name, mime) {
  if (window.webkit?.messageHandlers?.exportFile) { window.webkit.messageHandlers.exportFile.postMessage({content,name,mime}); return; }
  if (window.TeumExport?.save) { window.TeumExport.save(content,name,mime); return; }
  const blob = new Blob([content], {type:mime}), url = URL.createObjectURL(blob), a = document.createElement('a');
  a.href = url; a.download = name; a.click(); setTimeout(() => URL.revokeObjectURL(url),1000);
}
$('new-note').onclick = newNote; $('empty-create').onclick = newNote;
$('back').onclick = back; $('note-title').oninput = edited; $('note-body').oninput = edited;
$('search').oninput = event => { query = event.target.value; render(); };
$('sort').onchange = event => { sort = event.target.value; render(); };
document.querySelectorAll('[data-view]').forEach(button => button.onclick = () => { if (!flushDraft()) return; view = button.dataset.view; back(); });
$('account').onclick = showAccount; $('mobile-account').onclick = showAccount; $('close-account').onclick = () => $('account-dialog').close(); $('auth-form').onsubmit = authenticate;
$('toggle-auth').onclick = () => { authMode = authMode === 'login' ? 'register' : 'login'; $('auth-submit').textContent = authMode === 'login' ? '로그인' : '나만의 틈 만들기'; $('toggle-auth').textContent = authMode === 'login' ? '처음 오셨나요? 계정 만들기' : '이미 계정이 있나요? 로그인'; $('password').autocomplete = authMode === 'login' ? 'current-password' : 'new-password'; $('auth-error').textContent = ''; };
$('sync').onclick = () => session ? sync() : showAccount();
$('pin').onclick = () => { if (!flushDraft()) return; const n = notes.find(n => n.id === current); if (n && save({...n,pinned:!n.pinned,updatedAt:Date.now()})) renderEditor(notes.find(n => n.id === current)); };
$('trash-note').onclick = async () => { if (!flushDraft()) return; const n = notes.find(n => n.id === current); if (!n) return; if (await confirmation('메모를 휴지통으로 옮길까요?', '휴지통에서 언제든 복원할 수 있어요.', '휴지통으로 이동')) { if (save({...n,deleted:true,updatedAt:Date.now()})) { back(); toast('휴지통으로 옮겼어요.'); } } };
$('restore').onclick = () => { const n = notes.find(n => n.id === current); if (n && save({...n,deleted:false,updatedAt:Date.now()})) { view = 'all'; back(); toast('메모를 복원했어요.'); } };
$('purge').onclick = async () => { const n = notes.find(n => n.id === current); if (!n) return; if (await confirmation('이 메모를 영구 삭제할까요?', '동기화되면 서버에서도 내용이 지워지며 복원할 수 없습니다. 다른 기기의 동시 수정은 충돌 사본으로 보존됩니다.', '영구 삭제')) { if (save({...n,purged:true,title:'',body:'',updatedAt:Date.now()}, 'purge')) { back(); toast('영구 삭제를 기기에 저장했어요. 연결되면 서버에 반영돼요.'); } } };
$('export-note').onclick = () => { if (!flushDraft()) return; const n = notes.find(n => n.id === current); if (n) download(`${n.title}\n\n${n.body}`, `${(n.title || '메모').replace(/[^\p{L}\p{N}_-]/gu,'_').slice(0,60)}.txt`, 'text/plain;charset=utf-8'); };
$('export-all').onclick = () => { if (!flushDraft()) return; download(JSON.stringify({app:'teum',exportedAt:new Date().toISOString(),notes:notes.filter(n => !n.purged)},null,2), 'teum-notes.json','application/json'); };
$('logout').onclick = async () => {
  if (!flushDraft()) return;
  if (queue.length && !await confirmation('동기화 전 로그아웃할까요?', '보내지 못한 변경은 이 기기에 남습니다. 같은 서버·같은 계정으로 로그인하면 이어서 동기화합니다.', '로그아웃')) return;
  const old = session;
  try { localStorage.removeItem('teum:session'); } catch { toast('로그아웃 정보를 저장하지 못했습니다. 기기 저장 공간을 확인해 주세요.'); return; }
  request('/v1/logout',{},old).catch(() => {}); session = null; notes = []; queue = []; current = null; transientDraft = null;
  $('account-dialog').close(); back(); toast('로그아웃했어요.');
};
document.querySelector('.brand').onclick = event => { event.preventDefault(); view = 'all'; back(); };
document.addEventListener('keydown', event => {
  if (!(event.metaKey || event.ctrlKey)) return;
  if (event.key.toLowerCase() === 'k') { event.preventDefault(); back(); $('search').focus(); }
  if (event.key.toLowerCase() === 'n') { event.preventDefault(); if (!$('account-dialog').open) newNote(); }
  if (event.key.toLowerCase() === 's') { event.preventDefault(); flushDraft(); sync(); }
});
window.addEventListener('online', () => sync());
window.addEventListener('offline', () => updateStatus('오프라인 · 기기 저장 유지'));
window.addEventListener('pagehide', flushDraft);
window.addEventListener('beforeunload', event => { if (transientDraft || storageError) { event.preventDefault(); event.returnValue = ''; } });
document.addEventListener('visibilitychange', () => { if (document.hidden) flushDraft(); else sync(); });
window.addEventListener('popstate', () => { if (current) back(); });
$('today').textContent = new Intl.DateTimeFormat('ko-KR',{year:'numeric',month:'long',day:'numeric',weekday:'short'}).format(new Date());
try { prefs = read('teum:prefs',{}); session = read('teum:session',null); if (session) loadAccount(); }
catch { storageError = true; toast('기기 저장소를 사용할 수 없습니다. 브라우저 설정과 저장 공간을 확인해 주세요.'); }
render(); if (session) sync();
setInterval(() => { if (!document.hidden && session && navigator.onLine) sync(); },20000);
if ('serviceWorker' in navigator && !nativeServer && ['http:','https:'].includes(location.protocol)) navigator.serviceWorker.register('/sw.js').catch(() => {});

/* Design demonstration only. No API, localStorage, database or offline queue. */
(() => {
  const icon = (name) => `<svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">${({plus:'<path d="M12 5v14M5 12h14"/>',note:'<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M9 8h6M9 12h6M9 16h3"/>',back:'<path d="m14 6-6 6 6 6"/>',retry:'<path d="M20 8a8 8 0 1 0 0 8M20 3v5h-5"/>',error:'<circle cx="12" cy="12" r="9"/><path d="M12 7v6m0 4h.01"/>'})[name]}</svg>`;
  const escape = (value) => String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const samples = [
    {id:'sample-3',body:'아이디어는 작게, 완성은 끝까지.\n오늘은 메모 하나를 남기는 경험부터.',time:'2026. 10. 13 · 14:32'},
    {id:'sample-2',body:'주말에 하고 싶은 것\n\n동네 산책하기\n읽다 만 책 마저 읽기\n따뜻한 커피 한 잔',time:'2026. 10. 13 · 10:18'},
    {id:'sample-1',body:'잊기 전에 적어두기.\n생각을 꺼내 놓으면 조금 더 가벼워진다.',time:'2026. 10. 12 · 19:45'}
  ];
  let notes = samples.map(n=>({...n})), body = '', state = 'L-NORMAL', screen='SCREEN-LIST', attempt=null, timer=null, serial=0;
  const segmenter = typeof Intl.Segmenter === 'function' ? new Intl.Segmenter('ko',{granularity:'grapheme'}) : null;
  const length = (s) => segmenter ? [...segmenter.segment(s.trim())].length : null;
  const controls = `<aside class="review" aria-label="시안 검토 도구"><div class="brand"><span class="brand-mark">m.</span> MEMO / DESIGN STUDY</div><h1>작은 생각을 담는<br>가벼운 메모장.</h1><p>적고, 저장하고, 다시 꺼내보는 일.<br>그 사이의 모든 상태를 살펴봅니다.</p><div class="review-note"><p><strong>인터랙션 시안 · D0.4</strong><br>저장·재시도는 메모리 안에서만 시연합니다. 서버 저장, 영속성, 중복 방지를 검증하지 않습니다. 새로고침하면 초기화됩니다.</p></div><details open><summary>검토용 상태 선택 · 제품 UI 아님</summary><div class="controls"><label>목록 상태<select id="list-state"><option value="L-NORMAL">정상 목록</option><option value="L-LOADING">최초 로딩</option><option value="L-EMPTY">빈 목록</option><option value="L-ERROR">최초 조회 실패</option><option value="L-REFRESHING">기존 목록 갱신 중</option><option value="L-REFRESH-ERROR">저장 성공 · 목록 갱신 실패</option><option value="LONG-LIST">긴 목록 · 긴 본문</option></select></label><button id="show-list">목록 상태 보기</button><label>작성 상태<select id="create-state"><option value="C-INPUT">입력 중</option><option value="C-EMPTY">빈 본문</option><option value="C-INVALID">2,001자 초과</option><option value="C-SAVING">저장 중</option><option value="C-FAILED">확실한 미저장</option><option value="C-UNCERTAIN">저장 결과 불확실</option></select></label><button id="show-create">작성 상태 보기</button><label>다음 저장 시연 결과<select id="outcome"><option value="success">저장 성공</option><option value="failed">확실한 미저장</option><option value="uncertain">결과 불확실</option><option value="refresh-error">저장 성공 후 목록 갱신 실패</option></select></label><button id="reset">샘플 초기화</button><p>저장 중 표본은 상태가 유지됩니다. 작성 상태 보기에서 다른 상태로 전환하세요. 실제 키보드·장치 안전 영역은 네이티브 검증이 필요합니다.</p></div></details><a class="review-link" href="../../memo-list/prototype/index.html">목록 시안으로 시작</a><a class="review-link" href="../../memo-create/prototype/index.html">작성 시안으로 시작</a><a class="review-link" href="../../../design/README.md">실행 방법·검토 안내</a></aside>`;
  document.getElementById('root').innerHTML=`<div class="stage">${controls}<div class="preview"><p class="preview-caption">RESPONSIVE PREVIEW / 메모장</p><div class="canvas"><div class="demo-band">디자인 시안 · 서버 저장 없이 화면 흐름만 시연</div><main id="app" class="screen"></main></div></div></div><div id="announcement" class="sr-only" role="status" aria-live="polite"></div><dialog id="discard" data-screen-id="SCREEN-CREATE" data-state-id="C-DISCARD-CONFIRM" aria-labelledby="discard-title"><h2 id="discard-title">작성 중인 메모를 닫을까요?</h2><p>저장하지 않은 내용은 사라집니다.</p><div class="dialog-actions"><button id="keep" autofocus>계속 작성</button><button id="leave">내용 버리고 목록으로</button></div></dialog>`;
  const app=document.getElementById('app');
  const announce=(s)=>{document.getElementById('announcement').textContent=s;};
  const stop=()=>{clearTimeout(timer);timer=null;};
  const go=(s,{focus=true}={})=>{state=s;screen=s.startsWith('L-')?'SCREEN-LIST':'SCREEN-CREATE';render();if(focus)app.querySelector('h1')?.focus();};
  function listView(){
    const loading=state==='L-LOADING',empty=state==='L-EMPTY',error=state==='L-ERROR',refreshing=state==='L-REFRESHING';
    let content='';
    if(loading)content='<div role="status"><span class="spinner" aria-hidden="true"></span>메모를 불러오고 있어요.</div><div class="skeleton" aria-hidden="true"></div><div class="skeleton" aria-hidden="true"></div>';
    else if(empty)content=`<div class="center-state"><div class="state-mark">${icon('note')}</div><h2>첫 생각을 남겨볼까요?</h2><p>아직 메모가 없어요.<br>기억하고 싶은 것을 가볍게 적어보세요.</p></div>`;
    else if(error)content=`<div class="center-state"><div class="state-mark">${icon('error')}</div><h2>메모를 불러오지 못했어요</h2><p>연결 상태를 확인한 뒤<br>다시 시도해주세요.</p><button data-action-id="L-RETRY">${icon('retry')}다시 불러오기</button></div>`;
    else {
      if(state==='L-SUCCESS')content+='<div class="notice" role="status"><strong>메모를 저장했어요.</strong>새 메모를 목록에 반영했어요.</div>';
      if(state==='L-REFRESH-ERROR')content+='<div class="notice warning" role="status"><strong>저장 완료 · 목록 갱신 실패</strong>방금 저장한 메모는 아래에 있어요. 나머지 목록을 갱신하지 못했어요.<button data-action-id="L-RETRY">목록만 다시 불러오기</button></div>';
      if(refreshing)content+='<div class="notice" role="status"><span class="spinner" aria-hidden="true"></span>목록을 갱신하고 있어요. 확인한 메모는 그대로 보여드려요.</div>';
      content+=`<div class="list-meta"><span>메모 ${notes.length}개</span><span>최신순</span></div><ul class="notes">${notes.map(n=>`<li class="note" data-component-id="L-CARD" data-memo-id="${escape(n.id)}"><p class="note-body">${escape(n.body)}</p><time>${escape(n.time)}</time></li>`).join('')}</ul>`;
    }
    return `<header class="header"><div class="topline"><span class="wordmark">memo.</span><span class="badge">나의 기록</span></div><div class="title-row"><h1 tabindex="-1">메모장</h1><button class="quiet" data-action-id="L-REFRESH" ${loading||refreshing?'disabled':''} aria-label="목록 새로고침">${icon('retry')}새로고침</button></div><p class="subtitle">생각이 머무는 작은 공간.</p></header><section class="scroll" data-component-id="L-CONTENT" aria-label="메모 목록" aria-busy="${loading||refreshing}">${content}</section><footer class="footer"><button class="primary" data-action-id="L-CREATE">${icon('plus')}새 메모 작성</button><p class="footer-caption">기억하고 싶은 순간을 적어보세요.</p></footer>`;
  }
  function createView(){
    const locked=['C-SAVING','C-UNCERTAIN'].includes(state),n=length(body),invalid=n===0||n>2000||n===null;
    let notice='';
    if(state==='C-FAILED')notice='<div class="notice error" role="alert"><strong>메모가 저장되지 않았어요.</strong>입력한 내용은 그대로 있어요. 내용을 수정하거나 다시 저장해주세요.</div>';
    if(state==='C-UNCERTAIN')notice='<div class="notice warning" role="alert"><strong>저장 결과를 확인하지 못했어요.</strong>서버에 저장되었을 수 있어요. 중복 저장을 막기 위해 편집을 잠시 잠갔어요.<button data-action-id="C-RECHECK">같은 저장 결과 다시 확인</button></div>';
    if(state==='C-SAVING')notice='<div class="notice" role="status"><span class="spinner" aria-hidden="true"></span>저장 결과를 기다리고 있어요. 잠시만 기다려주세요.</div>';
    return `<header class="header"><div class="topline"><button class="back" data-action-id="C-BACK" ${locked?'disabled':''}>${icon('back')}목록</button><span class="badge">새로운 기록</span></div><h1 tabindex="-1">새 메모</h1><p class="subtitle">떠오른 생각을 잊기 전에.</p></header><section class="scroll" aria-label="메모 작성">${notice}<label class="editor-label" for="body">메모 본문</label><textarea class="editor" id="body" data-component-id="C-BODY" data-action-id="C-EDIT" aria-describedby="body-count body-error" aria-invalid="${state==='C-INVALID'}" ${locked?'readonly':''} placeholder="오늘 기억하고 싶은 것은 무엇인가요?">${escape(body)}</textarea><div class="input-meta"><span class="count" id="body-count"><span id="body-count-current" class="${n>2000?'count-over':''}">${n===null?'—':n.toLocaleString('ko-KR')}</span> / 2,000</span></div><p id="body-error" class="field-error" ${state==='C-INVALID'||n===null?'':'hidden'}>${n===null?'이 브라우저에서는 글자 수를 확인할 수 없어요. 최신 브라우저에서 열어주세요.':n>2000?'2,000자 이내로 줄여주세요.':'본문을 입력해주세요. 공백만으로는 저장할 수 없어요.'}</p><p class="editor-hint">짧은 문장도, 여러 줄의 생각도 좋아요.<br>저장이 완료되면 메모 목록으로 돌아가요.</p></section><footer class="footer"><button class="primary" data-action-id="C-SAVE" ${locked||invalid?'disabled':''}>${state==='C-SAVING'?'<span class="spinner" aria-hidden="true"></span>저장 중…':state==='C-UNCERTAIN'?'저장 결과 확인 필요':state==='C-FAILED'?'다시 저장':'메모 저장'}</button><p class="footer-caption">${locked?'저장 결과가 확인될 때까지 내용이 유지돼요.':invalid?'':'서버의 저장 완료를 확인한 뒤 목록에 반영해요.'}</p></footer>`;
  }
  function render(){
    app.dataset.screenId=screen;app.dataset.stateId=state;app.innerHTML=screen==='SCREEN-LIST'?listView():createView();
    app.querySelector('[data-action-id="L-CREATE"]')?.addEventListener('click',()=>{stop();body='';attempt=null;go('C-EMPTY');});
    app.querySelector('[data-action-id="C-BACK"]')?.addEventListener('click',()=>{if(body.trim())document.getElementById('discard').showModal();else go(notes.length?'L-NORMAL':'L-EMPTY');});
    app.querySelector('[data-action-id="L-RETRY"]')?.addEventListener('click',retryList);
    app.querySelector('[data-action-id="L-REFRESH"]')?.addEventListener('click',retryList);
    app.querySelector('[data-action-id="C-SAVE"]')?.addEventListener('click',save);
    app.querySelector('[data-action-id="C-RECHECK"]')?.addEventListener('click',()=>{stop();go('C-SAVING');announce('같은 저장 결과를 다시 확인해요.');timer=setTimeout(()=>complete(document.getElementById('outcome').value),900);});
    app.querySelector('#body')?.addEventListener('input',event=>{
      body=event.target.value;const n=length(body);state=n===0||n>2000||n===null?'C-INVALID':'C-INPUT';app.dataset.stateId=state;
      event.target.setAttribute('aria-invalid',state==='C-INVALID');document.getElementById('body-count-current').textContent=n===null?'—':n.toLocaleString('ko-KR');document.getElementById('body-count-current').classList.toggle('count-over',n>2000);
      const err=document.getElementById('body-error');err.hidden=state!=='C-INVALID';err.textContent=n===null?'이 브라우저에서는 글자 수를 확인할 수 없어요.':n>2000?'2,000자 이내로 줄여주세요.':'본문을 입력해주세요. 공백만으로는 저장할 수 없어요.';
      const button=app.querySelector('[data-action-id="C-SAVE"]');button.disabled=state==='C-INVALID';button.textContent='메모 저장';
      app.querySelector('.footer-caption').textContent=state==='C-INVALID'?'':'서버의 저장 완료를 확인한 뒤 목록에 반영해요.';
      app.querySelector('.notice.error')?.remove();attempt=null;
    });
  }
  function retryList(){stop();const initial=['L-ERROR','L-LOADING','L-EMPTY'].includes(state);go(initial?'L-LOADING':'L-REFRESHING');announce('목록을 다시 불러옵니다.');timer=setTimeout(()=>{go(notes.length?'L-NORMAL':'L-EMPTY');announce('목록을 불러왔어요.');},900);}
  function save(){if(['C-SAVING','C-UNCERTAIN'].includes(state))return;const n=length(body);if(n===null||!n||n>2000){go('C-INVALID');return;}attempt=attempt||{id:`demo-${++serial}`,body:body.trim(),time:'시연 · 방금 전'};go('C-SAVING');announce('저장 중입니다.');timer=setTimeout(()=>complete(document.getElementById('outcome').value),900);}
  function complete(result){
    if(result==='failed'){attempt=null;go('C-FAILED');announce('저장되지 않았어요. 입력한 내용은 유지됩니다.');return;}
    if(result==='uncertain'){go('C-UNCERTAIN');announce('저장 결과를 확인하지 못했어요. 편집이 잠겼습니다.');return;}
    if(attempt&&!notes.some(n=>n.id===attempt.id))notes.unshift({...attempt});
    body='';attempt=null;go(result==='refresh-error'?'L-REFRESH-ERROR':'L-SUCCESS');announce(result==='refresh-error'?'메모는 저장했지만 목록 갱신에 실패했어요.':'메모를 저장했어요.');
  }
  const sampleSaved=()=>{if(!notes.some(n=>n.id==='demo-saved'))notes.unshift({id:'demo-saved',body:'방금 저장한 메모예요.\n목록 갱신에 실패해도 저장 결과는 유지돼요.',time:'시연 · 방금 전'});};
  document.getElementById('show-list').addEventListener('click',()=>{stop();body='';attempt=null;const s=document.getElementById('list-state').value;if(s==='L-EMPTY')notes=[];else if(s==='LONG-LIST')notes=Array.from({length:14},(_,i)=>({id:'long-'+i,body:i===0?'긴 메모는 목록에서 최대 세 줄로 보여요.\n\n'+('줄바꿈과 긴 내용을 확인하기 위한 샘플입니다. '.repeat(24))+'\n나머지 내용은 목록 미리보기에서 생략됩니다.':`산책하며 떠오른 생각 ${i+1}\n작은 기록을 하나씩 쌓아가요.`,time:`2026. 10. ${String(13-Math.floor(i/3)).padStart(2,'0')} · 09:00`}));else if(!notes.length)notes=samples.map(n=>({...n}));if(s==='L-REFRESH-ERROR')sampleSaved();go(s==='LONG-LIST'?'L-NORMAL':s);});
  document.getElementById('show-create').addEventListener('click',()=>{stop();const s=document.getElementById('create-state').value;body=s==='C-EMPTY'?'':s==='C-INVALID'?'가'.repeat(2001):'오늘의 작은 생각\n\n서두르지 말고, 하나씩 완성하기.';attempt=['C-SAVING','C-UNCERTAIN'].includes(s)?{id:`demo-${++serial}`,body:body.trim(),time:'시연 · 방금 전'}:null;go(s);});
  document.getElementById('reset').addEventListener('click',()=>{stop();notes=samples.map(n=>({...n}));body='';attempt=null;document.getElementById('outcome').value='success';go('L-NORMAL');announce('샘플을 초기화했어요.');});
  document.getElementById('keep').dataset.actionId='C-KEEP';document.getElementById('leave').dataset.actionId='C-DISCARD';
  document.getElementById('keep').addEventListener('click',()=>document.getElementById('discard').close());
  document.getElementById('leave').addEventListener('click',()=>{document.getElementById('discard').close();body='';attempt=null;go(notes.length?'L-NORMAL':'L-EMPTY');});
  go(document.body.dataset.entry==='create'?'C-EMPTY':'L-NORMAL',{focus:false});
})();

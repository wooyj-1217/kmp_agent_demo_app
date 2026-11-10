// Execute the actual app in isolated device contexts; no browser or external packages required.
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const {webcrypto} = require('node:crypto');
const source = fs.readFileSync(__dirname+'/app.js','utf8');

function device() {
  const elements = new Map(), disk = new Map(); let fail = false, handler;
  function element() {
    return {hidden:false,value:'',textContent:'',dataset:{},className:'',classList:{toggle(){}},
      setAttribute(){},replaceChildren(){},append(){},focus(){},click(){},close(){this.open=false;},showModal(){this.open=true;}};
  }
  const get = id => { if (!elements.has(id)) elements.set(id,element()); return elements.get(id); };
  get('editor').hidden = true;
  const ctx = vm.createContext({
    document:{getElementById:get,createElement:element,createTextNode:text => ({textContent:text}),querySelectorAll:() => [],querySelector:()=>element(),addEventListener(){},hidden:false,activeElement:null},
    location:{search:'',origin:'http://127.0.0.1:8910',protocol:'http:'},history:{replaceState(){}},
    localStorage:{getItem:k=>disk.get(k)??null,setItem(k,v){if(fail)throw new Error('QuotaExceeded'); disk.set(k,v);},removeItem:k=>disk.delete(k)},
    navigator:{onLine:true}, window:{addEventListener(){}}, crypto:webcrypto,
    URL,URLSearchParams,Intl,Date,Map,Set,AbortController,Blob, console,
    setTimeout:()=>1,clearTimeout(){},setInterval(){},fetch:(url,options)=>handler(url,JSON.parse(options.body)),
  });
  vm.runInContext(source,ctx);
  const run = text => vm.runInContext(text,ctx);
  run(`session={server:'http://127.0.0.1:8910',userId:'user-a',email:'qa@teum.test',token:'test-only'};`);
  return {run,get,disk,fail: value => fail=value,fetch:fn=>handler=fn,
    read: expr => JSON.parse(JSON.stringify(run(expr)))};
}
const response = data => ({ok:true,json:async()=>data});
function note(body='initial', revision=1) { return {id:'n1',title:'메모',body,pinned:false,deleted:false,purged:false,revision,createdAt:1,updatedAt:1}; }

test('typing is persisted immediately and survives a device reload',()=>{
  const d=device(); d.run('newNote()'); d.get('note-title').value='한국어 제목'; d.get('note-body').value='줄 하나\n줄 둘'; d.run('edited()');
  const id=d.read('current'); assert.equal(d.read('notes[0].body'),'줄 하나\n줄 둘');
  assert.equal(d.read('queue.length'),1);
  d.run('notes=[];queue=[];loadAccount()'); assert.equal(d.read('notes[0].id'),id); assert.equal(d.read('notes[0].title'),'한국어 제목');
});

test('an offline request retains queued changes for retry',async()=>{
  const d=device(); d.run('newNote()'); const before=d.read('queue');
  d.fetch(async()=>{throw new Error('offline');}); await d.run('sync()');
  assert.deepEqual(d.read('queue'),before); assert.match(d.get('sync-label').textContent,/기기 저장 유지/);
});

test('editing while an earlier request is in flight preserves newer content and advances only its acknowledged base',async()=>{
  const d=device(); d.run(`notes=[${JSON.stringify(note())}];current='n1';`);
  d.get('note-title').value='메모'; d.get('note-body').value='first edit'; d.run('edited()');
  let finish; d.fetch(()=>new Promise(resolve=>finish=resolve)); const pending=d.run('sync()');
  const op=d.read('queue[0]'); d.get('note-body').value='newer edit'; d.run('edited()');
  assert.equal(d.read('queue.length'),2);
  finish(response({results:[{opId:op.opId,noteId:'n1',status:'saved',revision:2}],notes:[note('first edit',2)]})); await pending;
  assert.equal(d.read('notes[0].body'),'newer edit'); assert.equal(d.read('queue.length'),1); assert.equal(d.read('queue[0].baseRevision'),2);
});

test('an unsent note keeps its original base even when a newer remote snapshot is received',async()=>{
  const d=device(); d.run(`notes=[${JSON.stringify(note())}];`);
  d.run(`save({...notes[0],body:'offline local'});`);
  // Ten other notes precede n1, so n1 remains outside this network batch.
  d.run(`queue=Array.from({length:10},(_,i)=>({opId:'other'+i,id:'other'+i,kind:'put',baseRevision:0,title:'',body:'',pinned:false,deleted:false})).concat(queue);`);
  d.fetch(async(_url,body)=>response({results:body.operations.map(o=>({opId:o.opId,noteId:o.id,status:'saved',revision:1})),notes:[note('remote newer',5)]}));
  await d.run('sync()');
  assert.equal(d.read("queue.find(o=>o.id==='n1').baseRevision"),1);
  assert.equal(d.read("notes.find(o=>o.id==='n1').body"),'offline local');
});

test('a lost response retry never rebases subsequent local edits to someone else’s newer revision',async()=>{
  const d=device(); d.run(`notes=[${JSON.stringify(note())}];save({...notes[0],body:'first'});`);
  let finish; d.fetch(()=>new Promise(resolve=>finish=resolve)); const pending=d.run('sync()'), sent=d.read('queue[0]');
  d.run(`save({...notes[0],body:'second'});`);
  finish(response({results:[{opId:sent.opId,noteId:'n1',status:'saved',revision:2}],notes:[note('someone else newer',4)]})); await pending;
  assert.equal(d.read('queue[0].baseRevision'),2); assert.equal(d.read('notes[0].body'),'second');
});

test('conflict response moves a newer pending edit to its recovery copy',async()=>{
  const d=device(); d.run(`notes=[${JSON.stringify(note())}];current='n1';save({...notes[0],body:'first local'});`);
  let finish; d.fetch(()=>new Promise(resolve=>finish=resolve)); const pending=d.run('sync()'), sent=d.read('queue[0]');
  d.run(`save({...notes[0],body:'newest local'});`);
  const copy={...note('first local',1),id:'copy',title:'메모 (충돌 사본)'};
  finish(response({results:[{opId:sent.opId,noteId:'copy',status:'conflict',revision:1}],notes:[note('remote',3),copy]})); await pending;
  assert.equal(d.read('current'),'copy'); assert.equal(d.read('queue[0].id'),'copy');
  assert.equal(d.read("notes.find(n=>n.id==='copy').body"),'newest local'); assert.equal(d.read("notes.find(n=>n.id==='n1').body"),'remote');
});

test('quota failure keeps the visible draft and supports a retry',()=>{
  const d=device(); d.run('newNote()'); d.fail(true); d.get('note-title').value='아직 못 보낸 제목'; d.get('note-body').value='보존할 내용'; d.run('edited()');
  assert.equal(d.read('transientDraft.body'),'보존할 내용'); assert.equal(d.get('note-body').value,'보존할 내용');
  d.fail(false); assert.equal(d.run('flushDraft()'),true); assert.equal(d.read('notes[0].body'),'보존할 내용');
});

test('signing out or switching identity while syncing cannot import a previous account response',async()=>{
  const d=device(); d.run('newNote()'); let finish; d.fetch(()=>new Promise(resolve=>finish=resolve)); const pending=d.run('sync()');
  d.run(`session={server:'http://127.0.0.1:8910',userId:'user-b',email:'b@teum.test',token:'b'};notes=[];queue=[];`);
  finish(response({results:[],notes:[note('private a')]})); await pending; assert.deepEqual(d.read('notes'),[]);
});

const path=require('path');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE || path.resolve('verification/memo-evidence/browser-tools/node_modules/playwright'));
const fs=require('fs');
const output=process.env.MEMO_RESULTS || path.resolve('verification/memo-evidence'); fs.mkdirSync(output,{recursive:true});
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.MEMO_CHROME_EXECUTABLE,headless:true});
 const context=await browser.newContext();
 await context.tracing.start({screenshots:true,snapshots:true,sources:true});
 const page=await context.newPage();
 const token=require('crypto').randomUUID(); const title='memo-title-'+token; const body='memo-body-'+token;
 const events=[];
 async function clickUi(locator){ await locator.waitFor({timeout:90000}); const box=await locator.boundingBox(); if(!box)throw Error('UI control has no bounds');events.push({action:'mouse.click',locator:String(locator),box}); await page.mouse.click(box.x+box.width/2,box.y+box.height/2); }
 async function enterUi(locator,text){await clickUi(locator);events.push({action:'keyboard.insertText',text});await page.keyboard.insertText(text);}
 let result={events,criterion:'MEMO-PERSIST',platform:'web-wasm',scenario:'uniqueMemoSurvivesBrowserRefresh',title,body,status:'FAIL'};
 try {
  await page.goto(process.env.MEMO_URL||'http://127.0.0.1:8124');
  await clickUi(page.getByRole('button',{name:'＋ 메모',exact:true}));
  await enterUi(page.getByRole('textbox',{name:'메모 제목'}),title);
  await enterUi(page.getByRole('textbox',{name:'메모 내용'}),body);
  await clickUi(page.getByRole('button',{name:'저장',exact:true}));
  await page.getByRole('button').filter({hasText:title}).waitFor({timeout:30000});
  await page.reload();
  await page.getByRole('button',{name:'＋ 메모',exact:true}).waitFor({timeout:90000});
  await clickUi(page.getByRole('button').filter({hasText:title}));
  await page.getByRole('textbox',{name:'메모 제목'}).waitFor({timeout:90000});
  const actualTitle=await page.getByRole('textbox',{name:'메모 제목'}).innerText();
  const actualBody=await page.getByRole('textbox',{name:'메모 내용'}).innerText();
  if(actualTitle!==title||actualBody!==body) throw Error('reloaded content differs');
  await page.screenshot({path:output+'/web-'+token+'-restored.png'});
  result={...result,status:'PASS',actualTitle,actualBody};
 }catch(e){result.error=String(e);await page.screenshot({path:output+'/web-'+token+'-failure.png'});throw e;}
 finally{await context.tracing.stop({path:output+'/web-'+token+'-trace.zip'});fs.writeFileSync(output+'/web-'+token+'-observation.json',JSON.stringify(result,null,2));fs.writeFileSync(output+'/web-result.json',JSON.stringify({metadata:result,suites:[{specs:[{id:result.scenario,title:result.scenario,tests:[{expectedStatus:'passed',results:[{status:result.status==='PASS'?'passed':'failed'}]}]}]}]},null,2));await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});

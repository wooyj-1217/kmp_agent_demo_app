package app.teum.memo;

import android.test.ActivityInstrumentationTestCase2;
import android.view.View;
import android.view.ViewGroup;
import android.webkit.WebView;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;

/** Actual emulator WebView + actual localhost backend, using disposable QA data. */
@SuppressWarnings("deprecation")
public class MemoSmokeTest extends ActivityInstrumentationTestCase2<MainActivity> {
    public MemoSmokeTest() { super(MainActivity.class); }
    private WebView web;
    private WebView find(View v) {
        if (v instanceof WebView) return (WebView)v;
        if (v instanceof ViewGroup) for (int i=0;i<((ViewGroup)v).getChildCount();i++) {
            WebView found=find(((ViewGroup)v).getChildAt(i)); if(found!=null)return found;
        }
        return null;
    }
    private String js(String source) throws Exception {
        CountDownLatch done=new CountDownLatch(1);
        AtomicReference<String> value=new AtomicReference<>();
        getInstrumentation().runOnMainSync(() -> web.evaluateJavascript(source,r->{value.set(r);done.countDown();}));
        assertTrue("JavaScript callback timeout",done.await(10,TimeUnit.SECONDS)); return value.get();
    }
    private void waitFor(String condition) throws Exception {
        long deadline=System.currentTimeMillis()+20000;
        while(System.currentTimeMillis()<deadline) {
            if("true".equals(js("Boolean("+condition+")")))return;
            Thread.sleep(200);
        }
        fail("Condition timeout: "+condition+"; auth="+js("document.getElementById('auth-error').textContent")+"; sync="+js("document.getElementById('sync-label').textContent"));
    }
    public void testLoginEditSyncReloadAndRecoverableDeletion() throws Exception {
        MainActivity activity=getActivity(); web=find(activity.getWindow().getDecorView()); assertNotNull(web);
        waitFor("typeof newNote === 'function'");
        js("if(!session){showAccount();document.getElementById('email').value='qa@teum.test';document.getElementById('password').value='Teum-local-qa-2026!';document.getElementById('auth-submit').click();}");
        waitFor("session && session.email === 'qa@teum.test'");
        waitFor("!syncing");
        js("newNote();document.getElementById('note-title').value='Android native QA';document.getElementById('note-body').value='Native WebView sync survives reload';edited();sync();");
        waitFor("!syncing && queue.length===0");
        assertEquals("\"Native WebView sync survives reload\"",js("notes.find(n=>n.title==='Android native QA').body"));
        js("window.__beforeReload=true");
        getInstrumentation().runOnMainSync(() -> web.reload());
        waitFor("typeof window.__beforeReload === 'undefined' && typeof notes !== 'undefined' && notes.some(n=>n.title==='Android native QA')");
        js("current=notes.find(n=>n.title==='Android native QA').id;save({...notes.find(n=>n.id===current),deleted:true});sync();");
        waitFor("!syncing && queue.length===0");
        assertEquals("true",js("notes.find(n=>n.id===current).deleted"));
        js("save({...notes.find(n=>n.id===current),deleted:false});sync();");
        waitFor("!syncing && queue.length===0");
        assertEquals("false",js("notes.find(n=>n.id===current).deleted"));
    }
}

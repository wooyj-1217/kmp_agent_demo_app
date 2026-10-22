package memo.android

import android.app.AlertDialog
import android.view.KeyEvent
import android.view.MotionEvent
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.Before
import org.junit.Assume
import org.junit.Rule
import org.junit.rules.TestName
import org.junit.runner.RunWith
import java.net.HttpURLConnection
import java.net.URL

/** New missing acceptance paths. Real native callbacks + real JVM/SQLite via fault proxy.
 * Host maps emulator:8080 to host:18080, and emulator:18082 to the control service. */
@RunWith(AndroidJUnit4::class)
class AcceptanceTest {
    @get:Rule val testName = TestName()
    private fun captureNativeScreen() {
        if(InstrumentationRegistry.getArguments().getString("acceptance")!="true") return
        val instrumentation=InstrumentationRegistry.getInstrumentation()
        val file=java.io.File(instrumentation.targetContext.filesDir,"acceptance-${testName.methodName}.png")
        instrumentation.uiAutomation.takeScreenshot()?.let { bitmap -> file.outputStream().use { bitmap.compress(android.graphics.Bitmap.CompressFormat.PNG,100,it) }; bitmap.recycle() }
    }
    @Before fun requireControlledFixture() {
        Assume.assumeTrue("Host-controlled acceptance fixture and explicit ordering required",
            InstrumentationRegistry.getArguments().getString("acceptance") == "true")
    }
    private fun control(value: String? = null): JSONObject {
        val c = URL("http://127.0.0.1:18082/").openConnection() as HttpURLConnection
        c.connectTimeout = 30000; c.readTimeout = 30000
        if (value != null) { c.requestMethod = "POST"; c.doOutput = true; c.outputStream.use { it.write(value.toByteArray()) } }
        return try { JSONObject(c.inputStream.bufferedReader().use { it.readText() }) } finally { c.disconnect() }
    }
    private fun rows() = control().getJSONArray("rows").objects()
    private fun JSONArray.objects() = (0 until length()).map { getJSONObject(it) }
    private fun posts() = control().getJSONArray("requests").objects().count { it.getString("method") == "POST" }
    private fun views(v: View): List<View> = listOf(v) + if (v is ViewGroup) (0 until v.childCount).flatMap { views(v.getChildAt(it)) } else emptyList()
    private fun all(a: MainActivity) = views(a.window.decorView)
    private fun await(s: ActivityScenario<MainActivity>, predicate: (List<View>) -> Boolean) {
        val until = System.currentTimeMillis() + 25000
        while (System.currentTimeMillis() < until) {
            var pass = false
            s.onActivity { pass = predicate(all(it)) }
            if (pass) return
            Thread.sleep(50)
        }
        s.onActivity { a -> println("TIMEOUT VIEWS: "+all(a).filterIsInstance<TextView>().joinToString { it.text.toString().take(140)+" / "+it.contentDescription }) };fail("Acceptance UI condition timed out")
    }
    private fun click(s: ActivityScenario<MainActivity>, label: String) {
        s.onActivity { all(it).filterIsInstance<Button>().single { (it.contentDescription?.toString() ?: it.text.toString()) == label }.performClick() }
    }
    private fun text(s: ActivityScenario<MainActivity>, value: String) {
        s.onActivity { all(it).filterIsInstance<EditText>().single().setText(value) }
    }
    private fun has(label: String): (List<View>) -> Boolean = { list -> list.filterIsInstance<TextView>().any { it.visibility==View.VISIBLE && (it.contentDescription?.toString() ?: it.text.toString()) == label } }
    private fun ready(s: ActivityScenario<MainActivity>) = await(s, has("새 메모 작성"))
    private fun compose(s: ActivityScenario<MainActivity>, value: String) { ready(s); click(s, "새 메모 작성"); text(s, value) }
    @Test fun faultsPersistenceAndSaveRefresh() {
        control("""{"reset":true,"rules":[{"method":"GET","path":"/api/v1/memos","delay":3,"remaining":1}]}""")
        ActivityScenario.launch(MainActivity::class.java).use { s ->
            await(s, has("메모를 불러오고 있어요."))
            await(s, has("첫 생각을 남겨볼까요? 아직 메모가 없어요."))
            compose(s, "  first\nsecond  ")
            control("""{"rules":[{"method":"POST","path":"/api/v1/memos","delay":3,"remaining":1}]}""")
            s.onActivity {
                val save = all(it).filterIsInstance<Button>().single { it.text == "메모 저장" }
                save.performClick(); save.performClick()
            }
            await(s) { v -> v.filterIsInstance<EditText>().singleOrNull()?.isEnabled == false }
            ready(s); await(s, has("first\nsecond")); assertEquals(1, posts())
            assertEquals("first\nsecond", rows().single().getString("body"))
            control("""{"rules":[{"method":"POST","path":"/api/v1/memos","status":422,"remaining":1}]}""")
            compose(s, "retained"); click(s, "메모 저장")
            await(s, has("저장되지 않았어요. 본문을 확인하고 다시 저장해주세요."))
            s.onActivity { val editor = all(it).filterIsInstance<EditText>().single(); assertTrue(editor.isEnabled); assertEquals("retained", editor.text.toString()) }
            assertEquals(1, rows().size)
            text(s, "retained corrected"); click(s, "메모 저장"); ready(s)
            control("""{"rules":[{"method":"POST","path":"/api/v1/memos","drop_after_commit":true}]}""")
            compose(s, "Android committed response lost"); click(s, "메모 저장")
            await(s, has("같은 저장 결과 다시 확인"))
            val before = rows().single { it.getString("body") == "Android committed response lost" }
            control("""{"restart":true,"rules":[]}""")
            s.recreate()
            await(s, has("같은 저장 결과 다시 확인"))
            s.onActivity { val editor=all(it).filterIsInstance<EditText>().single(); assertFalse(editor.isEnabled); assertEquals("Android committed response lost", editor.text.toString()) }
            click(s, "같은 저장 결과 다시 확인"); ready(s)
            assertEquals(before.getInt("id"), rows().single { it.getString("body") == "Android committed response lost" }.getInt("id"))
            compose(s, "Android committed response lost"); click(s, "메모 저장"); ready(s)
            assertEquals(2, rows().count { it.getString("body") == "Android committed response lost" })
            control("""{"rules":[{"method":"GET","path":"/api/v1/memos","status":503}]}""")
            compose(s, "Android saved list failed"); click(s, "메모 저장")
            await(s, has("목록 갱신 실패 · 저장된 메모는 유지돼요.")); await(s, has("Android saved list failed"))
            val postsBefore = posts(); control("""{"rules":[]}""")
            click(s, "목록만 다시 불러오기")
            await(s) { v -> !has("목록만 다시 불러오기")(v) }
            assertEquals(postsBefore, posts()); assertEquals(5, rows().size)
            control("""{"restart":true}"""); s.recreate(); await(s, has("Android saved list failed"))
            captureNativeScreen()
        }
    }
    @Test fun orderInitialFailureBoundariesAndBack() {
        control("""{"reset":true,"rules":[{"method":"GET","path":"/api/v1/memos","status":503}]}""")
        ActivityScenario.launch(MainActivity::class.java).use { s ->
            await(s, has("목록을 불러오지 못했어요.")); control("""{"rules":[],"seed_order":true}""")
            click(s, "다시 불러오기"); await(s, has("newest date"))
            fun assertOrder() { s.onActivity { a ->
                val bodies=all(a).filterIsInstance<TextView>().map { it.text.toString() }.filter { it in listOf("newest date","tie newer id","tie older id") }
                assertEquals(listOf("newest date","tie newer id","tie older id"), bodies)
            } }
            assertOrder(); click(s, "새로고침"); await(s,has("newest date")); assertOrder()
            compose(s," \n\t ")
            s.onActivity { assertFalse(all(it).filterIsInstance<Button>().single { it.text=="메모 저장" }.isEnabled) }
            text(s,"a"); s.onActivity { assertTrue(all(it).filterIsInstance<Button>().single { it.text=="메모 저장" }.isEnabled) }
            text(s,"한👩🏽‍💻🇰🇷\r\n b")
            s.onActivity { assertTrue(all(it).filterIsInstance<TextView>().any { it.text.toString()=="6 / 2,000" }) }
            text(s,"가".repeat(2000)); s.onActivity { assertTrue(all(it).filterIsInstance<Button>().single { it.text=="메모 저장" }.isEnabled) }
            text(s,"가".repeat(2001)); s.onActivity { assertFalse(all(it).filterIsInstance<Button>().single { it.text=="메모 저장" }.isEnabled) }
            text(s,"discard test")
            s.onActivity { a ->
                val editor=all(a).filterIsInstance<EditText>().single()
                editor.requestFocus(); editor.setSelection(editor.text.length)
                (a.getSystemService(android.content.Context.INPUT_METHOD_SERVICE) as android.view.inputmethod.InputMethodManager).showSoftInput(editor,0)
            }
            InstrumentationRegistry.getInstrumentation().sendStringSync("xy")
            await(s) { it.filterIsInstance<EditText>().singleOrNull()?.text.toString()=="discard testxy" }
            // Exercise platform Back, not merely the app's list button.
            InstrumentationRegistry.getInstrumentation().sendKeyDownUpSync(KeyEvent.KEYCODE_BACK)
            InstrumentationRegistry.getInstrumentation().waitForIdleSync()
            // Confirm dialog buttons via the platform's accessible window hierarchy.
            val automation=InstrumentationRegistry.getInstrumentation().uiAutomation
            // Main-loop idleness does not guarantee the accessibility window transition is delivered.
            automation.waitForIdle(200,10000)
            if(automation.rootInActiveWindow?.findAccessibilityNodeInfosByText("계속 작성").isNullOrEmpty()) {
                InstrumentationRegistry.getInstrumentation().sendKeyDownUpSync(KeyEvent.KEYCODE_BACK)
                InstrumentationRegistry.getInstrumentation().waitForIdleSync()
                automation.waitForIdle(200,10000)
            }
            fun dialogClick(label:String) {
                val until=System.currentTimeMillis()+10000
                while(System.currentTimeMillis()<until) {
                    val node=automation.rootInActiveWindow?.findAccessibilityNodeInfosByText(label)?.firstOrNull()
                    if(node!=null){assertTrue(node.performAction(android.view.accessibility.AccessibilityNodeInfo.ACTION_CLICK));return}
                    Thread.sleep(50)
                }
                fail("Missing discard dialog action $label")
            }
            dialogClick("계속 작성"); await(s) { it.filterIsInstance<EditText>().singleOrNull()?.text.toString()=="discard testxy" }
            click(s,"목록"); dialogClick("내용 버리고 목록으로"); ready(s)
            // One path uses actual injected touchscreen input in addition to callback-based assertions.
            var x=0f; var y=0f
            s.onActivity { a ->
                val b=all(a).filterIsInstance<Button>().single { it.contentDescription=="새 메모 작성" }
                val rect=android.graphics.Rect(); assertTrue(b.getGlobalVisibleRect(rect))
                assertTrue(rect.width()>0 && rect.height()>0); x=rect.exactCenterX(); y=rect.exactCenterY()
            }
            val time=android.os.SystemClock.uptimeMillis()
            InstrumentationRegistry.getInstrumentation().sendPointerSync(MotionEvent.obtain(time,time,MotionEvent.ACTION_DOWN,x,y,0))
            InstrumentationRegistry.getInstrumentation().sendPointerSync(MotionEvent.obtain(time,time+50,MotionEvent.ACTION_UP,x,y,0))
            await(s) { it.any { v -> v is EditText } }
            text(s,"가".repeat(2000)); click(s,"메모 저장"); ready(s)
            assertEquals("가".repeat(2000),rows().first().getString("body"))
            captureNativeScreen()
        }
    }
    @Test fun prepareProcessRecovery() {
        control("""{"reset":true,"rules":[{"method":"POST","path":"/api/v1/memos","drop_after_commit":true}]}""")
        ActivityScenario.launch(MainActivity::class.java).use { s ->
            compose(s,"Android process recovery"); click(s,"메모 저장")
            await(s,has("같은 저장 결과 다시 확인"))
            assertEquals(1,rows().size)
            captureNativeScreen()
        }
    }
    @Test fun finishProcessRecovery() {
        // Host force-stops the app between these two explicitly selected instrumentation runs.
        control("""{"restart":true,"rules":[]}""")
        ActivityScenario.launch(MainActivity::class.java).use { s ->
            await(s,has("같은 저장 결과 다시 확인"))
            s.onActivity { val e=all(it).filterIsInstance<EditText>().single(); assertFalse(e.isEnabled); assertEquals("Android process recovery",e.text.toString()) }
            val before=posts()
            click(s,"같은 저장 결과 다시 확인"); ready(s)
            assertEquals(1,rows().size); assertEquals(before,posts())
            val keys=control().getJSONArray("requests").objects().filter { it.getString("method")=="POST" }.map { JSONObject(it.getString("payload")).getString("attemptId") }.distinct()
            assertEquals(1,keys.size)
            captureNativeScreen()
        }
    }
    @Test fun prepareOrdinaryDraft() {
        control("""{"reset":true,"rules":[]}""")
        ActivityScenario.launch(MainActivity::class.java).use { s -> compose(s,"ordinary process draft"); captureNativeScreen() }
    }
    @Test fun prepareDuringPostRecovery() {
        control("""{"reset":true,"rules":[{"method":"POST","path":"/api/v1/memos","delay":10,"remaining":1}]}""")
        ActivityScenario.launch(MainActivity::class.java).use { s ->
            compose(s,"Android during POST recovery"); click(s,"메모 저장")
            await(s) { it.filterIsInstance<EditText>().singleOrNull()?.isEnabled==false }
            assertEquals(0,rows().size)
            captureNativeScreen()
        }
    }
    @Test fun finishDuringPostRecovery() {
        // Host force-stops the previous target process before this delayed request commits.
        val until=System.currentTimeMillis()+20000
        while(rows().isEmpty() && System.currentTimeMillis()<until) Thread.sleep(100)
        assertEquals(1,rows().size)
        val before=posts()
        ActivityScenario.launch(MainActivity::class.java).use { s ->
            await(s,has("같은 저장 결과 다시 확인"))
            s.onActivity { val e=all(it).filterIsInstance<EditText>().single(); assertFalse(e.isEnabled); assertEquals("Android during POST recovery",e.text.toString()) }
            click(s,"같은 저장 결과 다시 확인"); ready(s)
            assertEquals(1,rows().size); assertEquals(before,posts())
            captureNativeScreen()
        }
    }
    @Test fun checkOrdinaryDraftAfterProcessRestart() {
        ActivityScenario.launch(MainActivity::class.java).use { s ->
            ready(s)
            s.onActivity { assertTrue(all(it).none { v -> v is EditText }) }
            click(s,"새 메모 작성")
            s.onActivity { assertEquals("",all(it).filterIsInstance<EditText>().single().text.toString()) }
            assertEquals(0,rows().size)
            captureNativeScreen()
        }
    }
    @Test fun largeFontAndThreeLinePreview() {
        val automation=InstrumentationRegistry.getInstrumentation().uiAutomation
        fun shell(command:String)=automation.executeShellCommand(command).use { descriptor ->
            android.os.ParcelFileDescriptor.AutoCloseInputStream(descriptor).bufferedReader().use { it.readText().trim() }
        }
        val original=shell("settings get system font_scale")
        require(original.matches(Regex("[0-9.]+")))
        control("""{"reset":true,"rules":[]}""")
        try {
            shell("settings put system font_scale 2.0")
            ActivityScenario.launch(MainActivity::class.java).use { s ->
                ready(s)
                s.onActivity {
                    assertEquals(2.0f,it.resources.configuration.fontScale,0.01f)
                    if(android.os.Build.VERSION.SDK_INT>=30) {
                        val appearance=it.window.insetsController!!.systemBarsAppearance
                        assertTrue(appearance and android.view.WindowInsetsController.APPEARANCE_LIGHT_STATUS_BARS != 0)
                        assertTrue(appearance and android.view.WindowInsetsController.APPEARANCE_LIGHT_NAVIGATION_BARS != 0)
                    }
                }
                val body="preview line one\npreview line two\npreview line three\npreview line four\npreview line five"
                compose(s,body)
                s.onActivity { a ->
                    val save=all(a).filterIsInstance<Button>().single { it.text=="메모 저장" }
                    val rect=android.graphics.Rect(); assertTrue(save.getGlobalVisibleRect(rect))
                    assertEquals(save.height,rect.height())
                }
                click(s,"메모 저장"); ready(s); await(s,has(body))
                s.onActivity { a ->
                    val card=all(a).filterIsInstance<TextView>().single { it !is EditText && it.text.toString()==body }
                    assertEquals(3,card.maxLines); assertEquals(3,card.lineCount)
                    assertTrue(card.layout.getEllipsisCount(2)>0)
                    val date=all(a).filterIsInstance<TextView>().single { it.text.toString().contains("T") && it.text.toString().endsWith("Z") }
                    assertTrue(date.contentDescription.toString().startsWith("작성 시각 "))
                    assertNotEquals(date.text.toString(),date.contentDescription.toString())
                }
                assertEquals(body,rows().single().getString("body"))
                captureNativeScreen()
            }
        } finally { shell("settings put system font_scale $original") }
    }
    @Test fun failureEditKeepsFocus() {
        control("""{"reset":true,"rules":[{"method":"POST","path":"/api/v1/memos","status":422,"remaining":1}]}""")
        ActivityScenario.launch(MainActivity::class.java).use { s ->
            compose(s,"failed draft"); click(s,"메모 저장")
            await(s,has("저장되지 않았어요. 본문을 확인하고 다시 저장해주세요."))
            s.onActivity { a -> val editor=all(a).filterIsInstance<EditText>().single(); editor.requestFocus(); editor.setSelection(editor.text.length) }
            InstrumentationRegistry.getInstrumentation().waitForIdleSync()
            // Finish the focus/IME window transition before injecting hardware key events.
            InstrumentationRegistry.getInstrumentation().uiAutomation.waitForIdle(200,10000)
            InstrumentationRegistry.getInstrumentation().sendStringSync(" changed")
            await(s) { v -> v.filterIsInstance<EditText>().singleOrNull()?.text.toString()=="failed draft changed" }
            s.onActivity { a ->
                val editor=all(a).filterIsInstance<EditText>().single()
                assertTrue(editor.hasFocus()); assertEquals(editor.text.length,editor.selectionStart)
                assertTrue(all(a).filterIsInstance<TextView>().none { it.visibility==View.VISIBLE && it.text=="저장되지 않았어요. 본문을 확인하고 다시 저장해주세요." })
            }
            click(s,"메모 저장"); ready(s); assertEquals(1,rows().size); captureNativeScreen()
        }
    }
    @Test fun designConformance() {
        control("""{"reset":true,"rules":[]}""")
        fun shot(name:String){
            val inst=InstrumentationRegistry.getInstrumentation();inst.waitForIdleSync();Thread.sleep(1000);inst.waitForIdleSync()
            val file=java.io.File(inst.targetContext.filesDir,"design-$name.png")
            inst.uiAutomation.takeScreenshot()?.let {b->file.outputStream().use{b.compress(android.graphics.Bitmap.CompressFormat.PNG,100,it)};b.recycle()}
        }
        ActivityScenario.launch(MainActivity::class.java).use{s->
            await(s,has("첫 생각을 남겨볼까요? 아직 메모가 없어요."));shot("empty-list")
            click(s,"새 메모 작성")
            s.onActivity{a->
                val e=all(a).filterIsInstance<EditText>().single();val back=all(a).filterIsInstance<Button>().single{it.contentDescription=="목록"}
                val er=android.graphics.Rect();val br=android.graphics.Rect();e.getGlobalVisibleRect(er);back.getGlobalVisibleRect(br)
                assertTrue("Back belongs in header",br.bottom<er.top)
                assertFalse(all(a).filterIsInstance<Button>().single{it.text=="메모 저장"}.isEnabled)
                assertTrue(all(a).filterIsInstance<TextView>().any{it.text.toString().contains("짧은 문장도")})
                val count=all(a).filterIsInstance<TextView>().single{it.text.toString()=="0 / 2,000"};assertEquals(android.view.Gravity.END,count.gravity and android.view.Gravity.RELATIVE_HORIZONTAL_GRAVITY_MASK)
            };shot("empty-create")
            text(s,"a");text(s,"");await(s,has("본문을 입력해주세요. 공백만으로는 저장할 수 없어요."));shot("empty-invalid")
            text(s,"디자인 비교 메모\n두 번째 줄");shot("input")
            text(s,"가".repeat(2001));s.onActivity{a->assertFalse(all(a).filterIsInstance<Button>().single{it.text=="메모 저장"}.isEnabled);val editor=all(a).filterIsInstance<EditText>().single();assertEquals((220*a.resources.displayMetrics.density).toInt(),editor.height);assertTrue(all(a).filterIsInstance<TextView>().any{it.text.toString()=="2001 / 2,000"})};shot("invalid")
            text(s,"디자인 비교 메모\n두 번째 줄")
            control("""{"rules":[{"method":"POST","path":"/api/v1/memos","delay":10,"status":422,"remaining":1}]}""")
            click(s,"메모 저장");await(s,has("저장 중…"));shot("saving")
            await(s,has("저장되지 않았어요. 본문을 확인하고 다시 저장해주세요."));shot("failed")
            text(s,"디자인 비교 메모\n두 번째 줄 · 수정");click(s,"메모 저장");ready(s)
            await(s,has("디자인 비교 메모\n두 번째 줄 · 수정"));assertEquals(1,rows().size);shot("list")
            control("""{"rules":[{"method":"POST","path":"/api/v1/memos","drop_after_commit":true}]}""")
            compose(s,"불확실 결과 디자인 확인");click(s,"메모 저장");await(s,has("같은 저장 결과 다시 확인"));shot("uncertain")
            control("""{"rules":[]}""");click(s,"같은 저장 결과 다시 확인");ready(s);assertEquals(2,rows().size);captureNativeScreen()
        }
    }

    @Test fun previewLiveServerReadOnly() {
        val c=URL("http://127.0.0.1:8080/api/v1/memos").openConnection() as HttpURLConnection
        val expected=try{assertEquals(200,c.responseCode);JSONObject(c.inputStream.bufferedReader().use{it.readText()}).getJSONArray("memos").objects()}finally{c.disconnect()}
        ActivityScenario.launch(MainActivity::class.java).use{s->
            ready(s)
            for(memo in expected)await(s,has(memo.getString("body")))
            if(expected.isNotEmpty())await(s,has("메모 ${expected.size}개"))
            Thread.sleep(1000);captureNativeScreen()
        }
    }

}

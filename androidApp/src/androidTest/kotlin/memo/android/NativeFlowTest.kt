package memo.android

import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith

/** Real Android Activity/native Views against the isolated local HTTP/SQLite fixture.
 * Uses native view callbacks; not a hardware-keyboard/accessibility/screenshot test. */
@RunWith(AndroidJUnit4::class)
class NativeFlowTest {
    private fun views(view: View): List<View> = listOf(view) +
        if (view is ViewGroup) (0 until view.childCount).flatMap { views(view.getChildAt(it)) } else emptyList()
    private fun await(scenario: ActivityScenario<MainActivity>, check: (List<View>)->Boolean) {
        val end=System.currentTimeMillis()+20000
        while(System.currentTimeMillis()<end) {
            var passed=false
            scenario.onActivity { passed=check(views(it.window.decorView)) }
            if(passed)return
            Thread.sleep(50)
        }
        fail("Native UI condition did not become true within 20s")
    }
    @Test fun actualSaveBoundaryAndGenericDraftNotRestored() {
        ActivityScenario.launch(MainActivity::class.java).use { scenario ->
            await(scenario){ all->all.filterIsInstance<Button>().any{it.contentDescription=="새 메모 작성"} }
            scenario.onActivity {activity->views(activity.window.decorView).filterIsInstance<Button>().single{it.contentDescription=="새 메모 작성"}.performClick()}
            scenario.onActivity {activity->
                val all=views(activity.window.decorView)
                all.filterIsInstance<EditText>().single().setText("가".repeat(2001))
                assertFalse(all.filterIsInstance<Button>().single{it.text=="메모 저장"}.isEnabled)
                all.filterIsInstance<EditText>().single().setText("Android native flow ${System.currentTimeMillis()}")
                all.filterIsInstance<Button>().single{it.text=="메모 저장"}.performClick()
            }
            await(scenario){ all->all.filterIsInstance<TextView>().any{it.text.toString().startsWith("Android native flow")} && all.filterIsInstance<Button>().any{it.contentDescription=="새 메모 작성"} }
            scenario.onActivity {activity->views(activity.window.decorView).filterIsInstance<Button>().single{it.contentDescription=="새 메모 작성"}.performClick()}
            scenario.onActivity {activity->views(activity.window.decorView).filterIsInstance<EditText>().single().setText("일반 초안 복원 안 함")}
            scenario.recreate()
            await(scenario){ all->all.none{it is EditText} && all.filterIsInstance<Button>().any{it.contentDescription=="새 메모 작성"} }
        }
    }
}

package dev.yeoback.app

import android.content.Intent
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createEmptyComposeRule
import androidx.test.core.app.ActivityScenario
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Rule
import org.junit.Test
import java.util.UUID

class MemoRestartTest {
    @get:Rule val ui = createEmptyComposeRule()
    @Test fun uniqueMemoSurvivesActivityRelaunch() {
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        val token = UUID.randomUUID().toString()
        val title = "title-$token"
        val body = "body-$token"
        val file = "acceptance-$token.txt"
        val intent = Intent(context, MainActivity::class.java).putExtra("test-storage-file", file)
        try {
            ActivityScenario.launch<MainActivity>(intent).use {
                ui.onNodeWithTag("new-memo").performClick()
                ui.onNodeWithTag("memo-title").performTextInput(title)
                ui.onNodeWithTag("memo-body").performTextInput(body)
                ui.onNodeWithTag("save-memo").performClick()
                ui.onNodeWithText(title).assertExists()
            }
            ActivityScenario.launch<MainActivity>(intent).use {
                ui.onNodeWithText(title).performClick()
                ui.onNodeWithTag("memo-title").assertTextEquals(title)
                ui.onNodeWithTag("memo-body").assertTextEquals(body)
            }
        } finally { context.deleteFile(file) }
    }
}

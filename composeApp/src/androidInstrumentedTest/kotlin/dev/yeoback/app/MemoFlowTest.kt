package dev.yeoback.app

import android.content.Context
import android.content.ContextWrapper
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.junit4.StateRestorationTester
import androidx.test.platform.app.InstrumentationRegistry
import dev.yeoback.domain.MemoRepository
import dev.yeoback.domain.MemoStorage
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import java.io.File
import java.util.UUID

class MemoFlowTest {
    @get:Rule val ui = createComposeRule()

    private class TestStorage : MemoStorage {
        private val context = InstrumentationRegistry.getInstrumentation().targetContext
        private val delegate = AndroidMemoStorage(context, "yeoback-instrumented-only.txt")
        var fail = false
        init { context.deleteFile("yeoback-instrumented-only.txt") }
        override fun read(): String? = delegate.read()
        override fun write(value: String) {
            check(!fail) { "Injected write failure" }
            delegate.write(value)
        }
    }
    private fun launch(storage: TestStorage): MemoRepository {
        val repo = createRepository(storage)
        ui.setContent { YeobackApp { repo } }
        ui.waitUntil(10_000) { ui.onAllNodesWithTag("new-memo").fetchSemanticsNodes().isNotEmpty() }
        return repo
    }
    private fun create(title: String, body: String) {
        ui.onNodeWithTag("new-memo").performClick()
        ui.onNodeWithTag("memo-title").performTextInput(title)
        ui.onNodeWithTag("memo-body").performTextInput(body)
        ui.onNodeWithTag("save-memo").performClick()
    }

    @Test fun createSearchPinTrashRestoreAndPersist() {
        val storage = TestStorage(); launch(storage)
        create("기억할 문장", "첫 번째 줄\n둘째 줄 🌿")
        ui.onNodeWithText("기억할 문장").performClick()
        ui.onNodeWithTag("memo-body").assertTextEquals("첫 번째 줄\n둘째 줄 🌿")
        ui.onNodeWithTag("pin-memo").performClick()
        ui.onNodeWithTag("editor-back").performClick()
        ui.onNodeWithTag("nav-pinned").performClick()
        ui.onNodeWithText("기억할 문장").assertExists()
        ui.onNodeWithText("기억할 문장").performClick()
        ui.onNodeWithTag("trash-memo").performClick()
        ui.onNodeWithTag("nav-trash").performClick()
        ui.onNodeWithText("기억할 문장").performClick()
        ui.onNodeWithTag("restore-memo").performClick()
        ui.onNodeWithTag("memo-search").performTextInput("둘째 줄")
        ui.onNodeWithText("기억할 문장").assertExists()
        ui.runOnIdle {
            val restored = createRepository(storage).memos.single()
            assertEquals("첫 번째 줄\n둘째 줄 🌿", restored.body)
            assertTrue(restored.pinned); assertNull(restored.deletedAt)
        }
    }

    @Test fun blankAndDiscardDoNotSave() {
        val storage = TestStorage(); val repo = launch(storage)
        ui.onNodeWithTag("new-memo").performClick()
        ui.onNodeWithTag("save-memo").assertIsNotEnabled()
        ui.onNodeWithTag("memo-title").performTextInput("아직 저장 전")
        ui.onNodeWithTag("editor-back").performClick()
        ui.onNodeWithTag("keep-editing").performClick()
        ui.onNodeWithTag("memo-title").assertTextEquals("아직 저장 전")
        ui.onNodeWithTag("editor-back").performClick()
        ui.onNodeWithTag("discard-draft").performClick()
        ui.onNodeWithText("첫 생각을 남겨볼까요?").assertExists()
        ui.runOnIdle { assertTrue(repo.memos.isEmpty()); assertNull(storage.read()) }
    }

    @Test fun failedWriteKeepsDraftAndRetrySavesOnce() {
        val storage = TestStorage(); val repo = launch(storage)
        ui.onNodeWithTag("new-memo").performClick()
        ui.onNodeWithTag("memo-body").performTextInput("실패해도 남는 초안")
        ui.runOnIdle { storage.fail = true }
        ui.onNodeWithTag("save-memo").performClick()
        ui.onNodeWithTag("memo-body").assertTextEquals("실패해도 남는 초안")
        ui.onNodeWithTag("retry-write").assertExists()
        ui.runOnIdle { assertTrue(repo.memos.isEmpty()); storage.fail = false }
        ui.onNodeWithTag("retry-write").performClick()
        ui.onNodeWithText("제목 없는 메모").assertExists()
        ui.runOnIdle { assertEquals(1, createRepository(storage).memos.size) }
    }

    @Test fun permanentDeleteNeedsConfirmation() {
        val storage = TestStorage(); val repo = launch(storage)
        create("삭제 시험용 기록", "검증 전용")
        ui.onNodeWithText("삭제 시험용 기록").performClick()
        ui.onNodeWithTag("trash-memo").performClick()
        ui.onNodeWithTag("nav-trash").performClick()
        ui.onNodeWithText("삭제 시험용 기록").performClick()
        ui.onNodeWithTag("purge-memo").performClick()
        ui.onNodeWithText("취소").performClick()
        ui.runOnIdle { assertEquals(1, repo.memos.size) }
        ui.onNodeWithTag("purge-memo").performClick()
        ui.onNodeWithTag("confirm-purge").performClick()
        ui.onNodeWithText("휴지통이 비어 있어요").assertExists()
        ui.runOnIdle { assertTrue(createRepository(storage).memos.isEmpty()) }
    }

    @Test fun unsavedDraftSurvivesStateRestoration() {
        val storage = TestStorage()
        val restoration = StateRestorationTester(ui)
        restoration.setContent { YeobackApp { createRepository(storage) } }
        ui.waitUntil(10_000) { ui.onAllNodesWithTag("new-memo").fetchSemanticsNodes().isNotEmpty() }
        ui.onNodeWithTag("new-memo").performClick()
        ui.onNodeWithTag("memo-title").performTextInput("복원할 초안")
        ui.onNodeWithTag("memo-body").performTextInput("아직 저장하지 않은 본문")
        restoration.emulateSavedInstanceStateRestore()
        ui.waitUntil(10_000) { ui.onAllNodesWithTag("memo-body").fetchSemanticsNodes().isNotEmpty() }
        ui.onNodeWithTag("memo-title").assertTextEquals("복원할 초안")
        ui.onNodeWithTag("memo-body").assertTextEquals("아직 저장하지 않은 본문")
        ui.onNodeWithTag("editor-back").performClick()
        ui.onNodeWithTag("keep-editing").assertExists()
        ui.runOnIdle { assertTrue(createRepository(storage).memos.isEmpty()) }
    }

    @Test fun actualAtomicFileFailurePreservesOldBytesAndCanRetry() {
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        val directory = File(context.cacheDir, "yeoback-storage-${UUID.randomUUID()}").apply { check(mkdirs()) }
        val isolated = object : ContextWrapper(context) {
            override fun getApplicationContext(): Context = this
            override fun getFilesDir(): File = directory
        }
        try {
            val storage = AndroidMemoStorage(isolated, "notes.txt")
            storage.write("원래 기록 🌿\n둘째 줄")
            check(directory.setWritable(false, false))
            try {
                storage.write("반영되면 안 되는 기록")
                fail("Read-only destination must reject write")
            } catch (_: Exception) {
                // The actual adapter failed before publishing its new snapshot.
            } finally {
                check(directory.setWritable(true, true))
            }
            assertEquals("원래 기록 🌿\n둘째 줄", storage.read())
            storage.write("재시도 성공")
            assertEquals("재시도 성공", AndroidMemoStorage(isolated, "notes.txt").read())
            assertEquals(listOf("notes.txt"), directory.listFiles()!!.map { it.name })
        } finally {
            directory.setWritable(true, true)
            directory.deleteRecursively()
        }
    }
}

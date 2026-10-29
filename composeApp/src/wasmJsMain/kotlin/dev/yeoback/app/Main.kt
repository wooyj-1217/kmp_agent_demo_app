package dev.yeoback.app

import androidx.compose.ui.ExperimentalComposeUiApi
import androidx.compose.ui.window.ComposeViewport
import dev.yeoback.domain.MemoStorage
import kotlin.JsFun

@OptIn(ExperimentalComposeUiApi::class)
fun main() {
    prepareKeyboardBridge()
    removeLoadingPlaceholder()
    ComposeViewport("app", configure = { isA11YEnabled = true }) {
        YeobackApp { createRepository(BrowserMemoStorage()) }
    }
}

private class BrowserMemoStorage : MemoStorage {
    override fun read(): String? {
        val result = readMemos()
        return when (result.firstOrNull()) {
            '0' -> null
            '1' -> result.substring(1)
            else -> error("저장된 메모를 읽지 못했습니다. 브라우저 저장소 접근을 확인해 주세요.")
        }
    }

    override fun write(value: String) {
        check(writeMemos(value)) { "메모를 저장하지 못했습니다. 브라우저 저장 공간을 확인해 주세요." }
    }
}

@JsFun("() => { try { const value = window.localStorage.getItem('yeoback.memos.v1'); return value === null ? '0' : '1' + value; } catch (_) { return '2'; } }")
private external fun readMemos(): String

@JsFun("value => { try { window.localStorage.setItem('yeoback.memos.v1', value); return true; } catch (_) { return false; } }")
private external fun writeMemos(value: String): Boolean

@JsFun("() => { document.getElementById('loading')?.remove(); }")
private external fun removeLoadingPlaceholder()

@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class)

package dev.yeoback.app

import androidx.compose.ui.window.ComposeUIViewController
import dev.yeoback.domain.MemoStorage
import platform.Foundation.NSDocumentDirectory
import platform.Foundation.NSProcessInfo
import platform.Foundation.NSFileManager
import platform.Foundation.NSSearchPathForDirectoriesInDomains
import platform.Foundation.NSString
import platform.Foundation.NSUTF8StringEncoding
import platform.Foundation.NSUserDomainMask
import platform.Foundation.create
import platform.Foundation.stringWithContentsOfFile
import platform.Foundation.writeToFile

fun MainViewController() = ComposeUIViewController {
    YeobackApp { createRepository(AppleMemoStorage()) }
}

private class AppleMemoStorage : MemoStorage {
    private val path: String
        get() {
            val directory = NSSearchPathForDirectoriesInDomains(
                NSDocumentDirectory, NSUserDomainMask, true,
            ).firstOrNull() as? String ?: error("기기 저장 경로를 찾지 못했습니다.")
            val fileName = if (NSProcessInfo.processInfo.arguments.contains("--uitest")) {
                "yeoback-uitest-memos-v1.txt"
            } else {
                "yeoback-memos-v1.txt"
            }
            return "$directory/$fileName"
        }

    override fun read(): String? {
        val location = path
        if (!NSFileManager.defaultManager.fileExistsAtPath(location)) return null
        return NSString.stringWithContentsOfFile(location, NSUTF8StringEncoding, null)
            ?: error("저장된 메모를 읽지 못했습니다.")
    }

    override fun write(value: String) {
        check(NSString.create(string = value).writeToFile(path, true, NSUTF8StringEncoding, null)) {
            "메모를 기기에 저장하지 못했습니다."
        }
    }
}

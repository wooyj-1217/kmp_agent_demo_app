package dev.yeoback.app

import android.content.Context
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import dev.yeoback.domain.MemoStorage
import java.io.File
import java.io.FileOutputStream

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        val storage = AndroidMemoStorage(this)
        setContent { YeobackApp { createRepository(storage) } }
    }
}

/** Same-directory rename publishes a complete UTF-8 snapshot only after its bytes sync. */
internal class AndroidMemoStorage(
    context: Context,
    fileName: String = "yeoback-memos-v1.txt",
) : MemoStorage {
    private val directory = context.applicationContext.filesDir
    private val target: File

    init {
        require(fileName.isNotBlank() && fileName != "." && fileName != ".." &&
            '/' !in fileName && '\\' !in fileName) { "Invalid private storage filename" }
        target = File(directory, fileName)
    }

    override fun read(): String? {
        if (!target.exists()) return null
        return target.readText(Charsets.UTF_8)
    }

    override fun write(value: String) {
        val temporary = File.createTempFile("yeoback-", ".tmp", directory)
        try {
            FileOutputStream(temporary).use { output ->
                output.write(value.toByteArray(Charsets.UTF_8))
                output.fd.sync()
            }
            check(temporary.renameTo(target)) { "메모를 기기에 저장하지 못했습니다." }
        } finally {
            temporary.delete()
        }
    }
}

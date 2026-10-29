package dev.yeoback.app

import androidx.compose.runtime.Composable
import dev.yeoback.domain.MemoRepository
import dev.yeoback.domain.MemoStorage

expect fun platformNow(): Long
expect fun platformId(): String
expect fun platformDate(timestamp: Long): String
expect fun platformInitialRoute(): String
expect fun platformReplaceRoute(route: String)
expect fun platformIsWeb(): Boolean

@Composable
expect fun PlatformNavigation(route: String, dirty: Boolean, onRoute: (String) -> Unit, onBack: () -> Unit)

@Composable
expect fun PlatformKeyboard(enabled: Boolean, onTab: (Boolean) -> Boolean)

fun createRepository(storage: MemoStorage) = MemoRepository(storage, ::platformNow, ::platformId)

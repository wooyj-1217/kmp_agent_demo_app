package dev.yeoback.app

import androidx.activity.compose.BackHandler
import androidx.compose.runtime.Composable
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.UUID

actual fun platformNow(): Long = System.currentTimeMillis()
actual fun platformId(): String = UUID.randomUUID().toString()
actual fun platformDate(timestamp: Long): String =
    SimpleDateFormat("yyyy. M. d. HH:mm", Locale.getDefault()).format(Date(timestamp))
actual fun platformInitialRoute(): String = "all"
actual fun platformReplaceRoute(route: String) = Unit

@Composable
actual fun PlatformNavigation(
    route: String,
    dirty: Boolean,
    onRoute: (String) -> Unit,
    onBack: () -> Unit,
) {
    BackHandler(enabled = route != "all" || dirty, onBack = onBack)
}

actual fun platformIsWeb(): Boolean = false

@Composable
actual fun PlatformKeyboard(enabled: Boolean, onTab: (Boolean) -> Boolean) = Unit

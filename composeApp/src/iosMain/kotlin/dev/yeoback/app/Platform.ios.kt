package dev.yeoback.app

import androidx.compose.runtime.Composable
import platform.Foundation.NSDate
import platform.Foundation.NSDateFormatter
import platform.Foundation.NSUUID
import platform.Foundation.dateWithTimeIntervalSince1970
import platform.Foundation.timeIntervalSince1970

actual fun platformNow(): Long = (NSDate().timeIntervalSince1970 * 1000.0).toLong()
actual fun platformId(): String = NSUUID().UUIDString
actual fun platformDate(timestamp: Long): String = NSDateFormatter().run {
    dateFormat = "yyyy. M. d. HH:mm"
    stringFromDate(NSDate.dateWithTimeIntervalSince1970(timestamp / 1000.0))
}
actual fun platformInitialRoute(): String = "all"
actual fun platformReplaceRoute(route: String) = Unit

@Composable
actual fun PlatformNavigation(
    route: String,
    dirty: Boolean,
    onRoute: (String) -> Unit,
    onBack: () -> Unit,
) = Unit

actual fun platformIsWeb(): Boolean = false

@Composable
actual fun PlatformKeyboard(enabled: Boolean, onTab: (Boolean) -> Boolean) = Unit

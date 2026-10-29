package dev.yeoback.app

import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.rememberUpdatedState
import kotlin.JsFun

actual fun platformNow(): Long = browserNow().toLong()
actual fun platformId(): String = browserId()
actual fun platformDate(timestamp: Long): String = browserDate(timestamp.toDouble())
actual fun platformInitialRoute(): String = readRoute().ifEmpty { "all" }
actual fun platformReplaceRoute(route: String) = replaceRoute(route)

@Composable
actual fun PlatformNavigation(
    route: String,
    dirty: Boolean,
    onRoute: (String) -> Unit,
    onBack: () -> Unit,
) {
    val latestOnRoute = rememberUpdatedState(onRoute)
    DisposableEffect(Unit) {
        val listener: () -> Unit = { latestOnRoute.value(platformInitialRoute()) }
        addPopState(listener)
        onDispose { removePopState(listener) }
    }
    LaunchedEffect(route) { pushRoute(route) }
    DisposableEffect(dirty) {
        if (dirty) enableUnloadGuard()
        onDispose { disableUnloadGuard() }
    }
}

@JsFun("() => Date.now()")
private external fun browserNow(): Double
@JsFun("() => crypto.randomUUID()")
private external fun browserId(): String
@JsFun("time => new Date(time).toLocaleString(undefined, {year:'numeric',month:'numeric',day:'numeric',hour:'2-digit',minute:'2-digit'})")
private external fun browserDate(time: Double): String
@JsFun("() => { try { return decodeURIComponent(window.location.hash.slice(1)); } catch (_) { return 'all'; } }")
private external fun readRoute(): String
@JsFun("route => { const hash = '#' + encodeURIComponent(route); if (window.location.hash !== hash) window.history.pushState(null, '', hash); }")
private external fun pushRoute(route: String)
@JsFun("route => { window.history.replaceState(null, '', '#' + encodeURIComponent(route)); }")
private external fun replaceRoute(route: String)
@JsFun("callback => { window.addEventListener('popstate', callback); }")
private external fun addPopState(callback: () -> Unit)
@JsFun("callback => { window.removeEventListener('popstate', callback); }")
private external fun removePopState(callback: () -> Unit)
@JsFun("() => { window.__yeobackUnload = event => { event.preventDefault(); event.returnValue = ''; }; window.addEventListener('beforeunload', window.__yeobackUnload); }")
private external fun enableUnloadGuard()
@JsFun("() => { if (window.__yeobackUnload) { window.removeEventListener('beforeunload', window.__yeobackUnload); delete window.__yeobackUnload; } }")
private external fun disableUnloadGuard()

actual fun platformIsWeb(): Boolean = true

@Composable
actual fun PlatformKeyboard(enabled: Boolean, onTab: (Boolean) -> Boolean) {
    val latestOnTab = rememberUpdatedState(onTab)
    DisposableEffect(Unit) {
        onDispose { releaseKeyboardBridge() }
    }
    DisposableEffect(enabled) {
        prepareKeyboardBridge()
        if (enabled) {
            registerKeyboardCallback { shifted -> latestOnTab.value(shifted) }
        } else {
            clearKeyboardCallback()
        }
        onDispose { clearKeyboardCallback() }
    }
}

@JsFun("() => { if (window.__yeobackKeyboard_listener) return; window.__yeobackKeyboard_listener = event => { const callback = window.__yeobackKeyboard_callback; if (callback && event.key === 'Tab' && !event.ctrlKey && !event.metaKey) { if (callback(event.shiftKey)) { event.preventDefault(); event.stopImmediatePropagation(); } } }; window.addEventListener('keydown', window.__yeobackKeyboard_listener, true); }")
internal external fun prepareKeyboardBridge()

@JsFun("callback => { window.__yeobackKeyboard_callback = callback; }")
private external fun registerKeyboardCallback(callback: (Boolean) -> Boolean)

@JsFun("() => { window.__yeobackKeyboard_callback = null; }")
private external fun clearKeyboardCallback()

@JsFun("() => { window.__yeobackKeyboard_callback = null; if (window.__yeobackKeyboard_listener) { window.removeEventListener('keydown', window.__yeobackKeyboard_listener, true); delete window.__yeobackKeyboard_listener; } }")
private external fun releaseKeyboardBridge()

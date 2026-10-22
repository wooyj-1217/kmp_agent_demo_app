package memo

import kotlin.test.*
import memo.domain.*
import memo.client.*

class PolicyTest {
    @Test fun limitsAndWhitespace() {
        assertFalse(BodyPolicy.valid("\t \n\u3000"))
        assertTrue(BodyPolicy.valid("가".repeat(2000)))
        assertFalse(BodyPolicy.valid("가".repeat(2001)))
        assertEquals("a\r\n b", BodyPolicy.normalize("\u2000a\r\n b\u3000"))
        assertEquals(1, BodyPolicy.count("한"))
        assertEquals(1, BodyPolicy.count("👩🏽‍💻"))
        assertEquals(1, BodyPolicy.count("🇰🇷"))
        assertFalse(BodyPolicy.valid("\uD800"))
    }
    private class Store : AttemptStore {
        var value: Attempt? = null; var failSave = false; var failClear = false
        override fun load() = value
        override fun save(attempt: Attempt) { check(!failSave); value = attempt }
        override fun clear() { check(!failClear); value = null }
    }
    @Test fun durableBeforeSendAndSameKeyAfterRestart() {
        val store = Store(); val state = SaveMachine(store)
        val request = state.begin("key", " body ")
        assertEquals(Attempt("key", "body"), store.value)
        assertFails { state.begin("new", "body") }
        val restart = SaveMachine(store)
        assertEquals(SavePhase.UNCERTAIN, restart.phase)
        assertEquals(request, restart.retry())
        restart.uncertain(); assertEquals(request, restart.retry())
        restart.complete(); assertNull(store.value)
    }
    @Test fun persistenceFailuresNeverPermitUnsafeSendOrNewKey() {
        val store = Store(); val state = SaveMachine(store); store.failSave = true
        assertFails { state.begin("key", "text") }; assertNull(state.attempt)
        store.failSave = false; state.begin("key", "text"); store.failClear = true
        assertFails { state.complete() }; assertTrue(state.locked)
        assertEquals("key", state.attempt?.id)
    }
}

package memo.client

import memo.domain.BodyPolicy

/** Side effects are injected. Persistence MUST succeed before begin returns a request. */
interface AttemptStore {
    fun load(): Attempt?
    fun save(attempt: Attempt)
    fun clear()
}
data class Attempt(val id: String, val body: String)
enum class SavePhase { EDITING, SAVING, UNCERTAIN }
class SaveMachine(private val store: AttemptStore) {
    var attempt: Attempt? = store.load(); private set
    var phase = if (attempt == null) SavePhase.EDITING else SavePhase.UNCERTAIN; private set
    val locked: Boolean get() = phase != SavePhase.EDITING
    fun begin(id: String, body: String): Attempt {
        check(!locked) { "Unresolved attempt" }
        require(BodyPolicy.valid(body)) { "Invalid body" }
        val next = Attempt(id, BodyPolicy.normalize(body))
        store.save(next)
        attempt = next; phase = SavePhase.SAVING
        return next
    }
    fun retry(): Attempt {
        check(phase == SavePhase.UNCERTAIN)
        val current = checkNotNull(attempt)
        phase = SavePhase.SAVING
        return current
    }
    fun uncertain() { check(attempt != null); phase = SavePhase.UNCERTAIN }
    fun complete() {
        check(attempt != null)
        // Failed cleanup must keep the same key locked. No new attempt may be created.
        try { store.clear() } catch (failure: Exception) { phase = SavePhase.UNCERTAIN; throw failure }
        attempt = null; phase = SavePhase.EDITING
    }
    fun definitelyNotSaved() = complete()
}

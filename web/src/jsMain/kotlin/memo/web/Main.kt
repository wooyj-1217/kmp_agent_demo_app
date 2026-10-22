package memo.web

import kotlinx.browser.document
import kotlinx.browser.window
import kotlinx.serialization.*
import memo.api.*
import memo.client.*
import memo.domain.BodyPolicy
import org.w3c.dom.*
import org.w3c.dom.events.Event

private const val PENDING_KEY = "memo.v1.pending-attempt"
private class BrowserAttempts : AttemptStore {
    private var owner: String? = null
    override fun load(): Attempt? = window.localStorage.getItem(PENDING_KEY)?.let {
        val req = wireJson.decodeFromString<SaveRequest>(it)
        require(req.attemptId.matches(Regex("[0-9a-f-]{36}")) && BodyPolicy.valid(req.body))
        owner = req.attemptId
        Attempt(req.attemptId, req.body)
    }
    override fun save(attempt: Attempt) {
        check(load() == null) { "Another unresolved attempt exists" }
        window.localStorage.setItem(PENDING_KEY, wireJson.encodeToString(SaveRequest(attempt.id, attempt.body)))
        owner = attempt.id
    }
    override fun clear() {
        val raw = window.localStorage.getItem(PENDING_KEY)
        if (raw != null) check(wireJson.decodeFromString<SaveRequest>(raw).attemptId == owner)
        window.localStorage.removeItem(PENDING_KEY)
    }
}

private class MemoApp {
    private val root = document.getElementById("app")!!
    private val store = BrowserAttempts()
    private var machine = SaveMachine(store)
    private var body = machine.attempt?.body ?: ""
    private var composing = machine.locked || window.location.hash == "#create"
    private var notes = emptyList<Memo>()
    private var listState = "loading"
    private var message = ""
    private var loadSerial = 0
    private var busy = false
    private fun escape(text: String) = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\"", "&quot;").replace("'", "&#39;")
    init {
        window.addEventListener("hashchange", {
            val wantsCreate = window.location.hash == "#create"
            if (machine.locked) { composing = true; if (!wantsCreate) window.location.hash = "create" }
            else if (composing && !wantsCreate && body.isNotEmpty() && !window.confirm("작성 중인 메모를 닫을까요? 저장하지 않은 내용은 사라집니다.")) window.location.hash = "create"
            else { composing = wantsCreate; if (!wantsCreate) body = "" }
            render()
        })
        window.addEventListener("beforeunload", { e -> if (!machine.locked && composing && body.isNotEmpty()) { e.preventDefault(); e.asDynamic().returnValue = "" } })
        window.addEventListener("storage", {
            if (!busy) {
                machine = SaveMachine(store)
                if (machine.locked) { composing = true; body = machine.attempt!!.body }
                render()
            }
        })
        render(); loadList()
    }
    private fun withAttemptLock(action: () -> Unit) {
        val locks = window.navigator.asDynamic().locks
        if (locks == null) { message="이 브라우저에서는 안전한 저장을 지원하지 않아요."; render(); return }
        locks.request("memo-v1-save-attempt", { _: dynamic -> action() })
    }
    private fun announce(text: String) { document.getElementById("announcer")!!.textContent = text }
    private fun render() {
        root.setAttribute("data-screen-id", if (composing) "SCREEN-CREATE" else "SCREEN-LIST")
        root.setAttribute("data-state-id", if (composing) machine.phase.name else listState)
        val failedNotice=message.contains("저장되지 않았어요") || message.startsWith("저장 시도 정보를")
        val noticeTone=if(failedNotice) "error" else if(machine.phase == SavePhase.UNCERTAIN) "warning" else ""
        val notice = if (message.isNotEmpty() && machine.phase != SavePhase.UNCERTAIN) "<div class='message notice $noticeTone' role='${if(failedNotice) "alert" else "status"}'>${if(busy) "<span class='spinner' aria-hidden='true'></span>" else ""}${escape(message)}</div>" else ""
        if (composing) {
            val uncertain = machine.phase == SavePhase.UNCERTAIN
            root.innerHTML = """
                <header class='header'><div class='topline'><button id='back' class='back' ${if (machine.locked) "disabled" else ""}>‹ 목록</button><span class='badge'>새로운 기록</span></div><h1 tabindex='-1'>새 메모</h1><p class='subtitle'>떠오른 생각을 잊기 전에.</p></header>
                <section class='scroll' aria-label='메모 작성'>
                $notice
                ${if (uncertain) "<div class='notice warning' role='alert'><strong>저장 결과를 확인하지 못했어요.</strong>중복 저장을 막기 위해 편집을 잠시 잠갔어요.<button id='retry'>같은 저장 결과 다시 확인</button></div>" else ""}
                <label class='editor-label' for='body'>메모 본문</label><textarea placeholder='오늘 기억하고 싶은 것은 무엇인가요?' id='body' class='editor' aria-describedby='body-count body-error' ${if (machine.locked) "readonly" else ""}>${escape(body)}</textarea><div class='input-meta'><span id='body-count' class='count'></span></div><p id='body-error' class='field-error' hidden></p><p class='editor-hint'>짧은 문장도, 여러 줄의 생각도 좋아요.<br>저장이 완료되면 메모 목록으로 돌아가요.</p></section>
                <footer class='footer'><button id='save' class='primary'>${if (busy) "<span class='spinner' aria-hidden='true'></span>저장 중…" else if (uncertain) "저장 결과 확인 필요" else if(failedNotice) "다시 저장" else "메모 저장"}</button><p id='save-caption' class='footer-caption'></p></footer>
            """ // Never trim template indentation across an interpolated user body.
            root.querySelector("#body")!!.addEventListener("input", { e ->
                body = (e.target as HTMLTextAreaElement).value
                if (!machine.locked && message.startsWith("메모가 저장되지 않았어요.")) {
                    message=""; root.querySelector(".message")?.remove()
                }
                updateInput(true)
            })
            root.querySelector("#back")!!.addEventListener("click", { if (!machine.locked && (body.isEmpty() || window.confirm("작성 중인 메모를 닫을까요? 저장하지 않은 내용은 사라집니다."))) { body=""; composing=false; window.location.hash=""; render() } })
            root.querySelector("#save")!!.addEventListener("click", { startSave() })
            root.querySelector("#retry")?.addEventListener("click", { retry() })
            updateInput(false)
        } else {
            val content = when (listState) {
                "loading" -> "<div class='center-state' role='status'>메모를 불러오고 있어요.</div>"
                "error" -> "<div class='center-state' role='alert'>메모를 불러오지 못했어요.<button id='reload'>다시 불러오기</button></div>"
                else -> {
                    val warning = if (listState == "refresh-error") "<div class='notice warning' role='alert'>목록 갱신 실패 · 이미 저장된 메모는 유지돼요.<button id='reload'>목록만 다시 불러오기</button></div>" else if (listState == "refreshing") "<p role='status'>목록을 갱신하고 있어요.</p>" else ""
                    warning + if (notes.isEmpty()) "<div class='center-state'>첫 생각을 남겨볼까요?<p>아직 메모가 없어요.</p></div>" else "<div class='list-meta'>메모 ${notes.size}개 <span>최신순</span></div><ul class='notes'>" + notes.joinToString("") { "<li class='note' data-memo-id='${escape(it.id)}'><p class='note-body'>${escape(it.body)}</p><time>${escape(it.createdAt)}</time></li>" } + "</ul>"
                }
            }
            root.innerHTML = "<header class='header'><div class='topline'><span class='wordmark'>memo.</span><span class='badge'>나의 기록</span></div><div class='title-row'><h1 tabindex='-1'>메모장</h1><button id='refresh' class='quiet' ${if (listState in listOf("loading","refreshing")) "disabled" else ""}>새로고침</button></div><p class='subtitle'>생각이 머무는 작은 공간.</p></header>$notice<section class='scroll' aria-label='메모 목록'>$content</section><footer class='footer'><button id='create' class='primary'>＋ 새 메모 작성</button><p class='footer-caption'>기억하고 싶은 순간을 적어보세요.</p></footer>"
            root.querySelector("#create")!!.addEventListener("click", { composing=true; body=""; message=""; announce(""); window.location.hash="create"; render() })
            root.querySelector("#refresh")!!.addEventListener("click", { loadList() })
            root.querySelector("#reload")?.addEventListener("click", { loadList() })
        }
        (root.querySelector("h1") as? HTMLElement)?.focus()
    }
    private fun updateInput(touched: Boolean) {
        val count = runCatching { BodyPolicy.count(body) }.getOrDefault(-1)
        val invalid = count !in 1..2000
        root.querySelector("#body-count")!!.innerHTML = "<span style='${if (count > 2000) "color:var(--error);font-weight:bold" else ""}'>${if(count<0) "—" else count.toString()}</span> / 2,000"
        (root.querySelector("#save") as HTMLButtonElement).disabled = machine.locked || invalid || busy
        if(!machine.locked && !busy)(root.querySelector("#save") as HTMLButtonElement).textContent=if(message.contains("저장되지 않았어요")) "다시 저장" else "메모 저장"
        root.querySelector("#save-caption")?.textContent=if(machine.locked) "저장 결과가 확인될 때까지 내용이 유지돼요." else if(!invalid) "서버의 저장 완료를 확인한 뒤 목록에 반영해요." else ""
        val error = root.querySelector("#body-error") as HTMLElement
        error.hidden = !invalid || (!touched && body.isEmpty())
        error.textContent = if (count > 2000) "2,000자 이내로 줄여주세요." else "본문을 입력해주세요. 공백만으로는 저장할 수 없어요."
        root.querySelector("#body")!!.setAttribute("aria-invalid", (!error.hidden).toString())
    }
    private fun loadList() {
        val serial = ++loadSerial
        listState = if (notes.isEmpty()) "loading" else "refreshing"
        render()
        http("GET", "/api/v1/memos") { status, text ->
            if (serial != loadSerial) return@http
            val result = if (status==200) runCatching { wireJson.decodeFromString<MemoList>(text).memos }.getOrNull() else null
            if (result != null) { notes = (result + notes).distinctBy { it.id }.sortedWith(compareByDescending<Memo> { it.createdAt }.thenByDescending { it.id }); listState="normal" }
            else listState=if(notes.isEmpty()) "error" else "refresh-error"
            render()
        }
    }
    private fun startSave() {
        if (busy || machine.locked || !BodyPolicy.valid(body)) return
        // Web Locks serialize the compare-and-persist step across tabs of this origin.
        val locks = window.navigator.asDynamic().locks
        if (locks == null) { message="이 브라우저에서는 안전한 저장을 지원하지 않아요."; render(); return }
        withAttemptLock {
            try {
                val request = machine.begin(window.asDynamic().crypto.randomUUID() as String, body)
                send(request)
            } catch (_: Exception) { message="저장 시도 정보를 보존하지 못했어요. 본문은 유지돼요."; render() }
        }
    }
    private fun retry() {
        if (busy || machine.phase != SavePhase.UNCERTAIN) return
        val attempt = machine.retry(); busy=true; message="같은 저장 결과를 확인하고 있어요."; render()
        http("GET", "/api/v1/attempts/${attempt.id}") { status,text ->
            if (status==200) success(text)
            else if (status==404) { busy=false; send(attempt) }
            else uncertain()
        }
    }
    private fun send(attempt: Attempt) {
        busy=true; message="저장 결과를 기다리고 있어요."; render()
        http("POST", "/api/v1/memos", wireJson.encodeToString(SaveRequest(attempt.id, attempt.body))) { status, text ->
            when (status) {
                200,201 -> success(text)
                422,413 -> {
                    busy=false
                    withAttemptLock {
                        try { machine.definitelyNotSaved(); message="메모가 저장되지 않았어요. 본문을 확인하고 다시 저장해주세요." }
                        catch (_: Exception) { machine.uncertain(); message="복구 정보를 정리하지 못했어요. 같은 시도를 다시 확인해주세요." }
                        render()
                    }
                }
                else -> uncertain()
            }
        }
    }
    private fun success(text: String) {
        busy=false
        withAttemptLock { try {
            val memo = wireJson.decodeFromString<MemoResult>(text).memo
            machine.complete()
            notes = (listOf(memo) + notes).distinctBy { it.id }.sortedWith(compareByDescending<Memo> { it.createdAt }.thenByDescending { it.id })
            body=""; composing=false; message="메모를 저장했어요."; window.location.hash=""; announce(message); loadList()
        } catch (_: Exception) { uncertain() } }
    }
    private fun uncertain() { busy=false; machine.uncertain(); body=machine.attempt!!.body; composing=true; message="저장 결과가 불확실해요. 같은 시도를 다시 확인해주세요."; render() }
}

private fun http(method: String, path: String, payload: String? = null, done: (Int,String)->Unit) {
    val controller: dynamic = js("new AbortController()")
    val options: dynamic = js("({})"); options.method=method; options.signal=controller.signal
    if (payload!=null) { options.headers=js("({'Content-Type':'application/json'})"); options.body=payload }
    var finished=false
    val timeout=window.setTimeout({ controller.abort() },15000)
    fun finish(status: Int,text: String) { if (!finished) { finished=true; window.clearTimeout(timeout); done(status,text) } }
    window.asDynamic().fetch(path,options).then({ response: dynamic -> response.text().then({ text: dynamic -> finish(response.status as Int,text as String) }) }).catch({ _: dynamic -> finish(0,"") })
}

fun main() {
    try { MemoApp() }
    catch (_: Exception) {
        document.getElementById("app")!!.innerHTML="<h1>저장 시도 복구 정보를 읽지 못했어요.</h1><p>중복 저장을 막기 위해 새 저장을 중단했어요. 기존 브라우저 저장 정보를 보존하고 다시 시도해주세요.</p>"
    }
}

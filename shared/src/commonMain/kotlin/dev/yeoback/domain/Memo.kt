package dev.yeoback.domain

data class Memo(
    val id: String,
    val title: String,
    val body: String,
    val pinned: Boolean,
    val createdAt: Long,
    val updatedAt: Long,
    val deletedAt: Long? = null,
) {
    val displayTitle: String get() = title.takeIf { it.isNotBlank() } ?: "제목 없는 메모"
}

/** A successful write must durably replace the complete value; failures must throw. */
interface MemoStorage {
    fun read(): String?
    fun write(value: String)
}

class MemoRepository(
    private val storage: MemoStorage,
    private val now: () -> Long,
    private val nextId: () -> String,
) {
    var memos: List<Memo> = emptyList()
        private set

    init { reload() }

    fun reload() {
        val loaded = storage.read()?.let(MemoCodec::decode) ?: emptyList()
        memos = loaded
    }

    fun save(id: String?, title: String, body: String): Memo {
        require(title.isNotBlank() || body.isNotBlank()) { "메모 내용을 입력해 주세요." }
        val memo = if (id == null) {
            val newId = nextId()
            require(newId.isNotBlank() && memos.none { it.id == newId }) { "메모 ID가 올바르지 않습니다." }
            val time = now()
            Memo(newId, title, body, false, time, time)
        } else {
            val previous = find(id)
            require(previous.deletedAt == null) { "휴지통의 메모는 편집할 수 없습니다." }
            previous.copy(title = title, body = body, updatedAt = now())
        }
        commit(if (id == null) memos + memo else memos.map { if (it.id == id) memo else it })
        return memo
    }

    fun pin(id: String) {
        val memo = find(id)
        require(memo.deletedAt == null) { "휴지통의 메모는 고정할 수 없습니다." }
        replace(memo.copy(pinned = !memo.pinned))
    }

    fun trash(id: String) {
        val memo = find(id)
        require(memo.deletedAt == null) { "이미 휴지통에 있는 메모입니다." }
        replace(memo.copy(deletedAt = now()))
    }

    fun restore(id: String) {
        val memo = find(id)
        require(memo.deletedAt != null) { "휴지통의 메모만 복원할 수 있습니다." }
        replace(memo.copy(deletedAt = null))
    }

    fun deleteForever(id: String) {
        require(find(id).deletedAt != null) { "휴지통의 메모만 영구 삭제할 수 있습니다." }
        commit(memos.filterNot { it.id == id })
    }

    fun visible(query: String = "", pinnedOnly: Boolean = false, trash: Boolean = false): List<Memo> {
        val term = query.trim()
        val filtered = memos.filter {
            (it.deletedAt != null) == trash && (!pinnedOnly || it.pinned) &&
                (term.isEmpty() || it.title.contains(term, ignoreCase = true) || it.body.contains(term, ignoreCase = true))
        }
        return if (trash) filtered.sortedWith(compareByDescending<Memo> { it.deletedAt }.thenBy { it.id })
        else filtered.sortedWith(compareByDescending<Memo> { it.pinned }.thenByDescending { it.updatedAt }.thenBy { it.id })
    }

    private fun find(id: String): Memo = requireNotNull(memos.find { it.id == id }) { "메모를 찾을 수 없습니다." }
    private fun replace(memo: Memo) = commit(memos.map { if (it.id == memo.id) memo else it })
    private fun commit(updated: List<Memo>) {
        storage.write(MemoCodec.encode(updated))
        memos = updated
    }
}

/** Version 1: UTF-16 String lengths, allowing every character including delimiters. */
object MemoCodec {
    private const val HEADER = "YEOBACK:1:"

    fun encode(memos: List<Memo>): String {
        validate(memos)
        return buildString {
            append(HEADER)
            field(memos.size.toString())
            for (memo in memos) {
                field(memo.id)
                field(memo.title)
                field(memo.body)
                field(if (memo.pinned) "1" else "0")
                field(memo.createdAt.toString())
                field(memo.updatedAt.toString())
                field(memo.deletedAt?.toString() ?: "")
            }
        }
    }

    fun decode(value: String): List<Memo> {
        require(value.startsWith(HEADER)) { "지원하지 않거나 손상된 저장 형식입니다." }
        val reader = Reader(value, HEADER.length)
        val count = reader.field().toIntOrNull()
        require(count != null && count >= 0 && count <= value.length / 14) { "잘못된 메모 개수입니다." }
        val result = List(count) {
            val id = reader.field()
            val title = reader.field()
            val body = reader.field()
            val pinned = when (reader.field()) { "1" -> true; "0" -> false; else -> error("잘못된 고정 값입니다.") }
            val createdAt = requireNotNull(reader.field().toLongOrNull()) { "잘못된 생성 시각입니다." }
            val updatedAt = requireNotNull(reader.field().toLongOrNull()) { "잘못된 수정 시각입니다." }
            val deleted = reader.field()
            val deletedAt = if (deleted.isEmpty()) null else requireNotNull(deleted.toLongOrNull()) { "잘못된 삭제 시각입니다." }
            Memo(id, title, body, pinned, createdAt, updatedAt, deletedAt)
        }
        require(reader.finished()) { "저장 데이터 뒤에 알 수 없는 값이 있습니다." }
        validate(result)
        return result
    }

    private fun validate(memos: List<Memo>) {
        require(memos.all { it.id.isNotBlank() && (it.title.isNotBlank() || it.body.isNotBlank()) }) { "잘못된 메모입니다." }
        require(memos.map { it.id }.toSet().size == memos.size) { "중복된 메모 ID입니다." }
    }

    private fun StringBuilder.field(value: String) { append(value.length); append(':'); append(value) }

    private class Reader(private val value: String, private var offset: Int) {
        fun field(): String {
            val separator = value.indexOf(':', offset)
            require(separator > offset) { "저장 필드 길이가 없습니다." }
            val digits = value.substring(offset, separator)
            require(digits.all { it in '0'..'9' }) { "잘못된 저장 필드 길이입니다." }
            val length = requireNotNull(digits.toIntOrNull()) { "저장 필드 길이가 너무 큽니다." }
            val start = separator + 1
            require(length <= value.length - start) { "저장 데이터가 잘렸습니다." }
            offset = start + length
            return value.substring(start, offset)
        }
        fun finished() = offset == value.length
    }
}

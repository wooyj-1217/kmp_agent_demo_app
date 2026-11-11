package dev.yeoback.domain

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFails
import kotlin.test.assertFalse
import kotlin.test.assertTrue

class MemoTest {
    private class Storage(var value: String? = null) : MemoStorage {
        var failRead = false
        var failWrite = false
        var writes = 0
        override fun read(): String? { check(!failRead); return value }
        override fun write(value: String) { check(!failWrite); this.value = value; writes++ }
    }

    private class Fixture {
        val storage = Storage()
        var time = 100L
        var sequence = 0
        val repo = MemoRepository(storage, { time }, { "id-${++sequence}" })
    }

    @Test fun acceptanceUniqueMemoSurvivesRepositoryRestart() {
        val storage = Storage()
        val token = kotlin.random.Random.nextLong().toString()
        val title = "acceptance-title-$token"
        val body = "acceptance-body-$token\nrestored exactly"
        MemoRepository(storage, { 1L }, { token }).save(null, title, body)
        val restored = MemoRepository(storage, { 2L }, { "unused" }).memos.single()
        assertEquals(title, restored.title)
        assertEquals(body, restored.body)
    }

    @Test fun unicodeAndDelimitersSurviveRestartAndEdit() {
        val f = Fixture()
        val title = "  여백 📝:0\n "
        val body = "\u0000본문 👩🏽‍💻\n둘째 줄: 42\r\n끝  "
        val memo = f.repo.save(null, title, body)
        val restarted = MemoRepository(f.storage, { 200L }, { "another" })
        assertEquals(memo, restarted.memos.single())
        val edited = restarted.save(memo.id, "", body)
        assertEquals("제목 없는 메모", edited.displayTitle)
        assertEquals(body, edited.body)
        assertEquals(100L, edited.createdAt)
        assertEquals(200L, edited.updatedAt)
        assertEquals(1, restarted.memos.size)
    }

    @Test fun blankUnknownAndCollidingIdsNeverWrite() {
        val s = Storage()
        val r = MemoRepository(s, { 1L }, { "same" })
        assertFails { r.save(null, " \n", "\t") }
        r.save(null, "title", "")
        assertFails { r.save(null, "collision", "") }
        assertFails { r.save("missing", "unknown", "") }
        assertFails { r.deleteForever("same") }
        assertEquals(1, s.writes)
    }

    @Test fun everyMutationIsTransactionalAndRetryable() {
        val f = Fixture()
        val memo = f.repo.save(null, "원문", "본문")
        fun failure(action: () -> Unit) {
            val before = f.repo.memos.toList()
            val disk = f.storage.value
            f.storage.failWrite = true
            assertFails(action)
            assertEquals(before, f.repo.memos)
            assertEquals(disk, f.storage.value)
            f.storage.failWrite = false
        }
        failure { f.repo.save(null, "new", "") }
        failure { f.repo.save(memo.id, "수정", "") }
        f.repo.save(memo.id, "수정", "")
        failure { f.repo.pin(memo.id) }
        f.repo.pin(memo.id)
        failure { f.repo.trash(memo.id) }
        f.repo.trash(memo.id)
        failure { f.repo.restore(memo.id) }
        f.repo.restore(memo.id)
        f.repo.trash(memo.id)
        failure { f.repo.deleteForever(memo.id) }
        f.repo.deleteForever(memo.id)
        assertTrue(f.repo.memos.isEmpty())
        assertTrue(MemoRepository(f.storage, { 0 }, { "x" }).memos.isEmpty())
    }

    @Test fun trashRestorePreserveMetadataAndRestrictOperations() {
        val f = Fixture()
        val memo = f.repo.save(null, "보존", "원문")
        f.repo.pin(memo.id)
        val pinned = f.repo.memos.single()
        f.time = 500
        f.repo.trash(memo.id)
        assertTrue(f.repo.visible().isEmpty())
        assertEquals(500L, f.repo.visible(trash = true).single().deletedAt)
        assertFails { f.repo.save(memo.id, "편집", "") }
        assertFails { f.repo.pin(memo.id) }
        assertFails { f.repo.trash(memo.id) }
        f.repo.restore(memo.id)
        assertEquals(pinned, f.repo.memos.single())
        assertFails { f.repo.restore(memo.id) }
    }

    @Test fun searchAndStableOrderingRespectActiveAndTrashGroups() {
        val s = Storage()
        val r = MemoRepository(s, { 5L }, listOf("z", "b", "a").iterator()::next)
        val z = r.save(null, "Alpha", "한글 본문")
        val b = r.save(null, "Beta", "alpha beta")
        val a = r.save(null, "Gamma", "ALPHA")
        assertEquals(listOf("a", "b", "z"), r.visible().map { it.id })
        r.pin(z.id)
        assertEquals(listOf("z", "a", "b"), r.visible(" alpha ").map { it.id })
        assertEquals(listOf(z), r.visible(pinnedOnly = true).map { it.copy(pinned = false) })
        assertEquals(listOf(b), r.visible("alpha beta"))
        assertTrue(r.visible("없음").isEmpty())
        r.trash(a.id)
        r.trash(b.id)
        assertEquals(listOf("a", "b"), r.visible(trash = true).map { it.id })
        assertEquals(listOf("z"), r.visible("한글").map { it.id })
        assertFalse(r.visible().any { it.id == a.id })
    }

    @Test fun corruptLoadNeverWritesAndReloadFailurePreservesMemory() {
        val f = Fixture()
        val memo = f.repo.save(null, "safe", "")
        val good = f.storage.value!!
        for (bad in listOf("", "YEOBACK:2:1:0", good.dropLast(1), good + "junk", "YEOBACK:1:1:91:x")) {
            f.storage.value = bad
            val writes = f.storage.writes
            assertFails { MemoRepository(f.storage, { 0 }, { "x" }) }
            assertFails { f.repo.reload() }
            assertEquals(listOf(memo), f.repo.memos)
            assertEquals(writes, f.storage.writes)
        }
        f.storage.failRead = true
        assertFails { f.repo.reload() }
        assertEquals(listOf(memo), f.repo.memos)
        f.storage.failRead = false
        f.storage.value = good
        f.repo.reload()
        assertEquals(listOf(memo), f.repo.memos)
    }

    @Test fun codecRejectsDuplicateIdsInvalidBooleanAndOverflow() {
        val memo = Memo("id", "title", "", false, 1, 1)
        assertFails { MemoCodec.encode(listOf(memo, memo)) }
        val encoded = MemoCodec.encode(listOf(memo))
        assertFails { MemoCodec.decode(encoded.replace("1:0", "1:9")) }
        assertFails { MemoCodec.decode("YEOBACK:1:999999999999999999999:x") }
        assertEquals(emptyList(), MemoCodec.decode(MemoCodec.encode(emptyList())))
    }

    @Test fun recentEditsAndDeletionTimesDetermineOrderAcrossRestart() {
        val f = Fixture()
        val first = f.repo.save(null, "first", "")
        f.time = 200
        val second = f.repo.save(null, "second", "")
        assertEquals(listOf(second.id, first.id), f.repo.visible().map { it.id })
        f.time = 300
        f.repo.save(first.id, "edited", "")
        assertEquals(listOf(first.id, second.id), f.repo.visible().map { it.id })
        f.time = 400
        f.repo.trash(first.id)
        f.time = 500
        f.repo.trash(second.id)
        val reopened = MemoRepository(f.storage, { 600 }, { "next" })
        assertEquals(listOf(second.id, first.id), reopened.visible(trash = true).map { it.id })
        assertEquals(300L, reopened.memos.first { it.id == first.id }.updatedAt)
    }
}

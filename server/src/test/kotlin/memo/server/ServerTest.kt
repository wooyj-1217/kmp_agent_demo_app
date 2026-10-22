package memo.server

import kotlin.test.*
import memo.api.*
import kotlinx.serialization.*
import java.nio.file.Files
import java.net.URI
import java.net.http.*
import java.time.Clock
import java.time.Instant
import java.time.ZoneOffset
import java.util.UUID
import java.util.concurrent.Callable
import java.util.concurrent.Executors

class ServerTest {
    private fun key() = UUID.randomUUID().toString()
    @Test fun atomicReplayRestartAndIndependentIdenticalBodies() {
        val file = Files.createTempDirectory("memo-test-").resolve("memos.db")
        val clock = Clock.fixed(Instant.parse("2026-10-20T10:00:00Z"), ZoneOffset.UTC)
        val store = MemoStore(file, clock); val request = SaveRequest(key(), " body\nsecond line ")
        val pool = Executors.newFixedThreadPool(8)
        try {
            val results = pool.invokeAll((1..24).map { Callable { MemoStore(file, clock).save(request) } }).map { it.get() }
            assertEquals(1, results.count { it.created }); assertEquals(1, results.map { it.memo.id }.distinct().size)
        } finally { pool.shutdownNow() }
        val restart = MemoStore(file, clock)
        assertEquals(1, restart.list().size); assertFalse(restart.save(request).created)
        assertEquals("body\nsecond line", restart.list().single().body)
        val another = restart.save(request.copy(attemptId = key()))
        assertEquals(another.memo.id, restart.list().first().id)
        assertEquals(restart.list(), restart.list())
        val conflict = assertFailsWith<ContractFailure> { restart.save(request.copy(body="different")) }
        assertEquals(409, conflict.status); assertEquals(2, restart.list().size)
    }
    @Test fun actualHttpPersistenceValidationAndLookup() {
        val file = Files.createTempDirectory("memo-http-").resolve("memos.db")
        val request = SaveRequest(key(), "👩🏽‍💻".repeat(2000))
        val client = HttpClient.newHttpClient()
        fun post(port: Int, body: String): HttpResponse<String> = client.send(HttpRequest.newBuilder(URI("http://127.0.0.1:$port/api/v1/memos")).header("Content-Type","application/json").POST(HttpRequest.BodyPublishers.ofString(body)).build(), HttpResponse.BodyHandlers.ofString())
        var id = ""
        MemoServer(MemoStore(file), 0).use { server ->
            assertEquals(422, post(server.port, "bad json").statusCode())
            assertEquals(422, post(server.port, wireJson.encodeToString(request.copy(body=" "))).statusCode())
            assertEquals(422, post(server.port, wireJson.encodeToString(request.copy(body="가".repeat(2001)))).statusCode())
            assertEquals(413, post(server.port, "a".repeat(131073)).statusCode())
            val saved = post(server.port, wireJson.encodeToString(request)); assertEquals(201, saved.statusCode())
            id = wireJson.decodeFromString<MemoResult>(saved.body()).memo.id
            assertEquals(200, post(server.port, wireJson.encodeToString(request)).statusCode())
        }
        MemoServer(MemoStore(file), 0).use { server ->
            val replay = post(server.port, wireJson.encodeToString(request))
            assertEquals(200, replay.statusCode()); assertEquals(id, wireJson.decodeFromString<MemoResult>(replay.body()).memo.id)
            val lookup = client.send(HttpRequest.newBuilder(URI("http://127.0.0.1:${server.port}/api/v1/attempts/${request.attemptId}")).build(), HttpResponse.BodyHandlers.ofString())
            assertEquals(id, wireJson.decodeFromString<MemoResult>(lookup.body()).memo.id)
            assertEquals(1, MemoStore(file).list().size)
        }
    }
    @Test fun lostResponseCanReplayAfterServerRestart() {
        val file = Files.createTempDirectory("memo-loss-").resolve("memos.db")
        val req = SaveRequest(key(), "response may be lost")
        MemoServer(MemoStore(file),0).use { server ->
            val body = wireJson.encodeToString(req).toByteArray()
            java.net.Socket("127.0.0.1",server.port).use { socket ->
                socket.getOutputStream().write(("POST /api/v1/memos HTTP/1.1\r\nHost: localhost\r\nContent-Length: ${body.size}\r\nConnection: close\r\n\r\n").toByteArray()+body)
                socket.getOutputStream().flush()
                // Read only response headers, proving commit but intentionally discard the result body.
                assertTrue(socket.getInputStream().bufferedReader().readLine().contains("201"))
            }
        }
        val restarted = MemoStore(file)
        assertFalse(restarted.save(req).created); assertEquals(1, restarted.list().size)
    }
    @Test fun unknownSchemaIsNotDestroyed() {
        val file=Files.createTempDirectory("memo-schema-").resolve("memos.db")
        java.sql.DriverManager.getConnection("jdbc:sqlite:$file").use { c -> c.createStatement().use { it.execute("PRAGMA user_version=99") } }
        assertFailsWith<IllegalArgumentException> { MemoStore(file) }
    }
}

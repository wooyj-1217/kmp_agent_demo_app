package memo.server

import com.sun.net.httpserver.HttpExchange
import com.sun.net.httpserver.HttpServer
import kotlinx.serialization.*
import memo.api.*
import java.net.InetSocketAddress
import java.nio.ByteBuffer
import java.nio.charset.CodingErrorAction
import java.nio.file.Files
import java.nio.file.Path
import java.util.concurrent.Executors

class MemoServer(private val store: MemoStore, port: Int = 8080, webRoot: Path? = null) : AutoCloseable {
    private val root = webRoot?.toAbsolutePath()?.normalize()
    private val executor = Executors.newFixedThreadPool(4)
    private val http = HttpServer.create(InetSocketAddress("127.0.0.1", port), 0)
    val port: Int get() = http.address.port
    init {
        http.executor = executor
        http.createContext("/") { request ->
            request.use { exchange ->
                try { route(exchange) }
                catch (failure: ContractFailure) { error(exchange, failure.status, failure.code) }
                catch (_: SerializationException) { error(exchange, 422, "MALFORMED_JSON") }
                catch (_: Exception) { runCatching { error(exchange, 500, "INTERNAL_ERROR") } }
            }
        }
        http.start()
    }
    private fun route(exchange: HttpExchange) {
        val path = exchange.requestURI.path
        if (path == "/api/v1/memos") {
            when (exchange.requestMethod) {
                "GET" -> json(exchange, 200, wireJson.encodeToString(MemoList(store.list())))
                "POST" -> {
                    val bytes = exchange.requestBody.readNBytes(128 * 1024 + 1)
                    if (bytes.size > 128 * 1024) throw ContractFailure(413, "REQUEST_TOO_LARGE")
                    val text = try { Charsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(bytes)).toString() }
                    catch (_: Exception) { throw ContractFailure(422, "MALFORMED_JSON") }
                    val saved = store.save(wireJson.decodeFromString<SaveRequest>(text))
                    json(exchange, if (saved.created) 201 else 200, wireJson.encodeToString(MemoResult(saved.memo)))
                }
                else -> throw ContractFailure(405, "METHOD_NOT_ALLOWED")
            }
        } else if (path.startsWith("/api/v1/attempts/")) {
            if (exchange.requestMethod != "GET") throw ContractFailure(405, "METHOD_NOT_ALLOWED")
            val memo = store.find(path.removePrefix("/api/v1/attempts/")) ?: throw ContractFailure(404, "ATTEMPT_NOT_FOUND")
            json(exchange, 200, wireJson.encodeToString(MemoResult(memo)))
        } else if (path.startsWith("/api/")) throw ContractFailure(404, "NOT_FOUND")
        else {
            if (exchange.requestMethod != "GET") throw ContractFailure(405, "METHOD_NOT_ALLOWED")
            val base = root ?: throw ContractFailure(404, "NOT_FOUND")
            val file = base.resolve(if (path == "/") "index.html" else path.removePrefix("/")).normalize()
            if (!file.startsWith(base) || !Files.isRegularFile(file) || !file.toRealPath().startsWith(base.toRealPath())) throw ContractFailure(404, "NOT_FOUND")
            val contentType = when (file.fileName.toString().substringAfterLast('.')) {
                "html" -> "text/html; charset=utf-8"; "js" -> "application/javascript; charset=utf-8"; "css" -> "text/css; charset=utf-8"; "map" -> "application/json"; else -> "application/octet-stream"
            }
            send(exchange, 200, Files.readAllBytes(file), contentType)
        }
    }
    private fun json(exchange: HttpExchange, status: Int, body: String) = send(exchange, status, body.toByteArray(Charsets.UTF_8), "application/json; charset=utf-8")
    private fun error(exchange: HttpExchange, status: Int, code: String) = json(exchange, status, wireJson.encodeToString(ApiError(code, code)))
    private fun send(exchange: HttpExchange, status: Int, bytes: ByteArray, contentType: String) {
        exchange.responseHeaders.set("Content-Type", contentType)
        exchange.responseHeaders.set("Cache-Control", "no-store")
        exchange.responseHeaders.set("X-Content-Type-Options", "nosniff")
        exchange.sendResponseHeaders(status, bytes.size.toLong())
        exchange.responseBody.use { it.write(bytes) }
    }
    override fun close() { http.stop(0); executor.shutdownNow() }
}

fun main() {
    val store = MemoStore(Path.of(System.getenv("MEMO_DB") ?: "data/memos.db"))
    val server = MemoServer(store, System.getenv("MEMO_PORT")?.toInt() ?: 8080, System.getenv("MEMO_WEB_ROOT")?.let(Path::of))
    Runtime.getRuntime().addShutdownHook(Thread { server.close() })
    println("Memo API: http://127.0.0.1:${server.port}; SQLite persistence enabled")
}

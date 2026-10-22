package memo.server

import memo.api.*
import memo.domain.BodyPolicy
import java.nio.file.Path
import java.sql.Connection
import java.sql.DriverManager
import java.time.Clock
import java.time.format.DateTimeFormatterBuilder

class ContractFailure(val status: Int, val code: String) : RuntimeException(code)
data class Saved(val memo: Memo, val created: Boolean)

class MemoStore(private val file: Path, private val clock: Clock = Clock.systemUTC()) {
    init {
        file.toAbsolutePath().parent.toFile().mkdirs()
        connection().use { connection ->
            connection.createStatement().use { sql ->
                sql.execute("PRAGMA journal_mode=WAL")
                val version = sql.executeQuery("PRAGMA user_version").use { it.next(); it.getInt(1) }
                require(version in 0..1) { "Unsupported database schema $version; existing data preserved" }
                sql.execute("CREATE TABLE IF NOT EXISTS memos(id INTEGER PRIMARY KEY AUTOINCREMENT, attempt_id TEXT UNIQUE NOT NULL, body TEXT NOT NULL, created_at TEXT NOT NULL)")
                if (version == 0) sql.execute("PRAGMA user_version=1")
            }
        }
    }
    private fun connection(): Connection = DriverManager.getConnection("jdbc:sqlite:${file.toAbsolutePath()}").also {
        it.createStatement().use { statement -> statement.execute("PRAGMA busy_timeout=10000") }
    }
    private fun validKey(key: String) = key.matches(Regex("[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"))
    private fun find(connection: Connection, key: String): Memo? = connection.prepareStatement("SELECT id,body,created_at FROM memos WHERE attempt_id=?").use {
        it.setString(1, key)
        it.executeQuery().use { rows -> if (rows.next()) Memo(rows.getLong(1).toString().padStart(12, '0'), rows.getString(2), rows.getString(3)) else null }
    }
    fun find(key: String): Memo? {
        if (!validKey(key)) throw ContractFailure(422, "INVALID_ATTEMPT")
        return connection().use { find(it, key) }
    }
    fun list(): List<Memo> = connection().use { connection ->
        connection.createStatement().use { it.executeQuery("SELECT id,body,created_at FROM memos ORDER BY created_at DESC,id DESC").use { rows ->
            buildList { while (rows.next()) add(Memo(rows.getLong(1).toString().padStart(12, '0'), rows.getString(2), rows.getString(3))) }
        } }
    }
    fun save(request: SaveRequest): Saved {
        if (!validKey(request.attemptId)) throw ContractFailure(422, "INVALID_ATTEMPT")
        if (!BodyPolicy.valid(request.body)) throw ContractFailure(422, "INVALID_BODY")
        val body = BodyPolicy.normalize(request.body)
        return connection().use { connection ->
            // Reserve the writer before looking up the key. Safe across separate processes/connections.
            connection.createStatement().use { it.execute("BEGIN IMMEDIATE") }
            try {
                val previous = find(connection, request.attemptId)
                val result = if (previous != null) {
                    if (previous.body != body) throw ContractFailure(409, "ATTEMPT_CONFLICT")
                    Saved(previous, false)
                } else {
                    val time = DateTimeFormatterBuilder().appendInstant(3).toFormatter().format(clock.instant())
                    connection.prepareStatement("INSERT INTO memos(attempt_id,body,created_at) VALUES(?,?,?)").use {
                        it.setString(1, request.attemptId); it.setString(2, body); it.setString(3, time); it.executeUpdate()
                    }
                    Saved(checkNotNull(find(connection, request.attemptId)), true)
                }
                connection.createStatement().use { it.execute("COMMIT") }
                result
            } catch (failure: Exception) {
                runCatching { connection.createStatement().use { it.execute("ROLLBACK") } }
                throw failure
            }
        }
    }
}

package memo.api

import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json

val wireJson = Json { ignoreUnknownKeys = false; encodeDefaults = true }
@Serializable data class Memo(val id: String, val body: String, val createdAt: String)
@Serializable data class MemoList(val memos: List<Memo>)
@Serializable data class MemoResult(val memo: Memo)
@Serializable data class SaveRequest(val attemptId: String, val body: String)
@Serializable data class ApiError(val code: String, val message: String)

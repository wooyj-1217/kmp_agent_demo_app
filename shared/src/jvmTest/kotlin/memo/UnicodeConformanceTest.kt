package memo

import kotlin.test.*
import memo.domain.Graphemes

class UnicodeConformanceTest {
    @Test fun officialUnicode16GraphemeVectors() {
        val fixture = checkNotNull(javaClass.getResourceAsStream("/GraphemeBreakTest.txt"))
        var tested = 0
        fixture.bufferedReader().useLines { lines -> lines.forEach { raw ->
            val line = raw.substringBefore('#').trim()
            if (line.isNotEmpty()) {
                val tokens = line.split(Regex("\\s+"))
                val expected = tokens.count { it == "÷" } - 1
                val text = buildString { tokens.filter { it != "÷" && it != "×" }.forEach { appendCodePoint(it.toInt(16)) } }
                assertEquals(expected, Graphemes.count(text), raw)
                tested++
            }
        } }
        assertTrue(tested > 1000, "Full official fixture required")
        println("Unicode 16 official grapheme vectors passed: $tested")
    }
}

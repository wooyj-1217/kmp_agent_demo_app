package memo.domain

// Pure domain: no DTO, storage, HTTP, or UI dependencies.
object BodyPolicy {
    private fun whitespace(c: Char) = c.code in 9..13 || c.code in 0x2000..0x200A ||
        c.code in listOf(0x20, 0x85, 0xA0, 0x1680, 0x2028, 0x2029, 0x202F, 0x205F, 0x3000)
    fun normalize(body: String): String = body.trim(::whitespace)
    fun count(body: String): Int = Graphemes.count(normalize(body))
    fun valid(body: String): Boolean = try { count(body) in 1..2000 } catch (_: IllegalArgumentException) { false }
}

/** UAX #29 revision 45, Unicode 16.0. Tables generated from official Unicode data. */
object Graphemes {
    fun count(text: String): Int {
        if (text.isEmpty()) return 0
        val points = mutableListOf<Int>()
        var at = 0
        while (at < text.length) {
            val first = text[at++].code
            val point = if (first in 0xD800..0xDBFF) {
                require(at < text.length && text[at].code in 0xDC00..0xDFFF) { "Unpaired surrogate" }
                0x10000 + ((first - 0xD800) shl 10) + (text[at++].code - 0xDC00)
            } else { require(first !in 0xDC00..0xDFFF) { "Unpaired surrogate" }; first }
            points.add(point)
        }
        val props = points.map { Unicode16.grapheme(it) }
        var total = 1
        var regionalRun = if (props[0] == "Regional_Indicator") 1 else 0
        for (i in 1 until points.size) {
            val a = props[i - 1]; val b = props[i]
            val boundary = when {
                a == "CR" && b == "LF" -> false
                a in listOf("Control", "CR", "LF") || b in listOf("Control", "CR", "LF") -> true
                a == "L" && b in listOf("L", "V", "LV", "LVT") -> false
                a in listOf("LV", "V") && b in listOf("V", "T") -> false
                a in listOf("LVT", "T") && b == "T" -> false
                b in listOf("Extend", "ZWJ", "SpacingMark") || a == "Prepend" -> false
                indicJoin(points, i) -> false
                b == "Other" && Unicode16.pictographic(points[i]) && a == "ZWJ" && emojiBefore(points, props, i - 2) -> false
                Unicode16.pictographic(points[i]) && a == "ZWJ" && emojiBefore(points, props, i - 2) -> false
                a == "Regional_Indicator" && b == "Regional_Indicator" && regionalRun % 2 == 1 -> false
                else -> true
            }
            if (boundary) total++
            regionalRun = if (b == "Regional_Indicator") {
                if (a == "Regional_Indicator") regionalRun + 1 else 1
            } else 0
        }
        return total
    }
    private fun emojiBefore(points: List<Int>, props: List<String>, from: Int): Boolean {
        var i = from
        while (i >= 0 && props[i] == "Extend") i--
        return i >= 0 && Unicode16.pictographic(points[i])
    }
    private fun indicJoin(points: List<Int>, index: Int): Boolean {
        if (Unicode16.indic(points[index]) != "Consonant") return false
        var i = index - 1; var linker = false
        while (i >= 0 && Unicode16.indic(points[i]) in listOf("Extend", "Linker")) {
            if (Unicode16.indic(points[i]) == "Linker") linker = true
            i--
        }
        return linker && i >= 0 && Unicode16.indic(points[i]) == "Consonant"
    }
}

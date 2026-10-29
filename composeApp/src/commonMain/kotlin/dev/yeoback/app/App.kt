package dev.yeoback.app

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.focusable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.grid.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.listSaver
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.ExperimentalComposeUiApi
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.focus.FocusDirection
import androidx.compose.ui.focus.focusRequester
import androidx.compose.ui.focus.onFocusChanged
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.input.key.*
import androidx.compose.ui.platform.LocalFocusManager
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.*
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import dev.yeoback.domain.Memo
import dev.yeoback.domain.MemoRepository
import dev.yeoback.resources.Res
import dev.yeoback.resources.noto_sans_kr
import org.jetbrains.compose.resources.Font

private val Cream = Color(0xFFF6F5F0)
private val Paper = Color(0xFFFFFEFA)
private val Ink = Color(0xFF243E36)
private val Forest = Color(0xFF24483F)
private val Muted = Color(0xFF606E66)
private val Line = Color(0xFFD9DDD4)
private val Danger = Color(0xFFA33930)
private val CardColors = listOf(Color(0xFFDFE9DD), Color(0xFFE5E7F5), Color(0xFFF5E1CE))

private enum class Section(val label: String, val path: String) {
    All("모든 메모", "all"), Pinned("고정한 메모", "pinned"), Trash("휴지통", "trash")
}
private data class Draft(val id: String?, val title: String, val body: String)

@Composable
fun YeobackApp(repositoryFactory: () -> MemoRepository) {
    val font = FontFamily(Font(Res.font.noto_sans_kr))
    val base = Typography()
    val type = base.copy(
        displayLarge = base.displayLarge.copy(fontFamily = font),
        displayMedium = base.displayMedium.copy(fontFamily = font),
        displaySmall = base.displaySmall.copy(fontFamily = font),
        headlineLarge = base.headlineLarge.copy(fontFamily = font, fontWeight = FontWeight.Bold),
        headlineMedium = base.headlineMedium.copy(fontFamily = font, fontWeight = FontWeight.Bold),
        headlineSmall = base.headlineSmall.copy(fontFamily = font, fontWeight = FontWeight.Bold),
        titleLarge = base.titleLarge.copy(fontFamily = font, fontWeight = FontWeight.Bold),
        titleMedium = base.titleMedium.copy(fontFamily = font, fontWeight = FontWeight.Bold),
        titleSmall = base.titleSmall.copy(fontFamily = font),
        bodyLarge = base.bodyLarge.copy(fontFamily = font, lineHeight = 28.sp),
        bodyMedium = base.bodyMedium.copy(fontFamily = font, lineHeight = 24.sp),
        bodySmall = base.bodySmall.copy(fontFamily = font),
        labelLarge = base.labelLarge.copy(fontFamily = font),
        labelMedium = base.labelMedium.copy(fontFamily = font),
        labelSmall = base.labelSmall.copy(fontFamily = font)
    )
    MaterialTheme(
        colorScheme = lightColorScheme(primary = Forest, onPrimary = Color.White, background = Cream,
            surface = Paper, onSurface = Ink, onBackground = Ink, onSurfaceVariant = Muted,
            outline = Line, error = Danger), typography = type,
        shapes = Shapes(medium = RoundedCornerShape(12.dp), large = RoundedCornerShape(20.dp))
    ) {
        var repository by remember { mutableStateOf<MemoRepository?>(null) }
        var loadError by remember { mutableStateOf(false) }
        var attempt by remember { mutableIntStateOf(0) }
        LaunchedEffect(attempt) {
            loadError = false
            repository = try { repositoryFactory() } catch (_: Exception) { loadError = true; null }
        }
        Surface(Modifier.fillMaxSize(), color = Cream) {
            Box(Modifier.fillMaxSize().windowInsetsPadding(WindowInsets.safeDrawing).imePadding()) {
                val current = repository
                if (current != null) MemoWorkspace(current)
                else Column(Modifier.align(Alignment.Center).padding(32.dp).widthIn(max = 420.dp),
                    horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(16.dp)) {
                    Brand()
                    if (loadError) {
                        Text("메모를 불러오지 못했어요", style = MaterialTheme.typography.titleLarge)
                        Text("저장된 데이터는 변경하지 않았습니다. 기기의 저장 공간과 접근 권한을 확인한 뒤 다시 시도해 주세요.", color = Muted)
                        Button(onClick = { attempt++ }, modifier = Modifier.testTag("retry-load")) { Text("다시 시도") }
                    } else {
                        CircularProgressIndicator(Modifier.size(28.dp))
                        Text("메모를 불러오고 있어요", color = Muted)
                    }
                }
            }
        }
    }
}

@OptIn(ExperimentalComposeUiApi::class, ExperimentalLayoutApi::class)
@Composable
private fun MemoWorkspace(repository: MemoRepository) {
    var notes by remember(repository) { mutableStateOf(repository.memos) }
    var section by rememberSaveable { mutableStateOf(Section.All) }
    var query by rememberSaveable { mutableStateOf("") }
    val draftSaver = listSaver<Draft?, String>(
        save = { if (it == null) emptyList() else listOf(it.id ?: "", it.title, it.body) },
        restore = { if (it.isEmpty()) null else Draft(it[0].ifEmpty { null }, it[1], it[2]) }
    )
    var draft by rememberSaveable(stateSaver = draftSaver) { mutableStateOf<Draft?>(null) }
    var navigationInitialized by rememberSaveable { mutableStateOf(false) }
    var notice by remember { mutableStateOf<String?>(null) }
    var error by remember { mutableStateOf<String?>(null) }
    var retry by remember { mutableStateOf<(() -> Unit)?>(null) }
    var pending by remember { mutableStateOf<(() -> Unit)?>(null) }
    var purge by remember { mutableStateOf<Memo?>(null) }
    var showInfo by remember { mutableStateOf(false) }
    val focus = LocalFocusManager.current
    val titleFocus = remember { FocusRequester() }
    val bodyFocus = remember { FocusRequester() }
    var focusedField by remember { mutableStateOf("") }
    val dialogCancelFocus = remember { FocusRequester() }
    val navFocus = remember { FocusRequester() }
    val gridState = rememberLazyGridState()
    val initialRoute = remember { platformInitialRoute() }
    val selected = notes.firstOrNull { it.id == draft?.id }
    val dirty = draft?.let { it.title != (selected?.title ?: "") || it.body != (selected?.body ?: "") } ?: false
    val modalOpen = pending != null || purge != null || showInfo
    var previousModalOpen by remember { mutableStateOf(false) }
    val route = draft?.let { if (it.id == null) "new" else if (selected?.deletedAt != null) "trash/${it.id}" else "note/${it.id}" } ?: section.path

    fun clearFeedback() { error = null; retry = null; notice = null }
    fun hasUnsavedChanges(): Boolean {
        val current = draft ?: return false
        val stored = notes.firstOrNull { it.id == current.id }
        return current.title != (stored?.title ?: "") || current.body != (stored?.body ?: "")
    }
    fun guard(action: () -> Unit) {
        if (hasUnsavedChanges()) pending = action else { clearFeedback(); action() }
    }
    fun applyRoute(path: String) {
        clearFeedback()
        when {
            path == "new" -> { section = Section.All; query = ""; draft = Draft(null, "", "") }
            path.startsWith("note/") || path.startsWith("trash/") -> {
                val memo = notes.firstOrNull { it.id == path.substringAfter('/') }
                if (memo == null) { draft = null; section = Section.All; notice = "메모를 찾을 수 없어요" }
                else { section = if (memo.deletedAt != null) Section.Trash else Section.All; draft = Draft(memo.id, memo.title, memo.body) }
            }
            else -> { section = Section.entries.firstOrNull { it.path == path } ?: Section.All; draft = null }
        }
    }
    LaunchedEffect(Unit) { if (!navigationInitialized) { applyRoute(initialRoute); navigationInitialized = true } }
    PlatformKeyboard(enabled = !modalOpen) { reverse ->
        when {
            draft != null && focusedField == "title" && !reverse -> { bodyFocus.requestFocus(); true }
            draft != null && focusedField == "body" && reverse -> { titleFocus.requestFocus(); true }
            else -> focus.moveFocus(if (reverse) FocusDirection.Previous else FocusDirection.Next)
        }
    }
    PlatformNavigation(route, dirty, onRoute = { incoming ->
        if (incoming != route) {
            if (hasUnsavedChanges()) platformReplaceRoute(route)
            guard { applyRoute(incoming) }
        }
    }, onBack = { guard { draft = null; section = Section.All; focus.clearFocus() } })
    LaunchedEffect(draft?.id, draft != null) { if (draft != null && selected?.deletedAt == null) titleFocus.requestFocus() }
    LaunchedEffect(pending != null, purge?.id) { if (pending != null || purge != null) dialogCancelFocus.requestFocus() }
    LaunchedEffect(modalOpen) {
        if (platformIsWeb() && !modalOpen && previousModalOpen) {
            if (draft != null) titleFocus.requestFocus() else navFocus.requestFocus()
        }
        previousModalOpen = modalOpen
    }

    fun mutate(operation: () -> Unit, success: () -> Unit) {
        try {
            operation()
            notes = repository.memos
            error = null; retry = null
            success()
        } catch (_: Exception) {
            error = "저장하지 못했어요. 내용은 유지됩니다. 저장 공간을 확인하고 다시 시도해 주세요."
            retry = { mutate(operation, success) }
        }
    }
    fun save() {
        val value = draft ?: return
        if (value.title.isBlank() && value.body.isBlank()) return
        mutate({ repository.save(value.id, value.title, value.body) }, {
            draft = null; notice = "저장했어요"; focus.clearFocus()
        })
    }
    fun create() { guard { applyRoute("new") } }
    fun navigate(target: Section) { guard { section = target; draft = null; query = ""; focus.clearFocus() } }
    val filtered = remember(notes, section, query) {
        repository.visible(query, pinnedOnly = section == Section.Pinned, trash = section == Section.Trash)
    }
    key(if (platformIsWeb()) modalOpen else false) {
    BoxWithConstraints(Modifier.fillMaxSize().then(if (platformIsWeb() && modalOpen) Modifier.clearAndSetSemantics { } else Modifier).onPreviewKeyEvent { event ->
        when {
            event.type != KeyEventType.KeyDown -> false
            (event.isCtrlPressed || event.isMetaPressed) && event.key == Key.S -> { save(); true }
            (event.isCtrlPressed || event.isMetaPressed) && event.key == Key.N -> { create(); true }
            event.key == Key.Escape && draft != null -> { guard { draft = null; focus.clearFocus() }; true }
            else -> false
        }
    }) {
        val wide = maxWidth >= 1100.dp
        val rail = maxWidth >= 700.dp
        val viewportWidth = maxWidth
        val editorWidth = (maxWidth * .30f).coerceIn(340.dp, 420.dp)
        Row(Modifier.fillMaxSize()) {
            if (rail && (wide || draft == null)) Sidebar(section, notes, if (wide) 204 else 168, navFocus, ::navigate, ::create, { showInfo = true })
            if (draft == null || wide) {
                Column(Modifier.weight(1f).fillMaxHeight().padding(horizontal = if (rail) 32.dp else 20.dp)) {
                    Spacer(Modifier.height(if (rail) 36.dp else 24.dp))
                    Text("Y E O B A C K  /  Y O U R  Q U I E T  S P A C E", fontSize = 9.sp, fontWeight = FontWeight.Bold, color = Forest)
                    Spacer(Modifier.height(12.dp))
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Column(Modifier.weight(1f)) {
                            Text(section.label, style = MaterialTheme.typography.headlineMedium, modifier = Modifier.semantics { heading() })
                            Text(if (section == Section.Trash) "잠시 내려놓은 기록들이에요." else "떠오른 생각을, 가볍게 남겨요.", fontSize = 12.sp, color = Muted)
                        }
                        if (section != Section.Trash) Button(onClick = ::create, modifier = Modifier.heightIn(min = 48.dp).testTag("new-memo"), shape = RoundedCornerShape(12.dp)) { Text("＋ 메모") }
                        else TextButton(onClick = { showInfo = true }) { Text("안내") }
                    }
                    Spacer(Modifier.height(24.dp))
                    OutlinedTextField(query, onValueChange = { query = it }, singleLine = true,
                        modifier = Modifier.fillMaxWidth().testTag("memo-search").semantics { contentDescription = "메모 검색" },
                        label = { Text("메모 검색") }, placeholder = { Text("제목이나 내용으로 검색") },
                        shape = RoundedCornerShape(12.dp),
                        trailingIcon = { if (query.isNotEmpty()) TextButton(onClick = { query = "" }, modifier = Modifier.semantics { contentDescription = "검색 지우기" }) { Text("지우기", fontSize = 11.sp) } },
                        keyboardOptions = KeyboardOptions(imeAction = ImeAction.Search),
                        keyboardActions = KeyboardActions(onSearch = { focus.clearFocus() }),
                        colors = OutlinedTextFieldDefaults.colors(unfocusedContainerColor = Paper, focusedContainerColor = Paper, unfocusedBorderColor = Line))
                    if (!rail) {
                        FlowRow(Modifier.fillMaxWidth().padding(top = 12.dp), horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                            Section.entries.forEach { target ->
                                FilterChip(section == target, onClick = { navigate(target) }, label = { Text(if (target == Section.Pinned) "고정" else target.label, fontSize = 12.sp) }, modifier = Modifier.heightIn(min = 44.dp).then(if (target == section) Modifier.focusRequester(navFocus) else Modifier).testTag("nav-${target.path}"))
                            }
                            TextButton(onClick = { showInfo = true }, contentPadding = PaddingValues(4.dp)) { Text("정보", fontSize = 12.sp) }
                        }
                    }
                    notice?.let { Feedback(it, false, { notice = null }, null) }
                    if (draft == null) error?.let { Feedback(it, true, null, retry) }
                    Row(Modifier.fillMaxWidth().padding(vertical = 20.dp), horizontalArrangement = Arrangement.SpaceBetween) {
                        Text("메모 ${filtered.size}개", fontSize = 11.sp, color = Muted)
                        Text(if (section == Section.Trash) "최근 삭제순" else "고정 먼저 · 최근 수정순", fontSize = 10.sp, color = Muted)
                    }
                    if (filtered.isEmpty()) {
                        EmptyMemos(Modifier.weight(1f).fillMaxWidth(), section, query, { query = "" }, ::create)
                    } else {
                        val columns = if (viewportWidth < 360.dp) 1 else if (viewportWidth >= 1440.dp) 3 else 2
                        LazyVerticalGrid(GridCells.Fixed(columns), state = gridState, modifier = Modifier.weight(1f).testTag("memo-grid"),
                            verticalArrangement = Arrangement.spacedBy(16.dp), horizontalArrangement = Arrangement.spacedBy(12.dp), contentPadding = PaddingValues(bottom = 24.dp)) {
                            items(filtered, key = { it.id }) { memo ->
                                MemoCard(memo, selected?.id == memo.id, if (rail) 220 else 220) {
                                    guard { draft = Draft(memo.id, memo.title, memo.body) }
                                }
                            }
                        }
                    }
                }
            }
            if (wide) VerticalDivider(color = Line)
            val value = draft
            if (value != null) {
                val modifier = if (wide) Modifier.width(editorWidth).fillMaxHeight() else Modifier.weight(1f).fillMaxHeight()
                Editor(modifier, value, selected, dirty, error, retry, titleFocus, bodyFocus,
                    onFieldFocus = { name, active -> if (active) focusedField = name else if (focusedField == name) focusedField = "" },
                    onTitleChange = { text -> draft = draft?.copy(title = text); error = null; retry = null },
                    onBodyChange = { text -> draft = draft?.copy(body = text); error = null; retry = null },
                    onBack = { guard { draft = null; focus.clearFocus() } }, onSave = ::save,
                    onPin = { selected?.let { memo -> guard {
                        mutate({ repository.pin(memo.id) }, { notes.firstOrNull { it.id == memo.id }?.let { draft = Draft(it.id, it.title, it.body) }; notice = if (memo.pinned) "고정을 해제했어요" else "메모를 고정했어요" })
                    } } },
                    onTrash = { selected?.let { memo -> guard { mutate({ repository.trash(memo.id) }, { draft = null; notice = "휴지통으로 옮겼어요"; focus.clearFocus() }) } } },
                    onRestore = { selected?.let { memo -> mutate({ repository.restore(memo.id) }, { draft = null; section = Section.All; query = ""; notice = "메모를 복원했어요" }) } },
                    onPurge = { purge = selected })
            } else if (wide) {
                Column(Modifier.width(editorWidth).fillMaxHeight().background(Paper).padding(32.dp), horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.Center) {
                    PaperDrawing(Modifier.size(100.dp))
                    Spacer(Modifier.height(24.dp))
                    Text("생각이 머무는 자리", style = MaterialTheme.typography.titleMedium)
                    Spacer(Modifier.height(8.dp))
                    Text("메모를 선택하거나\n새로운 생각을 남겨보세요.", color = Muted, fontSize = 13.sp)
                    Spacer(Modifier.height(24.dp))
                    OutlinedButton(onClick = ::create, shape = RoundedCornerShape(12.dp)) { Text("＋ 새 메모") }
                }
            }
        }
    }
    }
    if (pending != null) MemoDialog("변경 내용을 버릴까요?", "변경 버리기", "계속 편집", dialogCancelFocus,
        onDismiss = { pending = null }, onConfirm = { val action = pending; pending = null; clearFeedback(); action?.invoke() },
        confirmTag = "discard-draft", cancelTag = "keep-editing", danger = true) { Text("저장하지 않은 내용은 사라집니다.") }
    purge?.let { memo -> MemoDialog("메모를 영구 삭제할까요?", "영구 삭제", "취소", dialogCancelFocus,
        onDismiss = { purge = null }, onConfirm = { purge = null; mutate({ repository.deleteForever(memo.id) }, { draft = null; notice = "영구 삭제했어요" }) },
        confirmTag = "confirm-purge", danger = true) {
        Text("‘${memo.displayTitle.take(80)}${if (memo.displayTitle.length > 80) "…" else ""}’ 메모가 사라집니다. 영구 삭제 후에는 복구할 수 없어요.")
    } }
    if (showInfo) MemoDialog("나만의 기록, 여백", "알겠어요", null, dialogCancelFocus,
        onDismiss = { showInfo = false }, onConfirm = { showInfo = false }) {
            Text("메모는 이 기기 또는 현재 브라우저에만 저장됩니다. 다른 기기와 자동으로 동기화되지 않아요.")
            Text("저장 버튼을 눌러 기록을 보관해 주세요. 앱 제거나 브라우저 데이터 삭제 시 메모가 사라질 수 있습니다.")
            Text("휴지통의 메모는 자동으로 지워지지 않습니다. 영구 삭제한 메모는 복구할 수 없어요.")
            Text("키보드: Ctrl / ⌘ + N 새 메모 · Ctrl / ⌘ + S 저장 · Esc 목록", fontSize = 12.sp, color = Muted)
            Text("글꼴: Noto Sans KR · SIL Open Font License 1.1", fontSize = 10.sp, color = Muted)
    }
}

/** Web keeps modal semantics in the same scene: closing a dialog restores the live DOM tree. */
@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun MemoDialog(title: String, confirmLabel: String, cancelLabel: String?, cancelFocus: FocusRequester,
    onDismiss: () -> Unit, onConfirm: () -> Unit, confirmTag: String = "dialog-confirm", cancelTag: String = "dialog-cancel",
    danger: Boolean = false, content: @Composable ColumnScope.() -> Unit) {
    if (!platformIsWeb()) {
        AlertDialog(onDismissRequest = onDismiss, title = { Text(title) },
            text = { Column(Modifier.verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(16.dp), content = content) },
            confirmButton = { TextButton(onConfirm, modifier = Modifier.testTag(confirmTag)) { Text(confirmLabel, color = if (danger) Danger else Forest) } },
            dismissButton = { if (cancelLabel != null) TextButton(onDismiss, modifier = Modifier.focusRequester(cancelFocus).testTag(cancelTag)) { Text(cancelLabel) } })
        return
    }
    val confirmFocus = remember { FocusRequester() }
    var cancelFocused by remember { mutableStateOf(cancelLabel != null) }
    LaunchedEffect(Unit) { if (cancelLabel != null) cancelFocus.requestFocus() else confirmFocus.requestFocus() }
    BoxWithConstraints(Modifier.fillMaxSize().onPreviewKeyEvent { event ->
        if (event.type != KeyEventType.KeyDown) false
        else when (event.key) {
            Key.Escape -> { onDismiss(); true }
            Key.Tab -> {
                if (cancelLabel == null || cancelFocused) confirmFocus.requestFocus() else cancelFocus.requestFocus()
                true
            }
            else -> false
        }
    }) {
        val dialogMaxHeight = (maxHeight - 96.dp).coerceAtLeast(160.dp)
        Box(Modifier.matchParentSize().background(Color.Black.copy(alpha = .28f))
            .clickable(interactionSource = remember { MutableInteractionSource() }, indication = null, onClick = onDismiss)
            .clearAndSetSemantics { })
        Surface(Modifier.align(Alignment.Center).padding(24.dp).widthIn(max = 480.dp).fillMaxWidth().semantics { paneTitle = title },
            shape = RoundedCornerShape(24.dp), color = Paper, shadowElevation = 12.dp) {
            Column(Modifier.padding(24.dp).heightIn(max = dialogMaxHeight)) {
                Text(title, style = MaterialTheme.typography.titleLarge, modifier = Modifier.semantics { heading() })
                Spacer(Modifier.height(20.dp))
                Column(Modifier.weight(1f, fill = false).verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(16.dp), content = content)
                Spacer(Modifier.height(20.dp))
                FlowRow(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.End) {
                    if (cancelLabel != null) TextButton(onDismiss, modifier = Modifier.focusRequester(cancelFocus).onFocusChanged { if (it.isFocused) cancelFocused = true }.testTag(cancelTag)) { Text(cancelLabel) }
                    TextButton(onConfirm, modifier = Modifier.focusRequester(confirmFocus).onFocusChanged { if (it.isFocused) cancelFocused = false }.testTag(confirmTag)) { Text(confirmLabel, color = if (danger) Danger else Forest) }
                }
            }
        }
    }
}

@Composable
private fun Sidebar(section: Section, notes: List<Memo>, width: Int, navFocus: FocusRequester, navigate: (Section) -> Unit, create: () -> Unit, info: () -> Unit) {
    Column(Modifier.width(width.dp).fillMaxHeight().border(width = .5.dp, color = Line).padding(20.dp)) {
        Spacer(Modifier.height(20.dp)); Brand(); Spacer(Modifier.height(32.dp))
        Button(create, modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp), shape = RoundedCornerShape(12.dp)) { Text("＋ 새 메모") }
        Spacer(Modifier.height(28.dp))
        Section.entries.forEach { target ->
            val count = notes.count { if (target == Section.Trash) it.deletedAt != null else it.deletedAt == null && (target != Section.Pinned || it.pinned) }
            Row(Modifier.fillMaxWidth().heightIn(min = 48.dp).clip(RoundedCornerShape(12.dp))
                .background(if (target == section) CardColors[0] else Color.Transparent)
                .then(if (target == section) Modifier.focusRequester(navFocus) else Modifier).semantics { selected = target == section }.clickable(role = Role.Tab, onClick = { navigate(target) }).testTag("nav-${target.path}").padding(12.dp),
                verticalAlignment = Alignment.CenterVertically) {
                Text(target.label, Modifier.weight(1f), fontSize = 13.sp, fontWeight = if (target == section) FontWeight.Bold else FontWeight.Normal)
                if (count > 0) Text(count.toString(), fontSize = 10.sp, color = Muted)
            }
            Spacer(Modifier.height(4.dp))
        }
        Spacer(Modifier.weight(1f))
        Text("생각이 머무는 자리.", fontSize = 11.sp)
        Text("오직 이 기기에 보관됩니다.", fontSize = 10.sp, color = Muted)
        TextButton(onClick = info, contentPadding = PaddingValues(0.dp)) { Text("여백에 대해", fontSize = 11.sp) }
    }
}

@Composable
private fun Brand() {
    Column { Text("여백", fontSize = 28.sp, fontWeight = FontWeight.Black, color = Ink); Text("Y E O B A C K", fontSize = 9.sp, color = Forest) }
}

@Composable
private fun MemoCard(memo: Memo, selected: Boolean, height: Int, open: () -> Unit) {
    val shade = CardColors[(memo.id.hashCode() and Int.MAX_VALUE) % CardColors.size]
    var focused by remember { mutableStateOf(false) }
    val fontScale = LocalDensity.current.fontScale.coerceAtLeast(1f)
    Column(Modifier.fillMaxWidth().height((height * fontScale).dp).clip(RoundedCornerShape(20.dp)).background(shade)
        .onFocusChanged { focused = it.isFocused }
        .then(if (focused) Modifier.border(3.dp, Color(0xFF3249A8), RoundedCornerShape(20.dp)) else if (selected) Modifier.border(1.5.dp, Forest, RoundedCornerShape(20.dp)) else Modifier)
        .semantics { this.selected = selected }
        .clickable(role = Role.Button, onClick = open).testTag("memo-${memo.id}").padding(20.dp)) {
        Text(memo.displayTitle, fontSize = 16.sp, fontWeight = FontWeight.Bold, maxLines = 2, overflow = TextOverflow.Ellipsis)
        Spacer(Modifier.height(12.dp))
        Text(memo.body, fontSize = 13.sp, lineHeight = 22.sp, maxLines = 4, overflow = TextOverflow.Ellipsis, modifier = Modifier.weight(1f))
        Spacer(Modifier.height(12.dp))
        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.SpaceBetween) {
            Text(platformDate(memo.deletedAt ?: memo.updatedAt), modifier = Modifier.weight(1f).padding(end = 4.dp), fontSize = 10.sp, color = Muted, maxLines = 1, overflow = TextOverflow.Ellipsis)
            if (memo.pinned) Text("고정됨", fontSize = 10.sp, color = Forest)
        }
    }
}

@Composable
private fun EmptyMemos(modifier: Modifier, section: Section, query: String, clear: () -> Unit, create: () -> Unit) {
    Column(modifier.verticalScroll(rememberScrollState()).padding(vertical = 28.dp), horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.Center) {
        PaperDrawing(Modifier.size(84.dp)); Spacer(Modifier.height(24.dp))
        val title = when { query.isNotBlank() -> "검색 결과가 없어요"; section == Section.Trash -> "휴지통이 비어 있어요"; section == Section.Pinned -> "고정한 메모가 없어요"; else -> "첫 생각을 남겨볼까요?" }
        Text(title, style = MaterialTheme.typography.titleMedium, modifier = Modifier.semantics { heading() })
        Spacer(Modifier.height(8.dp))
        Text(when { query.isNotBlank() -> "다른 단어로 다시 찾아보세요."; section == Section.Trash -> "휴지통으로 옮긴 메모는 여기에서 복원해요."; section == Section.Pinned -> "자주 찾는 메모를 열어 고정해 보세요."; else -> "짧은 한 줄로 시작해도 좋아요." }, fontSize = 12.sp, color = Muted)
        Spacer(Modifier.height(20.dp))
        if (query.isNotBlank()) OutlinedButton(clear) { Text("검색 지우기") }
        else if (section == Section.All) Button(create, shape = RoundedCornerShape(12.dp)) { Text("＋ 첫 메모 쓰기") }
    }
}

@Composable
private fun PaperDrawing(modifier: Modifier) {
    Canvas(modifier) {
        val w = size.width; val h = size.height
        drawRoundRect(CardColors[0], Offset(w * .1f, h * .1f), Size(w * .75f, h * .85f), cornerRadius = androidx.compose.ui.geometry.CornerRadius(w * .15f))
        drawRoundRect(Forest, Offset(w * .22f, h * .03f), Size(w * .65f, h * .8f), cornerRadius = androidx.compose.ui.geometry.CornerRadius(w * .1f), style = Stroke(2.dp.toPx()))
        for (i in 0..2) drawLine(Forest.copy(alpha = .5f), Offset(w * .35f, h * (.3f + i * .14f)), Offset(w * (.72f - i * .06f), h * (.3f + i * .14f)), 2.dp.toPx())
    }
}

@Composable
private fun Feedback(text: String, isError: Boolean, dismiss: (() -> Unit)?, retry: (() -> Unit)?) {
    Column(Modifier.fillMaxWidth().padding(top = 12.dp).clip(RoundedCornerShape(12.dp))
        .background(if (isError) CardColors[2] else CardColors[0]).semantics { liveRegion = if (isError) LiveRegionMode.Assertive else LiveRegionMode.Polite }.padding(12.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text(text, Modifier.weight(1f), fontSize = 12.sp, color = if (isError) Danger else Forest)
            dismiss?.let { TextButton(it, contentPadding = PaddingValues(4.dp)) { Text("닫기", fontSize = 11.sp) } }
        }
        retry?.let { TextButton(it, modifier = Modifier.testTag("retry-write")) { Text("다시 시도") } }
    }
}

@Composable
private fun Editor(modifier: Modifier, draft: Draft, memo: Memo?, dirty: Boolean, error: String?, retry: (() -> Unit)?,
    titleFocus: FocusRequester, bodyFocus: FocusRequester, onFieldFocus: (String, Boolean) -> Unit,
    onTitleChange: (String) -> Unit, onBodyChange: (String) -> Unit, onBack: () -> Unit, onSave: () -> Unit,
    onPin: () -> Unit, onTrash: () -> Unit, onRestore: () -> Unit, onPurge: () -> Unit) {
    val trashed = memo?.deletedAt != null
    val blank = draft.title.isBlank() && draft.body.isBlank()
    Column(modifier.background(Paper).padding(horizontal = 24.dp)) {
        Row(Modifier.fillMaxWidth().padding(top = 16.dp), verticalAlignment = Alignment.CenterVertically) {
            TextButton(onBack, modifier = Modifier.testTag("editor-back"), contentPadding = PaddingValues(horizontal = 4.dp)) { Text("← 목록", fontSize = 12.sp) }
            Text(if (trashed) "휴지통" else if (error != null) "저장 실패" else if (dirty || draft.id == null) "저장 전" else "저장됨",
                modifier = Modifier.weight(1f).padding(horizontal = 8.dp).semantics { liveRegion = LiveRegionMode.Polite }, fontSize = 11.sp, color = Muted)
            if (!trashed) Button(onSave, enabled = !blank, modifier = Modifier.testTag("save-memo").heightIn(min = 44.dp), shape = RoundedCornerShape(12.dp), contentPadding = PaddingValues(horizontal = 16.dp)) { Text("저장", fontSize = 12.sp) }
        }
        if (memo != null) Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.End) {
            if (trashed) {
                TextButton(onRestore, modifier = Modifier.testTag("restore-memo")) { Text("복원") }
                TextButton(onPurge, modifier = Modifier.testTag("purge-memo")) { Text("영구 삭제", color = Danger) }
            } else {
                TextButton(onPin, modifier = Modifier.testTag("pin-memo")) { Text(if (memo.pinned) "고정 해제" else "고정", fontSize = 12.sp) }
                TextButton(onTrash, modifier = Modifier.testTag("trash-memo")) { Text("휴지통으로", fontSize = 12.sp, color = Muted) }
            }
        } else Spacer(Modifier.height(24.dp))
        error?.let { Feedback(it, true, null, retry) }
        Column(Modifier.weight(1f).fillMaxWidth().verticalScroll(rememberScrollState()).padding(top = 24.dp, bottom = 24.dp)) {
            Text(if (trashed) "다시 꺼내 쓸 수 있어요" else "나만의 작은 기록", color = Muted, fontSize = 11.sp)
            Spacer(Modifier.height(24.dp))
            BasicTextField(draft.title, onValueChange = onTitleChange,
                modifier = Modifier.fillMaxWidth().focusRequester(titleFocus).onFocusChanged { onFieldFocus("title", it.isFocused) }.testTag("memo-title").semantics { contentDescription = "메모 제목" },
                readOnly = trashed, singleLine = true, keyboardOptions = KeyboardOptions(imeAction = ImeAction.Next), textStyle = MaterialTheme.typography.headlineSmall.copy(color = Ink, fontSize = 26.sp), cursorBrush = SolidColor(Forest),
                decorationBox = { inner -> Box { if (draft.title.isEmpty()) Text("제목 없이도 괜찮아요", fontSize = 23.sp, color = Muted.copy(alpha = .65f), fontWeight = FontWeight.Bold); inner() } })
            Spacer(Modifier.height(36.dp))
            BasicTextField(draft.body, onValueChange = onBodyChange,
                modifier = Modifier.fillMaxWidth().heightIn(min = 240.dp).focusRequester(bodyFocus).onFocusChanged { onFieldFocus("body", it.isFocused) }.testTag("memo-body").semantics { contentDescription = "메모 내용" },
                readOnly = trashed, textStyle = MaterialTheme.typography.bodyLarge.copy(color = Ink, fontSize = 16.sp, lineHeight = 30.sp), cursorBrush = SolidColor(Forest),
                decorationBox = { inner -> Box { if (draft.body.isEmpty()) Text("지금 떠오른 생각을 적어보세요.", color = Muted.copy(alpha = .7f), style = MaterialTheme.typography.bodyLarge); inner() } })
            if (blank && !trashed) Text("제목이나 내용을 입력하면 저장할 수 있어요.", fontSize = 11.sp, color = Muted)
        }
        HorizontalDivider(color = Line)
        Row(Modifier.fillMaxWidth().padding(vertical = 16.dp), horizontalArrangement = Arrangement.SpaceBetween) {
            Text("${draft.title.length + draft.body.length}자", fontSize = 10.sp, color = Muted)
            Text("여백 / YEOBACK", fontSize = 10.sp, color = Muted)
        }
    }
}

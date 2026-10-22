package memo.android

import android.app.Activity
import android.app.AlertDialog
import android.os.Bundle
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.text.Editable
import android.text.TextWatcher
import android.text.TextUtils
import android.view.View
import android.widget.*
import kotlinx.serialization.*
import memo.api.*
import memo.client.*
import memo.domain.BodyPolicy
import java.net.HttpURLConnection
import java.net.URL
import java.util.UUID
import java.util.concurrent.Executors

class MainActivity : Activity() {
    private lateinit var machine: SaveMachine
    private lateinit var page: LinearLayout
    private var body = ""
    private var composing = false
    private var inputTouched = false
    private var notes = emptyList<Memo>()
    private var message = ""
    private var listState = "loading"
    private var notice: TextView? = null
    private var serial = 0
    private val network = Executors.newFixedThreadPool(2)
    private val ink = Color.rgb(36,60,52)
    private val accent = Color.rgb(40,93,73)
    private fun dp(value: Int) = (value * resources.displayMetrics.density).toInt()
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        // Target35 draws edge-to-edge: the paper background needs dark system-bar icons.
        window.decorView
        if(android.os.Build.VERSION.SDK_INT>=30) {
            val appearance=android.view.WindowInsetsController.APPEARANCE_LIGHT_STATUS_BARS or android.view.WindowInsetsController.APPEARANCE_LIGHT_NAVIGATION_BARS
            window.insetsController?.setSystemBarsAppearance(appearance,appearance)
        } else {
            @Suppress("DEPRECATION")
            window.decorView.systemUiVisibility=View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR or View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR
        }
        try {
            val preferences = getSharedPreferences("memo-attempt", MODE_PRIVATE)
            val store = object : AttemptStore {
                override fun load(): Attempt? = preferences.getString("pending",null)?.let {
                    val request=wireJson.decodeFromString<SaveRequest>(it)
                    require(BodyPolicy.valid(request.body))
                    Attempt(request.attemptId,request.body)
                }
                override fun save(attempt: Attempt) {
                    check(preferences.getString("pending",null)==null)
                    check(preferences.edit().putString("pending",wireJson.encodeToString(SaveRequest(attempt.id,attempt.body))).commit())
                }
                override fun clear() { check(preferences.edit().remove("pending").commit()) }
            }
            machine=SaveMachine(store); composing=machine.locked; body=machine.attempt?.body ?: ""
            render(); loadList()
        } catch (_: Exception) {
            setContentView(text("저장 시도 복구 정보를 읽지 못했어요. 중복 저장을 막기 위해 새 저장을 중단했어요."))
        }
    }
    private val muted=Color.rgb(95,110,102)
    private val line=Color.rgb(221,226,218)
    private val errorInk=Color.rgb(154,48,42)
    private fun shape(fill:Int,stroke:Int?=null)=GradientDrawable().apply {
        setColor(fill);cornerRadius=dp(12).toFloat();stroke?.let {setStroke(dp(1),it)}
    }
    private fun text(value:String,size:Float=16f)=TextView(this).apply {
        text=value;textSize=size;setTextColor(ink);setLineSpacing(dp(3).toFloat(),1.15f)
    }
    private fun button(label:String,enabled:Boolean=true,primary:Boolean=false,action:()->Unit)=Button(this).apply {
        text=if(label=="새 메모 작성")"＋ 새 메모 작성" else if(label=="목록")"‹ 목록" else label;contentDescription=label;isAllCaps=false;elevation=0f;stateListAnimator=null;isEnabled=enabled;minHeight=dp(if(primary)52 else 48);minimumHeight=minHeight
        setPadding(dp(12),dp(8),dp(12),dp(8));textSize=if(primary)15f else 13f
        setTextColor(if(primary)Color.WHITE else accent)
        background=shape(if(primary)accent else Color.TRANSPARENT,if(primary)null else line)
        alpha=if(enabled)1f else .55f;setOnClickListener{action()}
    }
    private fun render() {
        if(isFinishing || isDestroyed)return
        val gutter=if(resources.configuration.screenWidthDp<=360)18 else 24
        page=LinearLayout(this).apply {
            orientation=LinearLayout.VERTICAL;setBackgroundColor(Color.rgb(250,249,245))
            setPadding(dp(gutter),dp(24),dp(gutter),dp(16))
            setOnApplyWindowInsetsListener {v,insets->
                v.setPadding(dp(gutter),dp(24)+insets.systemWindowInsetTop,dp(gutter),dp(16)+insets.systemWindowInsetBottom);insets
            }
        };setContentView(page)
        val top=LinearLayout(this).apply {gravity=android.view.Gravity.CENTER_VERTICAL;minimumHeight=dp(35)}
        if(composing) {top.addView(button("목록",!machine.locked){back()}.apply{background=android.graphics.drawable.ColorDrawable(Color.TRANSPARENT)});top.addView(Space(this),LinearLayout.LayoutParams(0,1,1f))}
        else top.addView(text("memo.",22f).apply{setTypeface(Typeface.SERIF,Typeface.ITALIC)},LinearLayout.LayoutParams(0,-2,1f))
        top.addView(text(if(composing)"새로운 기록" else "나의 기록",11f).apply{setTextColor(muted);gravity=android.view.Gravity.END;setPadding(dp(9),dp(4),dp(9),dp(4));background=shape(Color.rgb(233,240,231))},LinearLayout.LayoutParams(-2,-2))
        page.addView(top)
        val titleRow=LinearLayout(this).apply{gravity=android.view.Gravity.CENTER_VERTICAL}
        titleRow.addView(text(if(composing)"새 메모" else "메모장",27f).apply{setTypeface(typeface,Typeface.BOLD);if(android.os.Build.VERSION.SDK_INT>=28)isAccessibilityHeading=true},LinearLayout.LayoutParams(0,-2,1f))
        if(!composing)titleRow.addView(button("새로고침",listState!="loading"&&listState!="refreshing"){loadList()})
        page.addView(titleRow,LinearLayout.LayoutParams(-1,-2).apply{topMargin=dp(22)})
        page.addView(text(if(composing)"떠오른 생각을 잊기 전에." else "생각이 머무는 작은 공간.",13f).apply{setTextColor(muted)},LinearLayout.LayoutParams(-1,-2).apply{topMargin=dp(8);bottomMargin=dp(20)})
        page.addView(View(this).apply{setBackgroundColor(line)},LinearLayout.LayoutParams(-1,dp(1)).apply{bottomMargin=dp(20)})
        notice=if(message.isNotEmpty() && machine.phase!=SavePhase.UNCERTAIN)text(message,13f).apply{
            val failed=message.startsWith("저장되지")||message.startsWith("저장 시도 정보를")
            val uncertain=machine.locked && machine.phase!=SavePhase.SAVING
            setTextColor(if(failed)errorInk else if(uncertain)Color.rgb(118,82,22) else ink)
            background=shape(if(failed)Color.rgb(255,240,237) else if(uncertain)Color.rgb(255,245,219) else Color.rgb(233,240,231),line)
            setPadding(dp(14),dp(14),dp(14),dp(14));accessibilityLiveRegion=View.ACCESSIBILITY_LIVE_REGION_POLITE
        } else null
        val scroll=ScrollView(this);val content=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL}
        scroll.addView(content);page.addView(scroll,LinearLayout.LayoutParams(-1,0,1f))
        notice?.let{noticeText->
            if(machine.phase==SavePhase.SAVING){
                val row=LinearLayout(this).apply{gravity=android.view.Gravity.CENTER_VERTICAL;background=shape(Color.rgb(233,240,231),line);setPadding(dp(14),dp(14),dp(14),dp(14))}
                row.addView(ProgressBar(this),LinearLayout.LayoutParams(dp(20),dp(20)).apply{marginEnd=dp(10)})
                noticeText.background=null;noticeText.setPadding(0,0,0,0);row.addView(noticeText,LinearLayout.LayoutParams(0,-2,1f));content.addView(row,LinearLayout.LayoutParams(-1,-2).apply{bottomMargin=dp(14)})
            }else content.addView(noticeText,LinearLayout.LayoutParams(-1,-2).apply{bottomMargin=dp(14)})
        }
        if(composing){
            if(machine.phase==SavePhase.UNCERTAIN){val warning=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL;background=shape(Color.rgb(255,245,219),line);setPadding(dp(14),dp(14),dp(14),dp(14))};warning.addView(text("저장 결과를 확인하지 못했어요. 서버에 저장되었을 수 있어요. 중복 저장을 막기 위해 편집을 잠시 잠갔어요.",13f).apply{setTextColor(Color.rgb(118,82,22))});warning.addView(button("같은 저장 결과 다시 확인"){retry()});content.addView(warning,LinearLayout.LayoutParams(-1,-2).apply{bottomMargin=dp(14)})}
            content.addView(text("메모 본문",13f).apply{setTypeface(typeface,Typeface.BOLD)},LinearLayout.LayoutParams(-1,-2).apply{bottomMargin=dp(12)})
            val editor=EditText(this).apply{
                setText(body);hint="오늘 기억하고 싶은 것은 무엇인가요?";setHintTextColor(muted);contentDescription="메모 본문";minHeight=dp(220);gravity=android.view.Gravity.TOP
                inputType=android.text.InputType.TYPE_CLASS_TEXT or android.text.InputType.TYPE_TEXT_FLAG_MULTI_LINE
                isEnabled=!machine.locked;setTextColor(ink);textSize=16f;setLineSpacing(kotlin.math.max(0f,30.4f*resources.displayMetrics.scaledDensity-paint.fontSpacing),1f)
                setPadding(dp(16),dp(16),dp(16),dp(16));background=shape(if(machine.locked)Color.rgb(240,240,232) else Color.WHITE,line)
            };content.addView(editor,LinearLayout.LayoutParams(-1,dp(220)))
            val count=text("",12f).apply{gravity=android.view.Gravity.END;setTextColor(muted)}
            content.addView(count,LinearLayout.LayoutParams(-1,-2).apply{topMargin=dp(10)})
            val fieldError=text("1~2,000자의 본문을 입력해주세요.",13f).apply{setTextColor(errorInk);visibility=View.GONE;accessibilityLiveRegion=View.ACCESSIBILITY_LIVE_REGION_POLITE}
            content.addView(fieldError)
            content.addView(View(this).apply{setBackgroundColor(line)},LinearLayout.LayoutParams(-1,dp(1)).apply{topMargin=dp(24)})
            content.addView(text("짧은 문장도, 여러 줄의 생각도 좋아요.\n저장이 완료되면 메모 목록으로 돌아가요.",12f).apply{setTextColor(muted);setPadding(0,dp(16),0,dp(20))},LinearLayout.LayoutParams(-1,-2).apply{topMargin=0})
            val save=button(if(machine.phase==SavePhase.SAVING)"저장 중…" else if(machine.phase==SavePhase.UNCERTAIN)"저장 결과 확인 필요" else if(message.startsWith("저장되지 않았어요."))"다시 저장" else "메모 저장",!machine.locked&&BodyPolicy.valid(body),true){save()}
            val footerCaption=text("",11f).apply{setTextColor(muted);gravity=android.view.Gravity.CENTER}
            fun update(){
                val length=runCatching{BodyPolicy.count(body)}.getOrDefault(-1)
                val display="$length / 2,000";val styled=android.text.SpannableString(display)
                if(length>2000){styled.setSpan(android.text.style.ForegroundColorSpan(errorInk),0,length.toString().length,0);styled.setSpan(android.text.style.StyleSpan(Typeface.BOLD),0,length.toString().length,0)}
                count.text=styled
                save.text=if(machine.phase==SavePhase.SAVING)"저장 중…" else if(machine.phase==SavePhase.UNCERTAIN)"저장 결과 확인 필요" else if(message.startsWith("저장되지 않았어요."))"다시 저장" else "메모 저장"
                save.contentDescription=save.text
                footerCaption.text=if(machine.locked)"저장 결과가 확인될 때까지 내용이 유지돼요." else if(length in 1..2000)"서버의 저장 완료를 확인한 뒤 목록에 반영해요." else ""
                footerCaption.visibility=if(footerCaption.text.isEmpty())View.GONE else View.VISIBLE
                save.isEnabled=!machine.locked&&length in 1..2000;save.alpha=if(save.isEnabled)1f else .55f
                fieldError.text=if(length>2000)"2,000자 이내로 줄여주세요." else "본문을 입력해주세요. 공백만으로는 저장할 수 없어요."
                fieldError.visibility=if(inputTouched&&length !in 1..2000)View.VISIBLE else View.GONE
                editor.background=shape(if(machine.locked)Color.rgb(240,240,232) else Color.WHITE,if(fieldError.visibility==View.VISIBLE)errorInk else line)
            }
            editor.addTextChangedListener(object:TextWatcher{
                override fun beforeTextChanged(s:CharSequence?,start:Int,count:Int,after:Int){}
                override fun onTextChanged(s:CharSequence?,start:Int,before:Int,count:Int){body=s.toString();inputTouched=true;if(!machine.locked&&message.startsWith("저장되지 않았어요.")){message="";notice?.visibility=View.GONE};update()}
                override fun afterTextChanged(s:Editable?){}
            });update()
            page.addView(View(this).apply{setBackgroundColor(line)},LinearLayout.LayoutParams(-1,dp(1)))
            page.addView(footerCaption,LinearLayout.LayoutParams(-1,-2).apply{topMargin=dp(16);bottomMargin=dp(8)})
            page.addView(save,LinearLayout.LayoutParams(-1,-2))
        }else{
            when(listState){
                "loading"->content.addView(text("메모를 불러오고 있어요.",14f))
                "error"->{content.addView(text("목록을 불러오지 못했어요.",14f).apply{setTextColor(errorInk)});content.addView(button("다시 불러오기"){loadList()})}
                "refresh-error"->{content.addView(text("목록 갱신 실패 · 저장된 메모는 유지돼요.",14f).apply{setTextColor(Color.rgb(118,82,22))});content.addView(button("목록만 다시 불러오기"){loadList()})}
            }
            if(notes.isEmpty()&&listState=="normal")content.addView(text("첫 생각을 남겨볼까요? 아직 메모가 없어요.",14f).apply{setTextColor(muted);gravity=android.view.Gravity.CENTER;setPadding(0,dp(64),0,dp(64))})
            if(notes.isNotEmpty()){
                val meta=LinearLayout(this)
                meta.addView(text("메모 ${notes.size}개",12f).apply{setTextColor(muted)},LinearLayout.LayoutParams(0,-2,1f))
                meta.addView(text("최신순",12f).apply{setTextColor(muted)})
                content.addView(meta,LinearLayout.LayoutParams(-1,-2).apply{bottomMargin=dp(16)})
            }
            for(note in notes){
                val card=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL;setPadding(dp(18),dp(18),dp(18),dp(18));background=object:GradientDrawable(){override fun draw(canvas:android.graphics.Canvas){super.draw(canvas);canvas.drawRoundRect(0f,dp(18).toFloat(),dp(3).toFloat(),dp(42).toFloat(),dp(2).toFloat(),dp(2).toFloat(),android.graphics.Paint().apply{color=Color.rgb(136,160,128)})}}.apply{setColor(Color.WHITE);cornerRadius=dp(12).toFloat();setStroke(dp(1),line)}}
                card.addView(text(note.body,15f).apply{setLineSpacing(kotlin.math.max(0f,27f*resources.displayMetrics.scaledDensity-paint.fontSpacing),1f);maxLines=3;ellipsize=TextUtils.TruncateAt.END})
                card.addView(text(note.createdAt,11f).apply{
                    setTextColor(muted);setPadding(0,dp(16),0,0)
                    contentDescription="작성 시각 "+runCatching{java.time.format.DateTimeFormatter.ofLocalizedDateTime(java.time.format.FormatStyle.LONG,java.time.format.FormatStyle.MEDIUM).withLocale(java.util.Locale.getDefault()).withZone(java.time.ZoneId.systemDefault()).format(java.time.Instant.parse(note.createdAt))}.getOrDefault(note.createdAt)
                });content.addView(card,LinearLayout.LayoutParams(-1,-2).apply{bottomMargin=dp(14)})
            }
            page.addView(text("기억하고 싶은 순간을 적어보세요.",11f).apply{setTextColor(muted);gravity=android.view.Gravity.CENTER},LinearLayout.LayoutParams(-1,-2).apply{topMargin=dp(16);bottomMargin=dp(8)})
            page.addView(button("새 메모 작성",true,true){composing=true;body="";inputTouched=false;message="";render()},LinearLayout.LayoutParams(-1,-2))
        }
    }
    private fun back() {
        if(machine.locked)return
        fun leave(){body="";composing=false;render()}
        if(body.isEmpty())leave() else AlertDialog.Builder(this).setTitle("작성 중인 메모를 닫을까요?").setMessage("저장하지 않은 내용은 사라집니다.").setNegativeButton("계속 작성",null).setPositiveButton("내용 버리고 목록으로") {_,_->leave()}.show()
    }
    @Deprecated("Platform callback") override fun onBackPressed() {if(composing)back() else super.onBackPressed()}
    private fun loadList() {
        val current=++serial;listState=if(notes.isEmpty())"loading" else "refreshing";render()
        http("GET","/memos") {status,text->
            if(current!=serial)return@http
            val received=if(status==200)runCatching {wireJson.decodeFromString<MemoList>(text).memos}.getOrNull() else null
            if(received!=null){notes=(received+notes).distinctBy {it.id}.sortedWith(compareByDescending<Memo>{it.createdAt}.thenByDescending{it.id});listState="normal"}
            else listState=if(notes.isEmpty())"error" else "refresh-error"
            render()
        }
    }
    private fun save(){
        if(machine.locked || !BodyPolicy.valid(body))return
        try {send(machine.begin(UUID.randomUUID().toString(),body))}
        catch (_:Exception){message="저장 시도 정보를 보존하지 못했어요. 본문은 유지돼요.";render()}
    }
    private fun retry(){
        if(machine.phase!=SavePhase.UNCERTAIN)return
        val attempt=machine.retry();render()
        http("GET","/attempts/${attempt.id}"){status,text->if(status==200)success(text) else if(status==404)send(attempt) else uncertain()}
    }
    private fun send(attempt:Attempt){
        message="저장 결과를 기다리고 있어요.";render()
        http("POST","/memos",wireJson.encodeToString(SaveRequest(attempt.id,attempt.body))){status,text->
            when(status){200,201->success(text);422,413->{try{machine.definitelyNotSaved();message="저장되지 않았어요. 본문을 확인하고 다시 저장해주세요."}catch(_:Exception){machine.uncertain()};render()};else->uncertain()}
        }
    }
    private fun success(text:String){
        try{val memo=wireJson.decodeFromString<MemoResult>(text).memo;machine.complete();notes=(listOf(memo)+notes).distinctBy{it.id};body="";composing=false;message="메모를 저장했어요.";loadList()}
        catch(_:Exception){uncertain()}
    }
    private fun uncertain(){machine.uncertain();composing=true;body=machine.attempt!!.body;message="저장 결과가 불확실해요. 같은 시도를 다시 확인해주세요.";render()}
    private fun http(method:String,path:String,payload:String?=null,done:(Int,String)->Unit){
        network.execute {
            var connection:HttpURLConnection?=null
            val result=try {
                connection=URL("http://127.0.0.1:8080/api/v1$path").openConnection() as HttpURLConnection
                connection.requestMethod=method;connection.connectTimeout=15000;connection.readTimeout=15000
                if(payload!=null){connection.doOutput=true;connection.setRequestProperty("Content-Type","application/json");connection.outputStream.use{it.write(payload.toByteArray(Charsets.UTF_8))}}
                val status=connection.responseCode
                val stream=if(status<400)connection.inputStream else connection.errorStream
                status to (stream?.bufferedReader(Charsets.UTF_8)?.use{it.readText()} ?: "")
            }catch(_:Exception){0 to ""}finally{connection?.disconnect()}
            runOnUiThread {if(!isFinishing && !isDestroyed)done(result.first,result.second)}
        }
    }
    override fun onDestroy(){network.shutdown();super.onDestroy()}
}

import SwiftUI
import Foundation
import Darwin
import Shared
import UIKit

// UIKit's explicit Dynamic Type contract is needed for text controls hosted by
// the iOS26 navigation toolbar; the default SwiftUI toolbar label stays fixed.
private struct ScalableToolbarButton: UIViewRepresentable {
    let title: String
    let action: () -> Void
    final class Coordinator: NSObject {
        var action: () -> Void
        init(_ action: @escaping () -> Void) { self.action = action }
        @objc func invoke() { action() }
    }
    func makeCoordinator() -> Coordinator { Coordinator(action) }
    func makeUIView(context: Context) -> UIButton {
        let button = UIButton(type: .system)
        button.tintColor = UIColor(red: 40.0/255, green: 93.0/255, blue: 73.0/255, alpha: 1)
        button.titleLabel?.adjustsFontForContentSizeCategory = true
        button.titleLabel?.font = .preferredFont(forTextStyle: .body)
        button.setContentHuggingPriority(.required, for: .horizontal)
        button.addTarget(context.coordinator, action: #selector(Coordinator.invoke), for: .touchUpInside)
        return button
    }
    func updateUIView(_ button: UIButton, context: Context) {
        context.coordinator.action = action
        button.setTitle(title, for: .normal)
        button.isEnabled = context.environment.isEnabled
    }
}

private struct ScalableHint: UIViewRepresentable {
    let text: String
    var style: UIFont.TextStyle = .footnote
    var alignment: NSTextAlignment = .left
    func makeUIView(context: Context) -> UILabel {
        let label = UILabel()
        label.numberOfLines = 0
        label.textAlignment = alignment
        label.lineBreakMode = .byWordWrapping
        label.font = .preferredFont(forTextStyle: style)
        label.textColor = UIColor(red:95.0/255,green:110.0/255,blue:102.0/255,alpha:1)
        label.adjustsFontForContentSizeCategory = true
        return label
    }
    func updateUIView(_ label: UILabel, context: Context) { label.text = text }
    func sizeThatFits(_ proposal: ProposedViewSize, uiView: UILabel, context: Context) -> CGSize? {
        guard let width = proposal.width else { return nil }
        return uiView.sizeThatFits(CGSize(width: width, height: .greatestFiniteMagnitude))
    }
}

private struct MemoRow: Codable, Identifiable {
    let id: String
    let body: String
    let createdAt: String
}
private struct MemoListResponse: Decodable { let memos: [MemoRow] }
private struct MemoResponse: Decodable { let memo: MemoRow }
private struct Pending: Codable { let attemptId: String; let body: String }

// Disk operations are performed and checked BEFORE calling the common state machine.
// This in-memory adapter never hides a failed write behind a nonthrowing ObjC callback.
private final class MemoryAttempts: NSObject, AttemptStore {
    var value: Attempt?
    init(_ value: Attempt?) { self.value = value }
    func load() -> Attempt? { value }
    func save(attempt: Attempt) { value = attempt }
    func clear() { value = nil }
}

@MainActor private final class MemoModel: ObservableObject {
    @Published var draft = ""
    @Published var composing = false
    @Published var notes: [MemoRow] = []
    @Published var message = ""
    @Published var listState = "loading"
    @Published var inFlight = false
    @Published var blocked = false
    private var machine: SaveMachine?
    private var listSerial = 0
    private let pendingURL: URL
    var locked: Bool { machine?.locked ?? true }
    var count: Int { Int(BodyPolicy.shared.count(body: draft)) }
    var valid: Bool { BodyPolicy.shared.valid(body: draft) }
    init() {
        pendingURL = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0].appendingPathComponent("memo-v1/pending.json")
        do {
            let pending: Pending? = FileManager.default.fileExists(atPath: pendingURL.path)
                ? try JSONDecoder().decode(Pending.self, from: Data(contentsOf: pendingURL)) : nil
            if let pending {
                guard UUID(uuidString: pending.attemptId) != nil, BodyPolicy.shared.valid(body: pending.body) else { throw CocoaError(.fileReadCorruptFile) }
            }
            let store = MemoryAttempts(pending.map { Attempt(id: $0.attemptId, body: $0.body) })
            machine = SaveMachine(store: store)
            composing = pending != nil
            draft = pending?.body ?? ""
            loadList()
        } catch {
            blocked = true
            message = "저장 시도 복구 정보를 읽지 못했어요. 중복 저장을 막기 위해 새 저장을 중단했어요."
        }
    }
    private func persist(_ pending: Pending) throws {
        guard !FileManager.default.fileExists(atPath: pendingURL.path) else { throw CocoaError(.fileWriteFileExists) }
        try FileManager.default.createDirectory(at: pendingURL.deletingLastPathComponent(), withIntermediateDirectories: true)
        try JSONEncoder().encode(pending).write(to: pendingURL, options: .atomic)
        let descriptor = open(pendingURL.path, O_RDONLY)
        guard descriptor >= 0 else { throw CocoaError(.fileWriteUnknown) }
        defer { close(descriptor) }
        guard fsync(descriptor) == 0 else { throw CocoaError(.fileWriteUnknown) }
    }
    private func clearPending() throws {
        if FileManager.default.fileExists(atPath: pendingURL.path) { try FileManager.default.removeItem(at: pendingURL) }
    }
    func newMemo() { guard !locked else { return }; draft = ""; composing = true; message = "" }
    func edited() {
        if !locked && message.hasPrefix("저장되지 않았어요.") { message = "" }
    }
    func discard() { guard !locked else { return }; draft = ""; composing = false }
    func loadList() {
        listSerial += 1
        let current = listSerial
        listState = notes.isEmpty ? "loading" : "refreshing"
        Task {
            let (status, data) = await request("GET", "/memos")
            guard current == listSerial else { return }
            if status == 200, let received = try? JSONDecoder().decode(MemoListResponse.self, from: data) {
                merge(received.memos); listState = "normal"
            } else { listState = notes.isEmpty ? "error" : "refresh-error" }
        }
    }
    private func merge(_ incoming: [MemoRow]) {
        var map = Dictionary(uniqueKeysWithValues: notes.map { ($0.id, $0) })
        incoming.forEach { map[$0.id] = $0 }
        notes = map.values.sorted { $0.createdAt == $1.createdAt ? $0.id > $1.id : $0.createdAt > $1.createdAt }
    }
    func save() {
        guard let machine, !machine.locked, !inFlight, valid else { return }
        let pending = Pending(attemptId: UUID().uuidString.lowercased(), body: BodyPolicy.shared.normalize(body: draft))
        do {
            try persist(pending)
            // The common begin preconditions were checked above. Disk is durable before its no-fail memory adapter runs.
            let attempt = machine.begin(id: pending.attemptId, body: pending.body)
            send(attempt)
        } catch {
            // A partially completed write is kept for safe reentry; never send without confirmed persistence.
            blocked = FileManager.default.fileExists(atPath: pendingURL.path)
            message = "저장 시도 정보를 보존하지 못했어요. 본문은 유지돼요. 다시 진입해 복구 정보를 확인해주세요."
        }
    }
    func retry() {
        guard let machine, machine.locked, !inFlight, !blocked else { return }
        let attempt = machine.retry()
        inFlight = true
        Task {
            let (status, data) = await request("GET", "/attempts/\(attempt.id)")
            if status == 200 { success(data) }
            else if status == 404 { inFlight = false; send(attempt) }
            else { uncertain() }
        }
    }
    private func send(_ attempt: Attempt) {
        inFlight = true; message = "저장 결과를 기다리고 있어요."
        Task {
            guard let payload = try? JSONEncoder().encode(Pending(attemptId: attempt.id, body: attempt.body)) else { uncertain(); return }
            let (status, data) = await request("POST", "/memos", payload)
            if status == 200 || status == 201 { success(data) }
            else if status == 422 || status == 413 {
                do { try clearPending(); machine?.definitelyNotSaved(); inFlight = false; message = "저장되지 않았어요. 본문을 확인하고 다시 저장해주세요." }
                catch { uncertain() }
            } else { uncertain() }
        }
    }
    private func success(_ data: Data) {
        do {
            let memo = try JSONDecoder().decode(MemoResponse.self, from: data).memo
            try clearPending()
            machine?.complete()
            merge([memo]); draft = ""; composing = false; inFlight = false; message = "메모를 저장했어요."
            loadList()
        } catch { uncertain() }
    }
    private func uncertain() {
        machine?.uncertain(); inFlight = false; composing = true
        draft = machine?.attempt?.body ?? draft
        message = "저장 결과가 불확실해요. 같은 시도를 다시 확인해주세요."
    }
    private func request(_ method: String, _ path: String, _ payload: Data? = nil) async -> (Int, Data) {
        // Platform HTTP composition boundary; tests may select an unreachable local port.
        // Always enforce the same local-only server scope.
        let base = ProcessInfo.processInfo.environment["MEMO_API_BASE_URL"] ?? "http://127.0.0.1:8080/api/v1"
        guard let url = URL(string: base + path), url.scheme == "http", url.host == "127.0.0.1" else { return (0, Data()) }
        var request = URLRequest(url: url)
        request.httpMethod = method; request.timeoutInterval = 15
        if let payload { request.httpBody = payload; request.setValue("application/json", forHTTPHeaderField: "Content-Type") }
        do {
            let (data, response) = try await URLSession.shared.data(for: request)
            return ((response as? HTTPURLResponse)?.statusCode ?? 0, data)
        } catch { return (0, Data()) }
    }
}

private struct MemoActionStyle: ButtonStyle {
    var primary=false
    var back=false
    @Environment(\.isEnabled) private var enabled
    func makeBody(configuration: Configuration) -> some View {
        configuration.label.font(.subheadline.weight(.semibold))
            .padding(.horizontal,12).frame(minHeight:primary ? 52 : 48)
            .frame(maxWidth:primary ? .infinity : nil)
            .foregroundStyle(primary ? Color.white : Color(red:40.0/255,green:93.0/255,blue:73.0/255))
            .background(primary ? Color(red:40.0/255,green:93.0/255,blue:73.0/255) : Color.clear)
            .clipShape(RoundedRectangle(cornerRadius:12))
            .overlay(RoundedRectangle(cornerRadius:12).stroke(primary || back ? Color.clear : Color(red:221.0/255,green:226.0/255,blue:218.0/255),lineWidth:1))
            .opacity(enabled ? (configuration.isPressed ? 0.8 : 1) : 0.55)
    }
}
private struct MemoScroll<Content:View>:View {
    let enabled:Bool
    @ViewBuilder var content:()->Content
    var body:some View { if enabled { ScrollView{content()}.scrollDismissesKeyboard(.immediately) } else {content()} }
}
private struct MemoScreen: View {
    @StateObject private var model=MemoModel()
    @State private var confirmDiscard=false
    @State private var inputTouched=false
    @Environment(\.dynamicTypeSize) private var dynamicTypeSize
    @ScaledMetric(relativeTo:.title) private var titleSize:CGFloat=27
    @ScaledMetric(relativeTo:.body) private var bodySize:CGFloat=15
    @ScaledMetric(relativeTo:.caption) private var smallSize:CGFloat=13
    @ScaledMetric(relativeTo:.body) private var backWidth:CGFloat=64
    @ScaledMetric(relativeTo:.body) private var backHeight:CGFloat=48
    private let green=Color(red:40.0/255,green:93.0/255,blue:73.0/255)
    private let ink=Color(red:36.0/255,green:60.0/255,blue:52.0/255)
    private let muted=Color(red:95.0/255,green:110.0/255,blue:102.0/255)
    private let error=Color(red:154.0/255,green:48.0/255,blue:42.0/255)
    private let line=Color(red:221.0/255,green:226.0/255,blue:218.0/255)
    private let paper=Color(red:250.0/255,green:249.0/255,blue:245.0/255)
    private func accessibleDate(_ value:String)->String {
        let parser=ISO8601DateFormatter();parser.formatOptions=[.withInternetDateTime,.withFractionalSeconds]
        guard let date=parser.date(from:value) else{return "작성 시각 \(value)"}
        return "작성 시각 "+DateFormatter.localizedString(from:date,dateStyle:.long,timeStyle:.medium)
    }
    private func back(){if model.draft.isEmpty{model.discard()}else{confirmDiscard=true}}
    var body: some View {
        NavigationStack {
            GeometryReader { geometry in
                let gutter:CGFloat=geometry.size.width<=600 ? 18 : 36
                MemoScroll(enabled:dynamicTypeSize.isAccessibilitySize){
                VStack(alignment:.leading,spacing:0){
                    VStack(alignment:.leading,spacing:8){
                        HStack{
                            if model.composing{ScalableToolbarButton(title:"‹ 목록",action:back).frame(width:backWidth,height:backHeight).disabled(model.locked).accessibilityLabel("목록").accessibilityIdentifier("back")}
                            else{Text("memo.").font(.system(.title2,design:.serif).italic()).accessibilityLabel("메모")}
                            Spacer();Text(model.composing ? "새로운 기록" : "나의 기록").font(.caption).foregroundStyle(muted).fixedSize(horizontal:false,vertical:true).padding(.horizontal,9).padding(.vertical,4).background(Color(red:233.0/255,green:240.0/255,blue:231.0/255)).clipShape(Capsule())
                        }.frame(minHeight:35).padding(.bottom,14)
                        HStack(alignment:.center){
                            Text(model.composing ? "새 메모" : "메모장").font(.system(size:titleSize,weight:.bold)).accessibilityAddTraits(.isHeader)
                            Spacer()
                            if !model.composing && !model.blocked{Button("새로고침"){model.loadList()}.buttonStyle(MemoActionStyle()).disabled(model.listState=="loading" || model.listState=="refreshing")}
                        }
                        ScalableHint(text:model.composing ? "떠오른 생각을 잊기 전에." : "생각이 머무는 작은 공간.")
                    }.padding(.top,24).padding(.bottom,20)
                    Divider().overlay(line).padding(.bottom,20)
                    MemoScroll(enabled: !dynamicTypeSize.isAccessibilitySize) {
                        VStack(alignment:.leading,spacing:14){
                    if !model.message.isEmpty && !(model.locked && !model.inFlight) {
                        let failed=model.message.hasPrefix("저장되지") || model.message.hasPrefix("저장 시도 정보를")
                        let uncertain=model.locked && !model.inFlight
                        HStack{if model.inFlight{ProgressView().accessibilityHidden(true)};Text(model.message)}.font(.system(size:smallSize)).foregroundStyle(failed ? error : ink)
                            .padding(14).frame(maxWidth:.infinity,alignment:.leading)
                            .background(failed ? Color(red:1,green:240.0/255,blue:237.0/255) : uncertain ? Color(red:1,green:245.0/255,blue:219.0/255) : Color(red:233.0/255,green:240.0/255,blue:231.0/255))
                            .clipShape(RoundedRectangle(cornerRadius:10)).padding(.bottom,14)
                            .accessibilityIdentifier("message").accessibilityAddTraits(.updatesFrequently)
                    }

                            if model.blocked{Text("기존 저장 시도 정보를 보존하고 다시 시도해주세요.")}
                            else if model.composing{
                                if model.locked && !model.inFlight{VStack(alignment:.leading,spacing:12){Text("저장 결과를 확인하지 못했어요. 서버에 저장되었을 수 있어요. 중복 저장을 막기 위해 편집을 잠시 잠갔어요.").font(.system(size:smallSize));Button("같은 저장 결과 다시 확인"){model.retry()}.buttonStyle(MemoActionStyle()).accessibilityIdentifier("retry")}.padding(14).frame(maxWidth:.infinity,alignment:.leading).foregroundStyle(Color(red:118.0/255,green:82.0/255,blue:22.0/255)).background(Color(red:1,green:245.0/255,blue:219.0/255)).clipShape(RoundedRectangle(cornerRadius:12))}
                                Text("메모 본문").font(.system(size:smallSize,weight:.semibold))
                                TextEditor(text:$model.draft).font(.system(size:bodySize+1)).lineSpacing(10)
                                    .scrollContentBackground(.hidden).scrollDismissesKeyboard(.immediately).padding(12).frame(height:220)
                                    .background(model.locked ? Color(red:240.0/255,green:240.0/255,blue:232.0/255) : Color.white)
                                    .clipShape(RoundedRectangle(cornerRadius:12))
                                    .overlay(RoundedRectangle(cornerRadius:12).stroke(inputTouched && !model.valid ? error : line,lineWidth:1))
                                    .overlay(alignment:.topLeading){if model.draft.isEmpty{Text("오늘 기억하고 싶은 것은 무엇인가요?").font(.system(size:bodySize)).foregroundStyle(muted).padding(18).allowsHitTesting(false).accessibilityHidden(true)}}
                                    .disabled(model.locked).accessibilityLabel("메모 본문").accessibilityIdentifier("body")
                                    .onChange(of:model.draft){_ in inputTouched=true;model.edited()}
                                HStack{Spacer();(Text("\(model.count)").foregroundColor(model.count>2000 ? error : muted).fontWeight(model.count>2000 ? .bold : .regular)+Text(" / 2,000").foregroundColor(muted)).font(.caption)}
                                if inputTouched && !model.valid{Text(model.count>2000 ? "2,000자 이내로 줄여주세요." : "본문을 입력해주세요. 공백만으로는 저장할 수 없어요.").font(.system(size:smallSize)).foregroundStyle(error)}
                                Divider().overlay(line).padding(.top,10)
                                ScalableHint(text:"짧은 문장도, 여러 줄의 생각도 좋아요.\n저장이 완료되면 메모 목록으로 돌아가요.")
                            }else{
                                if model.listState=="loading"{ProgressView("메모를 불러오고 있어요.")}
                                if model.listState=="error" || model.listState=="refresh-error"{
                                    Text(model.notes.isEmpty ? "목록을 불러오지 못했어요." : "목록 갱신 실패 · 저장된 메모는 유지돼요.").foregroundStyle(model.notes.isEmpty ? error : Color(red:118.0/255,green:82.0/255,blue:22.0/255))
                                    Button("목록만 다시 불러오기"){model.loadList()}.buttonStyle(MemoActionStyle())
                                }
                                if model.notes.isEmpty && model.listState=="normal"{Text("첫 생각을 남겨볼까요? 아직 메모가 없어요.").foregroundStyle(muted).frame(maxWidth:.infinity).padding(.vertical,64)}
                                if !model.notes.isEmpty{HStack{Text("메모 \(model.notes.count)개");Spacer();Text("최신순")}.font(.caption).foregroundStyle(muted)}
                                ForEach(model.notes){memo in
                                    VStack(alignment:.leading,spacing:16){
                                        Text(memo.body).font(.system(size:bodySize)).lineSpacing(9).lineLimit(3)
                                        Text(memo.createdAt).font(.caption2).foregroundStyle(muted).accessibilityLabel(accessibleDate(memo.createdAt))
                                    }.padding(18).frame(maxWidth:.infinity,alignment:.leading).background(.white)
                                    .clipShape(RoundedRectangle(cornerRadius:12)).overlay(RoundedRectangle(cornerRadius:12).stroke(line,lineWidth:1)).overlay(alignment:.topLeading){RoundedRectangle(cornerRadius:2).fill(Color(red:136.0/255,green:160.0/255,blue:128.0/255)).frame(width:3,height:24).offset(y:18)}
                                }
                            }
                        }.frame(maxWidth:.infinity,alignment:.leading).padding(.bottom,20)
                    }
                    if !model.blocked{
                        VStack(spacing:8){
                            Divider().overlay(line)
                            if model.composing{
                                if model.locked || model.valid{ScalableHint(text:model.locked ? "저장 결과가 확인될 때까지 내용이 유지돼요." : "서버의 저장 완료를 확인한 뒤 목록에 반영해요.",alignment:.center)}
                                Button(model.inFlight ? "저장 중…" : model.locked ? "저장 결과 확인 필요" : model.message.hasPrefix("저장되지 않았어요.") ? "다시 저장" : "메모 저장"){model.save()}.buttonStyle(MemoActionStyle(primary:true)).disabled(model.locked || !model.valid || model.inFlight).accessibilityIdentifier("save")
                            }else{
                                ScalableHint(text:"기억하고 싶은 순간을 적어보세요.",alignment:.center)
                                Button{inputTouched=false;model.newMemo()}label:{Label("새 메모 작성",systemImage:"plus")}.buttonStyle(MemoActionStyle(primary:true)).accessibilityIdentifier("create")
                            }
                        }.padding(.top,16).padding(.bottom,16)
                    }
                }.padding(.horizontal,gutter).foregroundStyle(ink).tint(green)
                }
            }.background(paper.ignoresSafeArea()).toolbar(.hidden,for:.navigationBar)
                .confirmationDialog("작성 중인 메모를 닫을까요?",isPresented:$confirmDiscard,titleVisibility:.visible){
                    Button("내용 버리고 목록으로",role:.destructive){model.discard()};Button("계속 작성",role:.cancel){}
                }message:{Text("저장하지 않은 내용은 사라집니다.")}
        }
    }
}

@main struct MemoApplication: App { var body: some Scene { WindowGroup { MemoScreen() } } }

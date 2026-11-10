import SwiftUI
import WebKit
import UniformTypeIdentifiers

@main struct TeumApp: App {
    var body: some Scene { WindowGroup { MemoView().ignoresSafeArea(.container, edges: .bottom) } }
}

struct MemoView: UIViewRepresentable {
    func makeCoordinator() -> Coordinator { Coordinator() }
    func makeUIView(context: Context) -> WKWebView {
        let config = WKWebViewConfiguration()
        let script = "window.MEMO_NATIVE_DEFAULT_SERVER = 'http://127.0.0.1:8910';"
        config.userContentController.addUserScript(WKUserScript(source: script, injectionTime: .atDocumentStart, forMainFrameOnly: true))
        config.userContentController.add(context.coordinator, name: "exportFile")
        let web = WKWebView(frame: .zero, configuration: config)
        web.navigationDelegate = context.coordinator
        web.isOpaque = false
        web.backgroundColor = UIColor(red: 250/255, green: 250/255, blue: 247/255, alpha: 1)
        web.scrollView.contentInsetAdjustmentBehavior = .never
        if let url = Bundle.main.url(forResource: "index", withExtension: "html", subdirectory: "web") {
            web.loadFileURL(url, allowingReadAccessTo: url.deletingLastPathComponent())
        }
        return web
    }
    func updateUIView(_ web: WKWebView, context: Context) {}

    final class Coordinator: NSObject, WKNavigationDelegate, WKScriptMessageHandler, UIDocumentPickerDelegate {
        var temporaryFile: URL?
        func webView(_ web: WKWebView, decidePolicyFor navigationAction: WKNavigationAction, decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
            guard let url = navigationAction.request.url else { decisionHandler(.cancel); return }
            decisionHandler(url.isFileURL || url.absoluteString == "about:blank" ? .allow : .cancel)
        }
        func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
            guard message.frameInfo.isMainFrame, let body = message.body as? [String: String],
                  let text = body["content"], let name = body["name"], text.utf8.count < 8_000_000 else { return }
            let safeName = name.replacingOccurrences(of: "/", with: "_")
            let directory = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
            do {
                try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
                let file = directory.appendingPathComponent(safeName)
                try text.write(to: file, atomically: true, encoding: .utf8)
                temporaryFile = file
                let picker = UIDocumentPickerViewController(forExporting: [file], asCopy: true)
                picker.delegate = self
                guard let scene = UIApplication.shared.connectedScenes.first as? UIWindowScene,
                      let root = scene.windows.first(where: \.isKeyWindow)?.rootViewController else { return }
                var presenter = root
                while let presented = presenter.presentedViewController { presenter = presented }
                presenter.present(picker, animated: true)
            } catch { /* Original memo remains in local storage; export can be retried. */ }
        }
        func documentPickerWasCancelled(_ controller: UIDocumentPickerViewController) { cleanup() }
        func documentPicker(_ controller: UIDocumentPickerViewController, didPickDocumentsAt urls: [URL]) { cleanup() }
        func cleanup() {
            if let file = temporaryFile { try? FileManager.default.removeItem(at: file.deletingLastPathComponent()) }
            temporaryFile = nil
        }
    }
}

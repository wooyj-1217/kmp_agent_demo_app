import XCTest
import WebKit
import UIKit

/// Host-app integration test: bundled screen, actual WKWebView storage and localhost server.
final class MemoSmokeTests: XCTestCase {
    var web: WKWebView!
    func findWeb(_ view: UIView) -> WKWebView? {
        if let web = view as? WKWebView { return web }
        return view.subviews.compactMap { findWeb($0) }.first
    }
    func js(_ source: String) async throws -> Any? {
        try await withCheckedThrowingContinuation { continuation in
            DispatchQueue.main.async {
                self.web.evaluateJavaScript(source) { value, error in
                    if let error { continuation.resume(throwing: error) }
                    else { continuation.resume(returning: value) }
                }
            }
        }
    }
    func waitFor(_ condition: String) async throws {
        for _ in 0..<100 {
            if (try? await js("Boolean(\(condition))")) as? Bool == true { return }
            try await Task.sleep(nanoseconds: 200_000_000)
        }
        let diagnostic = try? await js("document.getElementById('auth-error').textContent + ' / ' + document.getElementById('sync-label').textContent")
        XCTFail("Timeout: \(condition), \(String(describing: diagnostic))")
        throw NSError(domain: "TeumSmoke", code: 1)
    }
    func testLoginEditSyncReloadAndRestore() async throws {
        for _ in 0..<50 {
            web = await MainActor.run {
                UIApplication.shared.connectedScenes.compactMap { $0 as? UIWindowScene }.flatMap(\.windows).compactMap { self.findWeb($0) }.first
            }
            if web != nil { break }
            try await Task.sleep(nanoseconds: 200_000_000)
        }
        XCTAssertNotNil(web)
        guard web != nil else { return }
        try await waitFor("typeof newNote === 'function'")
        _ = try await js("if(!session){showAccount();document.getElementById('email').value='qa@teum.test';document.getElementById('password').value='Teum-local-qa-2026!';document.getElementById('auth-submit').click();}")
        try await waitFor("session && session.email === 'qa@teum.test'")
        try await waitFor("!syncing")
        _ = try await js("newNote();document.getElementById('note-title').value='iOS native QA';document.getElementById('note-body').value='Native WKWebView sync survives reload';edited();sync();void 0;")
        try await waitFor("!syncing && queue.length===0")
        let text = try await js("notes.find(n=>n.title==='iOS native QA').body") as? String
        XCTAssertEqual(text,"Native WKWebView sync survives reload")
        _ = try await js("window.__beforeReload=true")
        await MainActor.run { _ = web.reload() }
        try await waitFor("typeof window.__beforeReload === 'undefined' && typeof notes !== 'undefined' && notes.some(n=>n.title==='iOS native QA')")
        _ = try await js("current=notes.find(n=>n.title==='iOS native QA').id;save({...notes.find(n=>n.id===current),deleted:true});sync();void 0;")
        try await waitFor("!syncing && queue.length===0")
        let deleted = try await js("notes.find(n=>n.id===current).deleted") as? Bool
        XCTAssertEqual(deleted,true)
        _ = try await js("save({...notes.find(n=>n.id===current),deleted:false});sync();void 0;")
        try await waitFor("!syncing && queue.length===0")
        let restored = try await js("notes.find(n=>n.id===current).deleted") as? Bool
        XCTAssertEqual(restored,false)
    }
}

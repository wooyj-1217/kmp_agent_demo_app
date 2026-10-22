import XCTest

final class MemoUITests: XCTestCase {
    private func control(_ value: [String: Any]? = nil) throws -> [String: Any] {
        var request = URLRequest(url: URL(string: "http://127.0.0.1:18082/")!)
        if let value { request.httpMethod = "POST"; request.httpBody = try JSONSerialization.data(withJSONObject: value) }
        let done = DispatchSemaphore(value: 0)
        var result: Data?; var failure: Error?
        URLSession.shared.dataTask(with: request) { data, _, error in result = data; failure = error; done.signal() }.resume()
        XCTAssertEqual(done.wait(timeout: .now() + 30), .success)
        if let failure { throw failure }
        return try JSONSerialization.jsonObject(with: XCTUnwrap(result)) as! [String: Any]
    }
    private func acceptanceApp() -> XCUIApplication {
        let app = XCUIApplication()
        app.launchEnvironment["MEMO_API_BASE_URL"] = "http://127.0.0.1:18080/api/v1"
        app.launch()
        return app
    }
    private func compose(_ app: XCUIApplication, _ text: String) {
        XCTAssertTrue(app.buttons["create"].waitForExistence(timeout: 20))
        app.buttons["create"].tap()
        XCTAssertTrue(app.textViews["body"].waitForExistence(timeout: 10))
        app.textViews["body"].tap(); app.textViews["body"].typeText(text)
        dismissKeyboardIntroduction(app)
    }
    private func dismissKeyboardIntroduction(_ app: XCUIApplication) {
        // First-use iOS keyboard tutorial belongs to the fresh simulator, not the app.
        if app.staticTexts["Speed up your typing by sliding your finger across the letters to compose a word."].exists,
           app.buttons["Continue"].exists { app.buttons["Continue"].tap() }
    }
    private func rows() throws -> [[String: Any]] { try control()["rows"] as! [[String: Any]] }
    private func postCount() throws -> Int {
        (try control()["requests"] as! [[String: Any]]).filter { $0["method"] as? String == "POST" }.count
    }
    func testAcceptanceFaultsAndPersistence() throws {
        _ = try control(["reset": true, "rules": [["method": "GET", "path": "/api/v1/memos", "delay": 3, "remaining": 1]]])
        let app = acceptanceApp()
        XCTAssertTrue(app.staticTexts["메모를 불러오고 있어요."].waitForExistence(timeout: 10))
        XCTAssertTrue(app.staticTexts["첫 생각을 남겨볼까요? 아직 메모가 없어요."].waitForExistence(timeout: 15))
        compose(app, "  first\nsecond  ")
        _ = try control(["rules": [["method": "POST", "path": "/api/v1/memos", "delay": 3, "remaining": 1]]])
        app.buttons["save"].tap(withNumberOfTaps: 2, numberOfTouches: 1)
        XCTAssertTrue(app.textViews["body"].exists)
        XCTAssertFalse(app.textViews["body"].isEnabled)
        XCTAssertTrue(app.staticTexts["first\nsecond"].waitForExistence(timeout: 20))
        XCTAssertEqual(try postCount(), 1)
        XCTAssertEqual(try rows().first?["body"] as? String, "first\nsecond")
        // A definite rejection never reaches the real server and leaves an editable draft.
        _ = try control(["rules": [["method": "POST", "path": "/api/v1/memos", "status": 422, "remaining": 1]]])
        compose(app, "retained")
        app.buttons["save"].tap()
        XCTAssertTrue(app.staticTexts["저장되지 않았어요. 본문을 확인하고 다시 저장해주세요."].waitForExistence(timeout: 15))
        XCTAssertEqual(app.textViews["body"].value as? String, "retained")
        XCTAssertTrue(app.textViews["body"].isEnabled)
        XCTAssertEqual(try rows().count, 1)
        app.textViews["body"].tap(); app.textViews["body"].typeText(" corrected")
        dismissKeyboardIntroduction(app)
        app.buttons["save"].tap()
        XCTAssertTrue(app.staticTexts["retained corrected"].waitForExistence(timeout: 20))
        // Commit first, discard the actual HTTP result, then restart both server and app.
        _ = try control(["rules": [["method": "POST", "path": "/api/v1/memos", "drop_after_commit": true]]])
        compose(app, "committed response lost")
        app.buttons["save"].tap()
        XCTAssertTrue(app.buttons["retry"].waitForExistence(timeout: 25))
        XCTAssertFalse(app.textViews["body"].isEnabled)
        let before = try rows().filter { $0["body"] as? String == "committed response lost" }
        XCTAssertEqual(before.count, 1)
        app.terminate()
        _ = try control(["restart": true, "rules": []])
        app.launch()
        XCTAssertTrue(app.buttons["retry"].waitForExistence(timeout: 20))
        XCTAssertEqual(app.textViews["body"].value as? String, "committed response lost")
        app.buttons["retry"].tap()
        XCTAssertTrue(app.staticTexts["committed response lost"].waitForExistence(timeout: 20))
        XCTAssertEqual(try rows().filter { $0["body"] as? String == "committed response lost" }.first?["id"] as? Int, before.first?["id"] as? Int)
        XCTAssertEqual(try rows().count, 3)
        // A fresh identical body is an independent attempt.
        compose(app, "committed response lost"); app.buttons["save"].tap()
        XCTAssertTrue(app.buttons["create"].waitForExistence(timeout: 20))
        XCTAssertEqual(try rows().filter { $0["body"] as? String == "committed response lost" }.count, 2)
        // Save succeeds even when its following list fetch fails; retry must be GET only.
        _ = try control(["rules": [["method": "GET", "path": "/api/v1/memos", "status": 503]]])
        compose(app, "saved despite list failure"); app.buttons["save"].tap()
        XCTAssertTrue(app.staticTexts["목록 갱신 실패 · 저장된 메모는 유지돼요."].waitForExistence(timeout: 20))
        XCTAssertTrue(app.staticTexts["saved despite list failure"].exists)
        let count = try postCount()
        _ = try control(["rules": []])
        app.buttons["목록만 다시 불러오기"].tap()
        let gone = XCTNSPredicateExpectation(predicate: NSPredicate(format: "exists == false"), object: app.buttons["목록만 다시 불러오기"])
        wait(for: [gone], timeout: 15)
        XCTAssertEqual(try postCount(), count)
        XCTAssertEqual(try rows().count, 5)
        app.terminate(); _ = try control(["restart": true]); app.launch()
        XCTAssertTrue(app.staticTexts["saved despite list failure"].waitForExistence(timeout: 20))
        app.terminate()
        // Initial GET failure has a recoverable empty-state path.
        _ = try control(["reset": true, "rules": [["method": "GET", "path": "/api/v1/memos", "status": 503]]])
        app.launch()
        XCTAssertTrue(app.staticTexts["목록을 불러오지 못했어요."].waitForExistence(timeout: 15))
        _ = try control(["rules": []]); app.buttons["목록만 다시 불러오기"].tap()
        XCTAssertTrue(app.staticTexts["첫 생각을 남겨볼까요? 아직 메모가 없어요."].waitForExistence(timeout: 15))
    }

    func testAcceptanceOrderBoundaryAndDiscard() throws {
        _ = try control(["reset": true, "seed_order": true])
        let app = acceptanceApp()
        XCTAssertTrue(app.staticTexts["newest date"].waitForExistence(timeout: 20))
        func assertOrder() {
            XCTAssertLessThan(app.staticTexts["newest date"].frame.minY, app.staticTexts["tie newer id"].frame.minY)
            XCTAssertLessThan(app.staticTexts["tie newer id"].frame.minY, app.staticTexts["tie older id"].frame.minY)
        }
        assertOrder(); app.buttons["새로고침"].tap(); assertOrder()
        compose(app, " \n\t ")
        XCTAssertFalse(app.buttons["save"].isEnabled)
        app.buttons["목록"].tap()
        if app.buttons["계속 작성"].exists { app.buttons["계속 작성"].tap() }
        else { app.otherElements["PopoverDismissRegion"].tap() } // Native iOS26 outside-tap cancel region.
        XCTAssertTrue(app.textViews["body"].exists)
        app.buttons["목록"].tap(); app.buttons["내용 버리고 목록으로"].tap()
        compose(app, "a")
        XCTAssertTrue(app.buttons["save"].isEnabled)
        app.textViews["body"].typeText(String(repeating: "a", count: 1999))
        XCTAssertTrue(app.buttons["save"].isEnabled)
        app.buttons["save"].tap()
        XCTAssertTrue(app.buttons["create"].waitForExistence(timeout: 20))
        XCTAssertEqual(try rows().first?["body"] as? String, String(repeating: "a", count: 2000))
    }
    func testAcceptanceUnicodeAndInFlightRestart() throws {
        _ = try control(["reset": true])
        let app = acceptanceApp()
        compose(app, "한👩🏽‍💻🇰🇷\n b")
        XCTAssertTrue(app.staticTexts["6 / 2,000"].exists)
        let entered = try XCTUnwrap(app.textViews["body"].value as? String)
        _ = try control(["rules": [["method": "POST", "path": "/api/v1/memos", "delay": 6, "remaining": 1]]])
        app.buttons["save"].tap()
        XCTAssertFalse(app.textViews["body"].isEnabled)
        XCTAssertEqual(try rows().count, 0)
        app.terminate() // Terminate during POST, before the server commits its delayed request.
        let committed = expectation(description: "real delayed server commit")
        DispatchQueue.global().async {
            for _ in 0..<100 {
                if (try? self.rows().count) == 1 { committed.fulfill(); return }
                Thread.sleep(forTimeInterval: 0.1)
            }
        }
        wait(for: [committed], timeout: 15)
        app.launch()
        XCTAssertTrue(app.buttons["retry"].waitForExistence(timeout: 20))
        XCTAssertEqual(app.textViews["body"].value as? String, entered)
        let before = try postCount()
        app.buttons["retry"].tap()
        XCTAssertTrue(app.buttons["create"].waitForExistence(timeout: 20))
        XCTAssertEqual(try postCount(), before)
        XCTAssertEqual(try rows().count, 1)
        XCTAssertEqual(try rows().first?["body"] as? String, entered)
        let capture = XCTAttachment(screenshot: app.screenshot()); capture.lifetime = .keepAlways; add(capture)
    }
    func testAcceptanceLongPreview() throws {
        _ = try control(["reset": true])
        let app = acceptanceApp()
        let body = "preview line one\npreview line two\npreview line three\npreview line four\npreview line five"
        compose(app, body); app.buttons["save"].tap()
        XCTAssertTrue(app.staticTexts[body].waitForExistence(timeout: 20))
        // Baseline body15pt / line27pt: three native lines are about72pt, not old compact65pt.
        XCTAssertLessThanOrEqual(app.staticTexts[body].frame.height, 90)
        XCTAssertGreaterThan(app.staticTexts[body].frame.height, 60)
        XCTAssertEqual(try rows().count, 1)
        XCTAssertEqual(try rows().first?["body"] as? String, body)
        let capture = XCTAttachment(screenshot: app.screenshot()); capture.lifetime = .keepAlways; add(capture)
    }
    func testAcceptanceFailureEditKeepsFocus() throws {
        _ = try control(["reset": true, "rules": [["method": "POST", "path": "/api/v1/memos", "status": 422, "remaining": 1]]])
        let app = acceptanceApp()
        compose(app, "failed draft"); app.buttons["save"].tap()
        let error = app.staticTexts["저장되지 않았어요. 본문을 확인하고 다시 저장해주세요."]
        XCTAssertTrue(error.waitForExistence(timeout: 15))
        app.textViews["body"].tap(); app.textViews["body"].typeText(" changed")
        dismissKeyboardIntroduction(app)
        XCTAssertFalse(error.exists)
        XCTAssertEqual(app.textViews["body"].value as? String, "failed draft changed")
        XCTAssertTrue(app.keyboards.firstMatch.exists)
        app.buttons["save"].tap()
        XCTAssertTrue(app.staticTexts["failed draft changed"].waitForExistence(timeout: 20))
        XCTAssertEqual(try rows().count, 1)
    }
    @MainActor func testAcceptanceAppAccessibilityAudit() throws {
        _ = try control(["reset": true])
        let app = acceptanceApp()
        XCTAssertTrue(app.staticTexts["첫 생각을 남겨볼까요? 아직 메모가 없어요."].waitForExistence(timeout: 20))
        if #available(iOS 17.0, *) {
            var issues: [[String: String]] = []
            func audit(_ screen: String) throws {
                try app.performAccessibilityAudit { issue in
                    issues.append(["screen": screen, "summary": issue.compactDescription,
                                   "detail": issue.detailedDescription, "element": issue.element?.debugDescription ?? "UNKNOWN"])
                    // Collect every issue; the explicit empty assertion below still fails the test.
                    return true
                }
            }
            try audit("empty")
            _ = try control(["seed_order": true]); app.buttons["새로고침"].tap()
            XCTAssertTrue(app.staticTexts["newest date"].waitForExistence(timeout: 15))
            try audit("list")
            compose(app, "accessibility draft")
            app.textViews["body"].swipeDown()
            Thread.sleep(forTimeInterval:1) // audit visible form after keyboard dismissal, not obscured text
            try audit("create")
            let external = issues.filter { $0["detail", default: ""].contains("TUIPredictionViewCell") && $0["element", default: ""].contains("SystemInputAssistantView") && $0["element", default: ""].contains("Typing Predictions") }
            let appIssues = issues.filter { !external.contains($0) }
            let data = try JSONSerialization.data(withJSONObject: ["allIssues": issues, "externalSystemKeyboardIssues": external, "appIssues": appIssues], options: .prettyPrinted)
            let attachment = XCTAttachment(data: data, uniformTypeIdentifier: "public.json")
            attachment.name = "Accessibility audit issues"; attachment.lifetime = .keepAlways; add(attachment)
            XCTAssertTrue(appIssues.isEmpty, "All application audit issues must be fixed: \(appIssues)")
        } else { throw XCTSkip("Accessibility audit requires iOS17") }
    }
    override func setUp() { super.setUp(); continueAfterFailure = false }
    func testSaveLengthBoundaryAndDraftNotRestored() throws {
        continueAfterFailure = false
        let app = XCUIApplication()
        app.launch()
        XCTAssertTrue(app.buttons["create"].waitForExistence(timeout: 30))
        app.buttons["create"].tap()
        let body = app.textViews["body"]
        XCTAssertTrue(body.waitForExistence(timeout: 10))
        body.tap()
        body.typeText(String(repeating: "a", count: 2001))
        XCTAssertFalse(app.buttons["save"].isEnabled)
        // Terminating an ordinary draft must not restore it on a fresh process.
        app.terminate()
        app.launch()
        XCTAssertTrue(app.buttons["create"].waitForExistence(timeout: 20))
        app.buttons["create"].tap()
        XCTAssertTrue(body.waitForExistence(timeout: 10))
        XCTAssertEqual(body.value as? String, "")
        body.tap()
        let text = "iOS actual save \(UUID().uuidString)"
        body.typeText(text)
        app.buttons["save"].tap()
        XCTAssertTrue(app.buttons["create"].waitForExistence(timeout: 30))
        XCTAssertTrue(app.staticTexts[text].waitForExistence(timeout: 15))
        let screenshot = XCTAttachment(screenshot: app.screenshot())
        screenshot.lifetime = .keepAlways
        add(screenshot)
        app.terminate()
        app.launch()
        XCTAssertTrue(app.staticTexts[text].waitForExistence(timeout: 30))
    }

    func testUncertainAttemptRestoresAfterProcessRestart() throws {
        let app = XCUIApplication()
        app.launchEnvironment["MEMO_API_BASE_URL"] = "http://127.0.0.1:1/api/v1"
        app.launch()
        XCTAssertTrue(app.buttons["create"].waitForExistence(timeout: 30))
        app.buttons["create"].tap()
        let body = app.textViews["body"]
        XCTAssertTrue(body.waitForExistence(timeout: 10))
        body.tap()
        let text = "iOS uncertain recovery \(UUID().uuidString)"
        body.typeText(text)
        app.buttons["save"].tap()
        XCTAssertTrue(app.buttons["retry"].waitForExistence(timeout: 30))
        XCTAssertFalse(body.isEnabled)
        app.terminate()
        app.launchEnvironment.removeValue(forKey: "MEMO_API_BASE_URL")
        app.launch()
        XCTAssertTrue(app.buttons["retry"].waitForExistence(timeout: 30))
        XCTAssertEqual(body.value as? String, text)
        XCTAssertFalse(app.buttons["save"].isEnabled)
        app.buttons["retry"].tap()
        XCTAssertTrue(app.buttons["create"].waitForExistence(timeout: 30))
        XCTAssertTrue(app.staticTexts[text].waitForExistence(timeout: 15))
        app.terminate()
        app.launch()
        XCTAssertTrue(app.staticTexts[text].waitForExistence(timeout: 30))
        XCTAssertEqual(app.staticTexts.matching(NSPredicate(format: "label == %@", text)).count, 1)
    }
    func testDesignConformance() throws {
        _ = try control(["reset":true,"rules":[]])
        let app=acceptanceApp()
        func shot(_ name:String){Thread.sleep(forTimeInterval:1);let attachment=XCTAttachment(screenshot:app.screenshot());attachment.name="design-"+name;attachment.lifetime = .keepAlways;add(attachment)}
        XCTAssertTrue(app.staticTexts["첫 생각을 남겨볼까요? 아직 메모가 없어요."].waitForExistence(timeout:20));shot("empty-list")
        app.buttons["create"].tap()
        XCTAssertTrue(app.textViews["body"].waitForExistence(timeout:10));XCTAssertFalse(app.buttons["save"].isEnabled)
        XCTAssertLessThan(app.buttons["back"].frame.maxY,app.textViews["body"].frame.minY);shot("empty-create")
        app.textViews["body"].tap();app.textViews["body"].typeText("a");dismissKeyboardIntroduction(app);app.textViews["body"].typeText(XCUIKeyboardKey.delete.rawValue)
        XCTAssertTrue(app.staticTexts["본문을 입력해주세요. 공백만으로는 저장할 수 없어요."].exists);shot("empty-invalid")
        app.textViews["body"].tap();app.textViews["body"].typeText("디자인 비교 메모\n두 번째 줄");dismissKeyboardIntroduction(app)
        app.textViews["body"].swipeDown();shot("input")
        _ = try control(["rules":[["method":"POST","path":"/api/v1/memos","delay":4,"status":422,"remaining":1]]])
        app.buttons["save"].tap()
        XCTAssertTrue(app.buttons["save"].waitForExistence(timeout:5));XCTAssertFalse(app.buttons["save"].isEnabled);XCTAssertFalse(app.textViews["body"].isEnabled);shot("saving")
        XCTAssertTrue(app.staticTexts["저장되지 않았어요. 본문을 확인하고 다시 저장해주세요."].waitForExistence(timeout:20));shot("failed")
        app.textViews["body"].tap();app.textViews["body"].typeText(" · 수정");app.textViews["body"].swipeDown()
        XCTAssertFalse(app.staticTexts["저장되지 않았어요. 본문을 확인하고 다시 저장해주세요."].exists)
        app.buttons["save"].tap();XCTAssertTrue(app.buttons["create"].waitForExistence(timeout:20));XCTAssertEqual(try rows().count,1);shot("list")
        _ = try control(["rules":[["method":"POST","path":"/api/v1/memos","drop_after_commit":true]]])
        compose(app,"불확실 결과 디자인 확인");app.buttons["save"].tap();XCTAssertTrue(app.buttons["retry"].waitForExistence(timeout:25));shot("uncertain")
        _ = try control(["rules":[]]);app.buttons["retry"].tap();XCTAssertTrue(app.buttons["create"].waitForExistence(timeout:20));XCTAssertEqual(try rows().count,2)
    }

    func testDesignListFailureAppearance() throws {
        _ = try control(["reset":true,"rules":[["method":"GET","path":"/api/v1/memos","status":503]]])
        let app=acceptanceApp()
        XCTAssertTrue(app.staticTexts["목록을 불러오지 못했어요."].waitForExistence(timeout:20))
        let initial=XCTAttachment(screenshot:app.screenshot());initial.name="design-initial-error";initial.lifetime = .keepAlways;add(initial)
        _ = try control(["reset":true,"seed_order":true,"rules":[]])
        app.buttons["목록만 다시 불러오기"].tap()
        XCTAssertTrue(app.staticTexts["메모 3개"].waitForExistence(timeout:20))
        _ = try control(["rules":[["method":"GET","path":"/api/v1/memos","status":503]]])
        app.buttons["새로고침"].tap()
        XCTAssertTrue(app.staticTexts["목록 갱신 실패 · 저장된 메모는 유지돼요."].waitForExistence(timeout:20))
        XCTAssertTrue(app.staticTexts["메모 3개"].exists)
        let refresh=XCTAttachment(screenshot:app.screenshot());refresh.name="design-refresh-error";refresh.lifetime = .keepAlways;add(refresh)
        _ = try control(["rules":[]]);app.buttons["목록만 다시 불러오기"].tap()
        XCTAssertTrue(app.staticTexts["메모 3개"].waitForExistence(timeout:20));XCTAssertEqual(try postCount(),0)
    }
    func testDesignInvalidAppearance() throws {
        _ = try control(["reset":true]);let app=acceptanceApp()
        compose(app,String(repeating:"a",count:2001));app.textViews["body"].swipeDown();Thread.sleep(forTimeInterval:1)
        XCTAssertFalse(app.buttons["save"].isEnabled)
        XCTAssertFalse(app.keyboards.firstMatch.exists)
        XCTAssertLessThanOrEqual(app.textViews["body"].frame.height,230)
        XCTAssertEqual((app.textViews["body"].value as? String)?.count,2001)
        XCTAssertTrue(app.staticTexts["2,001 / 2,000"].exists)
        let capture=XCTAttachment(screenshot:app.screenshot());capture.name="design-invalid";capture.lifetime = .keepAlways;add(capture)
    }

}

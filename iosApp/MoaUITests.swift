import XCTest

final class YeobackUITests: XCTestCase {
    func testCreateDiscardAndPersistAcrossLaunch() {
        let app = XCUIApplication()
        app.launchArguments = ["--uitest"]
        app.launch()
        let title = "iOS 기록 \(Int(Date().timeIntervalSince1970))"
        let newMemo = app.buttons["new-memo"]
        XCTAssertTrue(newMemo.waitForExistence(timeout: 30))
        newMemo.tap()
        let titleField = app.descendants(matching: .any)["memo-title"]
        XCTAssertTrue(titleField.waitForExistence(timeout: 10))
        titleField.tap()
        titleField.typeText(title)
        let body = app.descendants(matching: .any)["memo-body"]
        XCTAssertTrue(body.waitForExistence(timeout: 10))
        body.tap()
        body.typeText("첫 줄\n다음 줄도 기억하기")
        app.buttons["save-memo"].tap()
        let returnedCard = app.buttons.matching(NSPredicate(format: "label CONTAINS %@", title)).firstMatch
        XCTAssertTrue(returnedCard.waitForExistence(timeout: 10))
        XCTAssertFalse(returnedCard.label.contains("버릴 변경"))
        XCTAssertTrue(returnedCard.label.contains("첫 줄"))
        XCTAssertTrue(returnedCard.label.contains("다음 줄도 기억하기"))
        returnedCard.tap()
        XCTAssertTrue(app.buttons["pin-memo"].waitForExistence(timeout: 10))
        app.buttons["pin-memo"].tap()
        app.buttons["editor-back"].tap()
        app.descendants(matching: .any)["nav-pinned"].tap()
        let pinnedCard = app.buttons.matching(NSPredicate(format: "label CONTAINS %@", title)).firstMatch
        XCTAssertTrue(pinnedCard.waitForExistence(timeout: 10))
        XCTAssertTrue(pinnedCard.label.contains("고정됨"))
        pinnedCard.tap()
        app.buttons["trash-memo"].tap()
        XCTAssertFalse(app.buttons.matching(NSPredicate(format: "label CONTAINS %@", title)).firstMatch.exists)
        app.descendants(matching: .any)["nav-trash"].tap()
        let trashedCard = app.buttons.matching(NSPredicate(format: "label CONTAINS %@", title)).firstMatch
        XCTAssertTrue(trashedCard.waitForExistence(timeout: 10))
        trashedCard.tap()
        app.buttons["restore-memo"].tap()
        let restoredCard = app.buttons.matching(NSPredicate(format: "label CONTAINS %@", title)).firstMatch
        XCTAssertTrue(restoredCard.waitForExistence(timeout: 10))
        XCTAssertTrue(restoredCard.label.contains("고정됨"))
        XCTAssertFalse(restoredCard.label.contains("버릴 변경"))
        XCTAssertTrue(restoredCard.label.contains("첫 줄"))
        XCTAssertTrue(restoredCard.label.contains("다음 줄도 기억하기"))
        app.terminate()
        app.launch()
        let persistedCard = app.buttons.matching(NSPredicate(format: "label CONTAINS %@", title)).firstMatch
        XCTAssertTrue(persistedCard.waitForExistence(timeout: 30))
        XCTAssertTrue(persistedCard.label.contains("고정됨"))
        XCTAssertTrue(persistedCard.label.contains("첫 줄"))
        XCTAssertTrue(persistedCard.label.contains("다음 줄도 기억하기"))
        persistedCard.tap()
        XCTAssertTrue(app.descendants(matching: .any)["memo-title"].waitForExistence(timeout: 10))
        let editorScreenshot = XCTAttachment(screenshot: app.screenshot())
        editorScreenshot.name = "재실행 후 원문 편집 화면"
        editorScreenshot.lifetime = .keepAlways
        add(editorScreenshot)
        app.descendants(matching: .any)["memo-title"].tap()
        app.descendants(matching: .any)["memo-title"].typeText(" 버릴 변경")
        app.buttons["editor-back"].tap()
        XCTAssertTrue(app.buttons["keep-editing"].waitForExistence(timeout: 5))
        app.buttons["keep-editing"].tap()
        app.buttons["editor-back"].tap()
        app.buttons["discard-draft"].tap()
        let discardedCard = app.buttons.matching(NSPredicate(format: "label CONTAINS %@", title)).firstMatch
        XCTAssertTrue(discardedCard.waitForExistence(timeout: 10))
        XCTAssertFalse(discardedCard.label.contains("버릴 변경"))
        XCTAssertTrue(discardedCard.label.contains("첫 줄"))
        XCTAssertTrue(discardedCard.label.contains("다음 줄도 기억하기"))
        let screenshot = XCTAttachment(screenshot: app.screenshot())
        screenshot.name = "여백 iOS 목록"
        screenshot.lifetime = .keepAlways
        add(screenshot)
    }
}

import SwiftUI
import MoaKit

@main
struct YeobackApp: App {
    var body: some Scene {
        WindowGroup { MemoHost().ignoresSafeArea() }
    }
}

struct MemoHost: UIViewControllerRepresentable {
    func makeUIViewController(context: Context) -> UIViewController {
        MainViewControllerKt.MainViewController()
    }
    func updateUIViewController(_ controller: UIViewController, context: Context) {}
}

import UIKit
import React
import React_RCTAppDelegate
import ReactAppDependencyProvider

@main
class AppDelegate: UIResponder, UIApplicationDelegate {
  var window: UIWindow?

  var reactNativeDelegate: ReactNativeDelegate?
  var reactNativeFactory: RCTReactNativeFactory?

  func application(
    _ application: UIApplication,
    didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]? = nil
  ) -> Bool {
    let delegate = ReactNativeDelegate()
    let factory = RCTReactNativeFactory(delegate: delegate)
    delegate.dependencyProvider = RCTAppDependencyProvider()

    reactNativeDelegate = delegate
    reactNativeFactory = factory

    window = UIWindow(frame: UIScreen.main.bounds)

    let env = ProcessInfo.processInfo.environment
    let solo = env["ZL_SOLO"] == "1"
    let initial: [String: Any]? = solo ? [
      "engine": env["ZL_ENGINE"] ?? "zigpool",
      "count": Int(env["ZL_COUNT"] ?? "100000") ?? 100000,
      "cell": env["ZL_CELL"] ?? "heavy",
      "legacyRecycling": env["ZL_LEGACY"] == "1",
      "audit": env["ZL_AUDIT"] == "1",
      "bindingDelayMs": Int(env["ZL_DELAY"] ?? "0") ?? 0
    ] : nil
    factory.startReactNative(
      withModuleName: solo ? "ZLSolo" : "ZerolistExample",
      in: window,
      initialProperties: initial,
      launchOptions: launchOptions
    )

    return true
  }
}

class ReactNativeDelegate: RCTDefaultReactNativeFactoryDelegate {
  override func sourceURL(for bridge: RCTBridge) -> URL? {
    self.bundleURL()
  }

  override func bundleURL() -> URL? {
#if DEBUG
    RCTBundleURLProvider.sharedSettings().jsBundleURL(forBundleRoot: "index")
#else
    Bundle.main.url(forResource: "main", withExtension: "jsbundle")
#endif
  }
}

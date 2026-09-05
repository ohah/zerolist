import UIKit
import React
import React_RCTAppDelegate
import ReactAppDependencyProvider

@main
class AppDelegate: UIResponder, UIApplicationDelegate {
  var window: UIWindow?
  private var frameProbe: FrameProbe?

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

    let measureFrames = ProcessInfo.processInfo.environment["ZL_FRAMES"] == "1"
    window = measureFrames ? ProbeWindow(frame: UIScreen.main.bounds) : UIWindow(frame: UIScreen.main.bounds)
    if measureFrames { frameProbe = FrameProbe() }

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

// 시뮬레이터 보조 지표: 화면 갱신 콜백 간격이며 GPU 마감 초과율이 아니다.
private final class FrameProbe: NSObject {
  private var link: CADisplayLink?
  override init() {
    super.init()
    link = CADisplayLink(target: self, selector: #selector(tick(_:)))
    link?.add(to: .main, forMode: .common)
  }
  @objc private func tick(_ link: CADisplayLink) {
    NSLog("ZlFrame ios timestamp=%.9f target=%.9f now=%.9f", link.timestamp, link.targetTimestamp, CACurrentMediaTime())
  }
  deinit { link?.invalidate() }
}
private final class ProbeWindow: UIWindow {
  override func sendEvent(_ event: UIEvent) {
    for touch in event.allTouches ?? [] {
      if touch.phase == .began || touch.phase == .ended {
        NSLog("ZlTouch action=%d timestamp=%.9f", touch.phase == .began ? 0 : 1, touch.timestamp)
      }
    }
    super.sendEvent(event)
  }
}

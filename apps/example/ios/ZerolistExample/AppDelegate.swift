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
    var initial: [String: Any]? = nil
    if solo {
      var options: [String: Any] = [:]
      options["jsBlockMs"] = Int(env["ZL_BLOCK_MS"] ?? "0") ?? 0
      options["preparation"] = env["ZL_PREPARATION"] ?? "baseline"
      options["preparationTrace"] = env["ZL_PREPARATION_TRACE"] == "1"
      options["engine"] = env["ZL_ENGINE"] ?? "zigpool"
      options["count"] = Int(env["ZL_COUNT"] ?? "100000") ?? 100000
      options["cell"] = env["ZL_CELL"] ?? "heavy"
      options["legacyRecycling"] = env["ZL_LEGACY"] == "1"
      options["audit"] = env["ZL_AUDIT"] == "1"
      options["bindingDelayMs"] = Int(env["ZL_DELAY"] ?? "0") ?? 0
      initial = options
    }
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
  private func scrollOffset(_ view: UIView) -> CGFloat? {
    if let scroll = view as? UIScrollView { return scroll.contentOffset.y }
    for child in view.subviews { if let y = scrollOffset(child) { return y } }
    return nil
  }
  override func sendEvent(_ event: UIEvent) {
    for touch in event.allTouches ?? [] {
      if touch.phase == .began || touch.phase == .ended {
        NSLog("ZlTouch action=%d timestamp=%.9f y=%.3f", touch.phase == .began ? 0 : 1, touch.timestamp, scrollOffset(self) ?? -1)
      }
    }
    super.sendEvent(event)
  }
}

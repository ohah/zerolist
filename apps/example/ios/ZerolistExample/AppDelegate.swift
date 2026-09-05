import UIKit
import React
import React_RCTAppDelegate
import ReactAppDependencyProvider

@main
class AppDelegate: UIResponder, UIApplicationDelegate {
  var window: UIWindow?
  private var frameProbe: FrameProbe?
  private var commonProbe: CommonListProbe?

  var reactNativeDelegate: ReactNativeDelegate?
  var reactNativeFactory: RCTReactNativeFactory?

  func application(
    _ application: UIApplication,
    didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]? = nil
  ) -> Bool {
    // RN 0.87의 os_log 정보 로그는 simctl --console에 나타나지 않을 수 있다.
    // Solo 측정 태그만 stderr에도 남겨 버전/작업량/JS 부하를 검증한다.
    if ProcessInfo.processInfo.environment["ZL_SOLO"] == "1" {
      RCTAddLogFunction { _, _, _, _, message in
        if let message, message.hasPrefix("[JS0]") || message.hasPrefix("[Zl") {
          NSLog("%@", message)
        }
      }
    }
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
      options["bufferRows"] = Int(env["ZL_BUFFER_ROWS"] ?? "-1") ?? -1
      options["commonAudit"] = env["ZL_COMMON_AUDIT"] == "1"
      options["jsBlockMs"] = Int(env["ZL_BLOCK_MS"] ?? "0") ?? 0
      options["diagnostic"] = env["ZL_DIAGNOSTIC"] ?? "normal"
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

    if env["ZL_COMMON_AUDIT"] == "1", let window { commonProbe = CommonListProbe(window: window, count: Int(env["ZL_COUNT"] ?? "100000") ?? 100000) }
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

// 측정 전용 공통 검사. 셀 루트와 실제 텍스트를 모든 엔진에서 같은 방식으로 읽는다.
private final class CommonListProbe: NSObject {
  private weak var window: UIWindow?
  private weak var scroll: UIScrollView?
  private var link: CADisplayLink?
  private let count: Int
  private var rowHeight: CGFloat = 0
  private var previous = Set<Int>()
  private var frame = 0
  init(window: UIWindow, count: Int) {
    self.window=window; self.count=count; super.init()
    link=CADisplayLink(target:self,selector:#selector(tick(_:)))
    link?.add(to:.main,forMode:.common)
  }
  deinit { link?.invalidate() }
  private func findScroll(_ v:UIView) -> UIScrollView? {
    if let s=v as? UIScrollView { return s }
    for child in v.subviews { if let s=findScroll(child) { return s } }
    return nil
  }
  private func rows(_ v:UIView, _ result:inout [UIView]) {
    if v.isHidden || v.alpha <= 0 { return }
    if v.accessibilityIdentifier?.hasPrefix("zl-row-") == true { result.append(v); return }
    for child in v.subviews { rows(child,&result) }
  }
  private func title(_ v:UIView) -> Int? {
    // 기대값 라벨이 아니라 템플릿의 실제 UILabel 문자열을 읽는다.
    if let text=(v as? UILabel)?.text, text.hasPrefix("#") {
      return Int(text.dropFirst().prefix(while: { $0.isNumber }))
    }
    if let text=v.accessibilityLabel, text.hasPrefix("#") {
      return Int(text.dropFirst().prefix(while: { $0.isNumber }))
    }
    for child in v.subviews { if let id=title(child) { return id } }
    return nil
  }
  @objc private func tick(_ link:CADisplayLink) {
    guard let window else { return }
    if scroll == nil { scroll=findScroll(window) }
    guard let scroll else { return }
    var candidates:[UIView]=[];rows(scroll,&candidates)
    if rowHeight == 0 { rowHeight=candidates.first(where: { $0.bounds.height>0 })?.bounds.height ?? 0 }
    if rowHeight<=0 { return }
    let y=scroll.contentOffset.y;let height=scroll.bounds.height
    let start=max(0,-y);let stop=min(height,CGFloat(count)*rowHeight-y)
    if stop<=start { return }
    var ready=Set<Int>();var spans:[(CGFloat,CGFloat)]=[];var wrong=0;var visible=0
    for v in candidates {
      let rect=v.convert(v.bounds,to:scroll)
      let top=rect.minY-y;let bottom=rect.maxY-y
      if bottom<=start || top>=stop { continue }
      visible+=1
      let expected=Int((rect.minY/rowHeight).rounded())
      let marker=Int((v.accessibilityIdentifier ?? "").dropFirst(7).prefix(while: { $0.isNumber }))
      if marker != expected || title(v) != expected { wrong+=1 } else { ready.insert(expected) }
      spans.append((max(start,top),min(stop,bottom)))
    }
    var end=start;var covered:CGFloat=0;var overlap:CGFloat=0
    for (a,b) in spans.sorted(by:{$0.0<$1.0}) { overlap+=max(0,min(end,b)-a);covered+=max(0,b-max(end,a));end=max(end,b) }
    let first=max(0,Int(floor(y/rowHeight)));let last=min(count,Int(ceil((y+height)/rowHeight)))
    guard last>=first else { return }
    let expected=Set(first..<last);let entered=expected.subtracting(previous);previous=expected
    frame+=1
    NSLog("ZlCommon frame=%d ns=%.0f y=%.3f viewport=%.3f rh=%.3f visible=%d attached=%d entered=%d unready=%d wrong=%d blank=%.3f overlap=%.3f",frame,link.timestamp*1e9,y,stop-start,rowHeight,visible,candidates.count,entered.count,entered.subtracting(ready).count,wrong,stop-start-covered,overlap)
  }
}

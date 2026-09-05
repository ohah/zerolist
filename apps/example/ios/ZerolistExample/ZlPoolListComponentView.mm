// React의 내용 커밋과 같은 매핑으로 배치한다. 이전 동작은 비교 옵션으로 남긴다.
#import <React/RCTViewComponentView.h>
#import <React/RCTLog.h>
#import <React/RCTComponentViewFactory.h>
#import <React/RCTMountingTransactionObserving.h>
#import <UIKit/UIKit.h>
#import <string>
#import <vector>
#import <sstream>
#import <map>
#import <deque>
#import <set>
#import <QuartzCore/QuartzCore.h>

#import <react/renderer/components/ZlExampleSpec/ComponentDescriptors.h>
#import <react/renderer/components/ZlExampleSpec/EventEmitters.h>
#import <react/renderer/components/ZlExampleSpec/Props.h>
#import <react/renderer/components/ZlExampleSpec/RCTComponentViewHelpers.h>

#import "zerolist_engine.h"

using namespace facebook::react;

@interface ZlPoolListComponentView : RCTViewComponentView <UIScrollViewDelegate, RCTMountingTransactionObserving>
@end

@implementation ZlPoolListComponentView {
  UIScrollView *_scroll;
  // 배치의 단일 진실원. _scroll 서브뷰 인덱스(인디케이터 등 포함)와
  // 무관하게 이 배열 순서로만 슬롯을 배치한다.
  NSMutableArray<UIView *> *_slots;
  std::vector<double> _offsets; // Zig 가 채운 누적 오프셋(count+1)
  NSInteger _count;
  CGFloat _rowH;
  // windowStart 불변 프레임은 frame 재배치·csv·emit 전부 스킵
  // (슬롯은 content 고정좌표라 UIScrollView 가 스크롤 처리).
  NSInteger _lastStart;
  std::vector<NSInteger> _committed;
  NSInteger _overscan;
  NSInteger _preparationMode;
  BOOL _preparationTrace;
  BOOL _bindingTrace;
  int32_t _committedVersion, _acknowledgedVersion, _inFlightVersion;
  std::map<int32_t, double> _preparationRequests;
  std::deque<double> _preparationSamples;
  double _preparationBudgetMs, _velocity, _lastMotionMs, _lastMotionY;
  int32_t _version;
  BOOL _legacyRecycling;
  BOOL _audit;
  BOOL _placementDirty;
  CADisplayLink *_auditLink;
  NSUInteger _auditFrame;
  std::set<NSInteger> _previousExpected;
}

// app-local Fabric 컴포넌트는 codegen ThirdPartyComponentsProvider 에
// 자동 등록되지 않는다(그 맵은 node_modules 라이브러리 전용, 앱은 빔).
// → 공개 API 로 명시 자기등록(런타임 준비 후 main 큐).
+ (void)load {
  if ([NSProcessInfo.processInfo.environment[@"ZL_PREPARATION_TRACE"] isEqualToString:@"1"]) {
    // 기본 OS 로그에서 생략되는 JS 진단 메시지를 감사 실행에서만 보관한다.
    RCTAddLogFunction(^(RCTLogLevel level, RCTLogSource source, NSString *file, NSNumber *line, NSString *message) {
      if (source == RCTLogSourceJavaScript && ([message hasPrefix:@"[ZlBlock]"] || [message hasPrefix:@"[JS0]"])) NSLog(@"%@", message);
    });
  }
  dispatch_async(dispatch_get_main_queue(), ^{
    [[RCTComponentViewFactory currentComponentViewFactory]
        registerComponentViewClass:self];
  });
}

+ (ComponentDescriptorProvider)componentDescriptorProvider {
  return concreteComponentDescriptorProvider<ZlPoolListComponentDescriptor>();
}

- (instancetype)initWithFrame:(CGRect)frame {
  if (self = [super initWithFrame:frame]) {
    _bindingTrace = [NSProcessInfo.processInfo.environment[@"ZL_DIAGNOSTIC"] isEqualToString:@"trace-binding"];
    _slots = [NSMutableArray new];
    _lastStart = NSIntegerMin;
    _overscan = 5;
    _committedVersion = _acknowledgedVersion = _inFlightVersion = -1;
    _preparationBudgetMs = 34;
    _scroll = [[UIScrollView alloc] initWithFrame:frame];
    _scroll.contentInsetAdjustmentBehavior = UIScrollViewContentInsetAdjustmentNever;
    _scroll.delegate = self;
    _scroll.showsVerticalScrollIndicator = YES;
    self.contentView = _scroll;
  }
  return self;
}

// Zig 로 균일 높이 offsets 빌드(zero-copy: 직접 포인터 전달).
- (void)rebuild {
  if (_count <= 0 || _rowH <= 0) return;
  std::vector<float> heights((size_t)_count, (float)_rowH);
  _offsets.assign((size_t)_count + 1, 0.0);
  zl_build_offsets(heights.data(), (size_t)_count, _offsets.data());
  _scroll.contentSize =
      CGSizeMake(self.bounds.size.width, _offsets[(size_t)_count]);
  _lastStart = NSIntegerMin;
  [self layoutSlots];
}

// 진단 실행에서만 JS Date.now와 같은 벽시계로 단계별 대기를 연결한다.
- (void)bindingLog:(NSString *)phase version:(int32_t)version {
  if (_bindingTrace)
    NSLog(@"ZlBinding phase=%@ version=%d wall=%.0f", phase, version, NSDate.date.timeIntervalSince1970 * 1000);
}

// 완료된 요청의 최근 p95로 선행 준비 거리의 시간 예산을 정한다.
- (NSInteger)preparationBehind:(NSInteger)pool {
  if (!(_preparationMode & 1) || _rowH <= 0) return _overscan;
  NSInteger spare = MAX(0, pool - (NSInteger)ceil(_scroll.bounds.size.height / _rowH));
  if (spare < 8 || fabs(_velocity) < .01) return MIN(_overscan, spare);
  double budget = _preparationBudgetMs;
  if ((_preparationMode & 8) && !_preparationRequests.empty())
    budget = MAX(budget, MIN(500, CACurrentMediaTime()*1000 - _preparationRequests.begin()->second));
  NSInteger lead = (NSInteger)ceil(fabs(_velocity) * (budget * 1.25 + 16) / _rowH) + 2;
  NSInteger ahead = MAX(5, MIN(lead, spare - 3));
  return _velocity >= 0 ? spare - ahead : ahead;
}
- (void)preparationPlaced {
  if (_committedVersion <= _acknowledgedVersion) return;
  _acknowledgedVersion = _committedVersion;
  [self bindingLog:@"placed" version:_committedVersion];
  auto found = _preparationRequests.find(_committedVersion);
  if (found != _preparationRequests.end()) {
    double now = CACurrentMediaTime() * 1000;
    // 합쳐져 사라진 이전 요청도 준비 예산에서 누락하지 않는 비교 옵션.
    double requested = (_preparationMode & 8) ? _preparationRequests.begin()->second : found->second;
    double elapsed = now - requested;
    _preparationSamples.push_back(elapsed);
    if (_preparationSamples.size() > 32) _preparationSamples.pop_front();
    std::vector<double> sorted(_preparationSamples.begin(), _preparationSamples.end());
    std::sort(sorted.begin(), sorted.end());
    _preparationBudgetMs = MAX(34, MIN(500, sorted[(size_t)ceil(sorted.size() * .95)-1]));
    if (_preparationTrace) NSLog(@"ZlPrepare phase=ready version=%d elapsed=%.3f budget=%.3f pool=%lu y=%.0f", _committedVersion, elapsed, _preparationBudgetMs, (unsigned long)_slots.count, _scroll.contentOffset.y);
  }
  _preparationRequests.erase(_preparationRequests.begin(), _preparationRequests.upper_bound(_committedVersion));
  if (_inFlightVersion <= _committedVersion) {
    _inFlightVersion = -1;
    if (_preparationMode & 2) [self layoutSlots];
  }
}

// #25: 네이티브가 binding(slot→dataIndex, ring)의 단일 권위. 슬롯 s 를
// offsets[ring(s)] 에 자기배치(child 순서 무관). windowStart 가 바뀔
// 때만 재배치 + binding csv 하달 → JS 는 그대로 적용(자체 파생 X =
// #24 desync 제거). 그 외 프레임은 즉시 반환(프레임당 JS·작업 0).
- (void)layoutSlots {
  if (_offsets.empty() || _slots.count == 0 || _count <= 0) return;
  NSInteger pool = MIN((NSInteger)_slots.count, _count); // OOB 방지
  double y = _scroll.contentOffset.y;
  double vp = _scroll.bounds.size.height;
  int32_t f = 0, l = 0;
  zl_visible_range(_offsets.data(), (size_t)_count, y, vp, &f, &l);
  NSInteger behind = [self preparationBehind:pool];
  NSInteger start = std::max<NSInteger>(0, std::min<NSInteger>(f - behind, _count - pool));
  if ((_preparationMode & 4) && _lastStart >= 0) {
    NSInteger visible = (NSInteger)ceil(vp/_rowH), spare=MAX(0,pool-visible);
    NSInteger ahead = fabs(_velocity)<.01 ? 5 : (_velocity>=0 ? spare-behind : behind);
    NSInteger needStart=MAX(0,f-(_velocity<0 ? ahead : 3));
    NSInteger needEnd=MIN(_count,f+visible+(_velocity>=0 ? ahead : 3));
    if (_lastStart<=needStart && _lastStart+pool>=needEnd) start=_lastStart;
  }
  // 슬롯은 content 고정좌표(offsets[ring])라 UIScrollView 가 스크롤
  // 처리 → windowStart 불변 프레임은 frame·csv·emit 전부 불필요.
  if (start == _lastStart) return;
  if ((_preparationMode & 2) && _inFlightVersion >= 0) return;
  _lastStart = start;
  std::string binds;
  for (NSInteger s = 0; s < pool; s++) {
    // ring(packages/zerolist/src/virtualizer.ts ringIndex 와 동일 계약)
    NSInteger idx = start + (((s - start) % pool) + pool) % pool;
    if (_legacyRecycling) _slots[(NSUInteger)s].frame =
        CGRectMake(0, _offsets[(size_t)idx], self.bounds.size.width, _rowH);
    if (s) binds += ',';
    binds += std::to_string((long)idx);
  }
  if (_eventEmitter) {
    ++_version;
    _preparationRequests[_version] = CACurrentMediaTime() * 1000;
    while (_preparationRequests.size() > 512) _preparationRequests.erase(_preparationRequests.begin());
    _inFlightVersion = _version;
    if (_preparationTrace) NSLog(@"ZlPrepare phase=request version=%d first=%d start=%ld pool=%ld velocity=%.3f", _version, f, (long)start, (long)pool, _velocity);
    [self bindingLog:@"request" version:_version];
    auto emitter = std::static_pointer_cast<const ZlPoolListEventEmitter>(_eventEmitter);
    if (_preparationMode & 16) {
      // PoC: 화면 준비 요청에 명시적 우선순위. JS 실행을 강제 중단하지 않는다.
      emitter->dispatchEvent("recycle", [binds, version = _version](facebook::jsi::Runtime &runtime) {
        auto payload = facebook::jsi::Object(runtime);
        payload.setProperty(runtime, "binds", binds);
        payload.setProperty(runtime, "version", version);
        return payload;
      }, RawEvent::Category::Discrete);
    } else emitter->onRecycle({.binds = binds, .version = _version});
  }
}

- (void)mountingTransactionDidMount:(const MountingTransaction &)transaction
               withSurfaceTelemetry:(const SurfaceTelemetry &)surfaceTelemetry {
  // 하위 텍스트까지 모두 반영한 뒤 같은 매핑으로 위치를 확정한다.
  if (!_legacyRecycling && _placementDirty) { [self placeCommitted]; _placementDirty=NO; }
  [self preparationPlaced];
}

- (void)placeCommitted {
  for (NSUInteger slot = 0; slot < _slots.count; slot++) {
    UIView *view = _slots[slot];
    NSInteger idx = slot < _committed.size() ? _committed[slot] : -1;
    view.hidden = idx < 0 || idx >= _count || _offsets.empty();
    if (!view.hidden) view.frame = CGRectMake(0, _offsets[(size_t)idx], self.bounds.size.width, _rowH);
  }
}

// 실제 텍스트와 셀 위치에서 구한 항목 번호를 비교한다.
- (NSInteger)titleIndex:(UIView *)view {
  NSString *label = view.accessibilityLabel;
  if ([label hasPrefix:@"#"]) return [[label substringFromIndex:1] integerValue];
  for (UIView *child in view.subviews) {
    NSInteger found = [self titleIndex:child];
    if (found >= 0) return found;
  }
  return -1;
}
- (void)auditFrame:(CADisplayLink *)link {
  if (!_audit || _rowH <= 0 || !self.window) return;
  CGFloat y = _scroll.contentOffset.y, height = _scroll.bounds.size.height;
  CGFloat viewportStart=MAX(0,-y), viewportEnd=MIN(height,_scroll.contentSize.height-y);
  NSInteger wrong = 0, visible = 0;
  std::set<NSInteger> readyIndices;
  std::vector<std::pair<CGFloat,CGFloat>> spans;
  for (UIView *view in _slots) {
    CGFloat top = view.frame.origin.y - y, bottom = top + view.frame.size.height;
    if (view.hidden || bottom <= viewportStart || top >= viewportEnd) continue;
    visible++;
    NSInteger expected = (NSInteger)llround(view.frame.origin.y / _rowH);
    if ([self titleIndex:view] != expected) wrong++; else readyIndices.insert(expected);
    spans.emplace_back(MAX(viewportStart,top), MIN(viewportEnd,bottom));
  }
  std::sort(spans.begin(),spans.end());
  CGFloat end=viewportStart, covered=0, overlap=0;
  for (auto span : spans) { overlap+=MAX(0,MIN(end,span.second)-span.first); covered+=MAX(0,span.second-MAX(end,span.first)); end=MAX(end,span.second); }
  NSInteger first=MAX(0,(NSInteger)floor(y/_rowH)), stop=MIN(_count,(NSInteger)ceil((y+height)/_rowH));
  std::set<NSInteger> expected;
  NSInteger entered=0, unready=0;
  for (NSInteger i=first;i<stop;i++) {
    expected.insert(i);
    if (!_previousExpected.count(i)) { entered++; if (!readyIndices.count(i)) unready++; }
  }
  _previousExpected=expected;
  NSLog(@"ZlAudit entered=%ld unready=%ld frame=%lu y=%.0f wrong=%ld visible=%ld blank=%.0f overlap=%.0f version=%d",(long)entered,(long)unready,(unsigned long)++_auditFrame,y,(long)wrong,(long)visible,MAX(0,viewportEnd-viewportStart)-covered,overlap,_version);
}
- (void)didMoveToWindow {
  [super didMoveToWindow];
  [_auditLink invalidate]; _auditLink=nil;
  if (self.window && _audit) { _auditLink=[CADisplayLink displayLinkWithTarget:self selector:@selector(auditFrame:)]; [_auditLink addToRunLoop:NSRunLoop.mainRunLoop forMode:NSRunLoopCommonModes]; }
}

- (void)scrollViewDidScroll:(UIScrollView *)scrollView {
  double now = CACurrentMediaTime() * 1000, dt = now - _lastMotionMs;
  if (dt > 0 && dt <= 100) {
    double v = (scrollView.contentOffset.y - _lastMotionY) / dt;
    _velocity = v * _velocity < 0 ? v : _velocity * .6 + v * .4;
  } else _velocity = 0;
  _lastMotionMs = now; _lastMotionY = scrollView.contentOffset.y;
  [self layoutSlots];
}

- (void)updateProps:(const Props::Shared &)props
           oldProps:(const Props::Shared &)oldProps {
  const auto &p = *std::static_pointer_cast<const ZlPoolListProps>(props);
  BOOL changed = NO;
  if (_preparationMode != p.preparationMode) _lastStart = NSIntegerMin;
  _preparationMode = p.preparationMode;
  _preparationTrace = p.preparationTrace;
  if (_committedVersion != p.committedVersion) [self bindingLog:@"native_commit" version:p.committedVersion];
  _committedVersion = p.committedVersion;
  _legacyRecycling = p.legacyRecycling;
  _overscan = MAX(0,p.overscan);
  if (_audit != p.audit) { _audit = p.audit; [self didMoveToWindow]; }
  _placementDirty=YES;
  _committed.clear();
  std::istringstream stream(p.committedBinds);
  std::string part;
  while (std::getline(stream,part,',')) { char *end=nullptr; long value=strtol(part.c_str(),&end,10); _committed.push_back(end != part.c_str() && *end == '\0' ? value : -1); }
  [self setNeedsLayout];
  if ((NSInteger)p.count != _count) {
    _count = (NSInteger)p.count;
    changed = YES;
  }
  if ((CGFloat)p.rowHeight != _rowH) {
    _rowH = (CGFloat)p.rowHeight;
    changed = YES;
  }
  [super updateProps:props oldProps:oldProps];
  if (changed) [self rebuild];
}

// Fabric 자식(JSX 슬롯)을 스크롤뷰에 마운트 — 풀.
- (void)mountChildComponentView:(UIView<RCTComponentViewProtocol> *)child
                          index:(NSInteger)index {
  [_scroll insertSubview:child atIndex:(NSUInteger)index];
  [_slots insertObject:child atIndex:(NSUInteger)index];
  _placementDirty=YES;
  _lastStart = NSIntegerMin;
  [self layoutSlots];
}

- (void)unmountChildComponentView:(UIView<RCTComponentViewProtocol> *)child
                            index:(NSInteger)index {
  [child removeFromSuperview];
  [_slots removeObjectAtIndex:(NSUInteger)index];
  _placementDirty=YES;
  _lastStart = NSIntegerMin; // 풀 크기 변경 → 다음 layoutSlots 강제
  [self layoutSlots];
}

- (void)layoutSubviews {
  [super layoutSubviews];
  _scroll.frame = self.bounds;
  if (!_offsets.empty())
    _scroll.contentSize =
        CGSizeMake(self.bounds.size.width, _offsets[(size_t)_count]);
  [self layoutSlots];
  if (!_legacyRecycling) [self placeCommitted];
}

- (void)prepareForRecycle {
  [_auditLink invalidate]; _auditLink=nil;
  _committed.clear();
  _preparationRequests.clear(); _preparationSamples.clear(); _previousExpected.clear();
  _committedVersion = _acknowledgedVersion = _inFlightVersion = -1;
  _preparationBudgetMs = 34; _velocity = _lastMotionMs = _lastMotionY = 0;
  _scroll.delegate = nil;
  [_slots removeAllObjects];
  _offsets.clear();
  _count = 0;
  _rowH = 0;
  _lastStart = NSIntegerMin;
  _scroll.contentOffset = CGPointZero; // 재사용 셀 스크롤 위치 누수 방지
  _scroll.contentSize = CGSizeZero;
  [super prepareForRecycle];
  _scroll.delegate = self;
}

@end

// ZeroList③ iOS #25: Android ZlPoolList 의 iOS Fabric 포팅. 네이티브가
// slot↔dataIndex(ring) 의 단일 권위. UIScrollView 가 스크롤/모멘텀
// (프레임당 JS 0). windowStart 가 바뀔 때만 슬롯 frame 재배치 +
// binding csv 하달(onRecycle{binds}, codegen EventEmitter) → JS 는
// 그대로 적용(자체 ring 파생 X = #24 desync 제거). 한계: 위치는 항상
// 정합하나 내용은 JS state ~1 이벤트지연 → 빠른 플링 중 잠깐 stale
// (at-rest 정합 — #24 영구겹침 해소).
#import <React/RCTViewComponentView.h>
#import <React/RCTComponentViewFactory.h>
#import <UIKit/UIKit.h>
#import <string>
#import <vector>

#import <react/renderer/components/ZlExampleSpec/ComponentDescriptors.h>
#import <react/renderer/components/ZlExampleSpec/EventEmitters.h>
#import <react/renderer/components/ZlExampleSpec/Props.h>
#import <react/renderer/components/ZlExampleSpec/RCTComponentViewHelpers.h>

#import "zerolist_engine.h"

using namespace facebook::react;

@interface ZlPoolListComponentView : RCTViewComponentView <UIScrollViewDelegate>
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
}

// app-local Fabric 컴포넌트는 codegen ThirdPartyComponentsProvider 에
// 자동 등록되지 않는다(그 맵은 node_modules 라이브러리 전용, 앱은 빔).
// → 공개 API 로 명시 자기등록(런타임 준비 후 main 큐).
+ (void)load {
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
    _slots = [NSMutableArray new];
    _lastStart = NSIntegerMin;
    _scroll = [[UIScrollView alloc] initWithFrame:frame];
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
  NSInteger start =
      std::max<NSInteger>(0, std::min<NSInteger>(f, _count - pool));
  // 슬롯은 content 고정좌표(offsets[ring])라 UIScrollView 가 스크롤
  // 처리 → windowStart 불변 프레임은 frame·csv·emit 전부 불필요.
  if (start == _lastStart) return;
  _lastStart = start;
  std::string binds;
  for (NSInteger s = 0; s < pool; s++) {
    // ring(packages/zerolist/src/virtualizer.ts ringIndex 와 동일 계약)
    NSInteger idx = start + (((s - start) % pool) + pool) % pool;
    _slots[(NSUInteger)s].frame =
        CGRectMake(0, _offsets[(size_t)idx], self.bounds.size.width, _rowH);
    if (s) binds += ',';
    binds += std::to_string((long)idx);
  }
  if (_eventEmitter) {
    std::static_pointer_cast<const ZlPoolListEventEmitter>(_eventEmitter)
        ->onRecycle({.binds = binds});
  }
}

- (void)scrollViewDidScroll:(UIScrollView *)scrollView {
  [self layoutSlots];
}

- (void)updateProps:(const Props::Shared &)props
           oldProps:(const Props::Shared &)oldProps {
  const auto &p = *std::static_pointer_cast<const ZlPoolListProps>(props);
  BOOL changed = NO;
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
  _lastStart = NSIntegerMin;
  [self layoutSlots];
}

- (void)unmountChildComponentView:(UIView<RCTComponentViewProtocol> *)child
                            index:(NSInteger)index {
  [child removeFromSuperview];
  [_slots removeObjectAtIndex:(NSUInteger)index];
  _lastStart = NSIntegerMin; // 풀 크기 변경 → 다음 layoutSlots 강제
  [self layoutSlots];
}

- (void)layoutSubviews {
  [super layoutSubviews];
  _scroll.frame = self.bounds;
  if (!_offsets.empty())
    _scroll.contentSize =
        CGSizeMake(self.bounds.size.width, _offsets[(size_t)_count]);
  _lastStart = NSIntegerMin; // bounds 변화 시 슬롯 폭 재적용 강제
  [self layoutSlots];
}

- (void)prepareForRecycle {
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

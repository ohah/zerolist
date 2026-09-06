#import <React/RCTViewComponentView.h>
#import <React/RCTComponentViewFactory.h>
#import <react/renderer/components/ZlExampleSpec/ComponentDescriptors.h>
#import <react/renderer/components/ZlExampleSpec/Props.h>
#import <react/renderer/components/ZlExampleSpec/RCTComponentViewHelpers.h>
#include <cmath>
using namespace facebook::react;

@interface ZlPaletteCanvas : UIView
@property(nonatomic) double hue;
@end
@implementation ZlPaletteCanvas {
  NSArray<UIColor *> *_colors;
  CGPathRef _dotPath;
}
- (instancetype)initWithFrame:(CGRect)frame {
  if (self=[super initWithFrame:frame]) {
    _dotPath=CGPathCreateWithRoundedRect(CGRectMake(0,0,18,18),4,4,nullptr);
    _hue=NAN;self.hue=0;
  }
  return self;
}
- (void)dealloc { CGPathRelease(_dotPath); }
- (void)setHue:(double)hue {
  if (_hue==hue) return;
  _hue=hue;
  NSMutableArray<UIColor *> *colors=[NSMutableArray arrayWithCapacity:64];
  for (int i=0;i<64;i++) {
    double h=fmod(fmod(_hue+i*5,360)+360,360)/60;
    double c=.36,x=c*(1-fabs(fmod(h,2)-1)),m=.52,r=0,g=0,b=0;
    switch ((int)h) { case 0:r=c;g=x;break;case 1:r=x;g=c;break;case 2:g=c;b=x;break;case 3:g=x;b=c;break;case 4:r=x;b=c;break;default:r=c;b=x; }
    // RN의 색상 정수와 같은 8비트 반올림을 적용한다.
    [colors addObject:[UIColor colorWithRed:round((r+m)*255)/255 green:round((g+m)*255)/255 blue:round((b+m)*255)/255 alpha:1]];
  }
  _colors=colors;[self setNeedsDisplay];
}
- (void)drawRect:(CGRect)rect {
  const int columns=std::max(1,(int)floor((self.bounds.size.width+2)/20));
  CGContextRef context=UIGraphicsGetCurrentContext();
  for (int i=0;i<64;i++) {
    CGContextSaveGState(context);
    CGContextTranslateCTM(context,(i%columns)*20,(i/columns)*20);
    CGContextSetFillColorWithColor(context,_colors[i].CGColor);
    CGContextAddPath(context,_dotPath);CGContextFillPath(context);
    CGContextRestoreGState(context);
  }
}
@end
@interface ZlTemplatePaletteComponentView : RCTViewComponentView <RCTZlTemplatePaletteViewProtocol>
@end
@implementation ZlTemplatePaletteComponentView {
  ZlPaletteCanvas *_canvas;
}
+ (void)load {
  dispatch_async(dispatch_get_main_queue(), ^{ [[RCTComponentViewFactory currentComponentViewFactory] registerComponentViewClass:self]; });
}
+ (ComponentDescriptorProvider)componentDescriptorProvider { return concreteComponentDescriptorProvider<ZlTemplatePaletteComponentDescriptor>(); }
- (instancetype)initWithFrame:(CGRect)frame {
  if (self=[super initWithFrame:frame]) {
    _props=std::make_shared<const ZlTemplatePaletteProps>();
    _canvas=[ZlPaletteCanvas new];_canvas.opaque=NO;_canvas.userInteractionEnabled=NO;
    _canvas.contentMode=UIViewContentModeRedraw;
    [self addSubview:_canvas];
  }
  return self;
}
- (void)updateProps:(Props::Shared const &)props oldProps:(Props::Shared const &)oldProps {
  const auto &p=*std::static_pointer_cast<const ZlTemplatePaletteProps>(props);
  const auto &old=*std::static_pointer_cast<const ZlTemplatePaletteProps>(_props);
  // 명령으로 설정한 현재 값을 무관한 스타일 갱신이 초기 props로 되돌리지 않는다.
  if (p.hue!=old.hue) _canvas.hue=p.hue;
  [super updateProps:props oldProps:oldProps];
}
- (void)handleCommand:(const NSString *)commandName args:(const NSArray *)args {
  RCTZlTemplatePaletteHandleCommand(self, commandName, args);
}
- (void)updateHue:(double)hue { _canvas.hue=hue; }
- (void)layoutSubviews { [super layoutSubviews];_canvas.frame=self.bounds; }
- (void)prepareForRecycle { [super prepareForRecycle];_canvas.hue=0; }
@end

#import <React/RCTViewComponentView.h>
#import <React/RCTComponentViewFactory.h>
#import <react/renderer/components/ZlExampleSpec/ComponentDescriptors.h>
#import <react/renderer/components/ZlExampleSpec/Props.h>
#import <react/renderer/components/ZlExampleSpec/RCTComponentViewHelpers.h>
using namespace facebook::react;

// UIView/UILabel 구성과 문자열 속성만 제공하는 앱 전용 실험 컴포넌트.
@interface ZlTemplateTextComponentView : RCTViewComponentView <RCTZlTemplateTextViewProtocol>
@end
@implementation ZlTemplateTextComponentView {
  UILabel *_label;
}
+ (void)load {
  dispatch_async(dispatch_get_main_queue(), ^{
    [[RCTComponentViewFactory currentComponentViewFactory] registerComponentViewClass:self];
  });
}
+ (ComponentDescriptorProvider)componentDescriptorProvider {
  return concreteComponentDescriptorProvider<ZlTemplateTextComponentDescriptor>();
}
- (instancetype)initWithFrame:(CGRect)frame {
  if (self = [super initWithFrame:frame]) {
    _props = std::make_shared<const ZlTemplateTextProps>();
    _label = [UILabel new];
    _label.lineBreakMode = NSLineBreakByTruncatingTail;
    [self addSubview:_label];
  }
  return self;
}
- (void)updateProps:(Props::Shared const &)props oldProps:(Props::Shared const &)oldProps {
  const auto &p = *std::static_pointer_cast<const ZlTemplateTextProps>(props);
  const auto &old = *std::static_pointer_cast<const ZlTemplateTextProps>(_props);
  if (p.content != old.content) _label.text = [NSString stringWithUTF8String:p.content.c_str()];
  _label.numberOfLines = p.kind == 1 ? 3 : 1;
  UIFont *base = p.kind == 0 ? [UIFont boldSystemFontOfSize:15] : [UIFont systemFontOfSize:13];
  _label.font = [[UIFontMetrics defaultMetrics] scaledFontForFont:base];
  _label.textColor = [UIColor colorWithWhite:p.kind == 0 ? 17.0/255 : 68.0/255 alpha:1];
  [super updateProps:props oldProps:oldProps];
}
- (void)handleCommand:(const NSString *)commandName args:(const NSArray *)args {
  RCTZlTemplateTextHandleCommand(self, commandName, args);
}
- (void)updateContent:(NSString *)content { _label.text=content; }
- (void)layoutSubviews {
  [super layoutSubviews];
  _label.frame = self.bounds;
}
- (void)prepareForRecycle {
  [super prepareForRecycle];
  _label.text = nil;
}
@end

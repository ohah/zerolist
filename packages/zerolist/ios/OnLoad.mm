#import <Foundation/Foundation.h>
#import "ZerolistImpl.h"
#import <ReactCommon/CxxTurboModuleUtils.h>

@interface ZerolistOnLoad : NSObject
@end

@implementation ZerolistOnLoad

using namespace facebook::react;

+ (void)load
{
  registerCxxModuleToGlobalModuleMap(
    std::string(ZerolistImpl::kModuleName),
    [](std::shared_ptr<CallInvoker> jsInvoker) {
      return std::make_shared<ZerolistImpl>(jsInvoker);
    }
  );
}

@end

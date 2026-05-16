package zerolist.example

import android.os.Bundle
import com.facebook.react.ReactActivity
import com.facebook.react.ReactActivityDelegate
import com.facebook.react.defaults.DefaultNewArchitectureEntryPoint.fabricEnabled
import com.facebook.react.defaults.DefaultReactActivityDelegate

// chrome-free 측정용 ReactActivity — "ZLSolo" RN 컴포넌트(단일 엔진만)
// 를 풀스크린으로 띄운다. engine/count/cell 은 adb am start 의 intent
// extra → getLaunchOptions → initialProps 로 전달.
// 예: am start -n PKG/.SoloActivity --es engine flatlist --ei count 20000
class SoloActivity : ReactActivity() {
  override fun getMainComponentName(): String = "ZLSolo"

  override fun createReactActivityDelegate(): ReactActivityDelegate =
    object : DefaultReactActivityDelegate(this, mainComponentName, fabricEnabled) {
      override fun getLaunchOptions(): Bundle =
        Bundle().apply {
          putString("engine", intent.getStringExtra("engine") ?: "flatlist")
          putInt("count", intent.getIntExtra("count", 20_000))
          putString("cell", intent.getStringExtra("cell") ?: "complex")
        }
    }
}

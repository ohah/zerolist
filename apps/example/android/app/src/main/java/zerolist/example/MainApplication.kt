package zerolist.example

import android.app.Application
import com.facebook.react.PackageList
import com.facebook.react.ReactApplication
import com.facebook.react.ReactHost
import com.facebook.react.ReactNativeApplicationEntryPoint.loadReactNative
import com.facebook.react.defaults.DefaultReactHost.getDefaultReactHost
import com.facebook.react.internal.featureflags.ReactNativeFeatureFlags
import com.facebook.react.internal.featureflags.ReactNativeNewArchitectureFeatureFlagsDefaults
import android.util.Log

class MainApplication : Application(), ReactApplication {
  private var hostCreated = false
  private var benchmarkRecycling: Boolean? = null

  // 진단 전용. 새 프로세스에서 ReactHost 생성 전에만 변경한다.
  // 기본 앱 및 라이브러리 동작은 변경하지 않는다.
  fun configureBenchmarkRecycling(enabled: Boolean) {
    check(!hostCreated) { "View recycling diagnostics require a fresh process" }
    check(benchmarkRecycling == null) { "View recycling configured twice" }
    val previous = ReactNativeFeatureFlags.dangerouslyForceOverride(
      object : ReactNativeNewArchitectureFeatureFlagsDefaults() {
        override fun enableViewRecycling(): Boolean = enabled
      }
    )
    check(previous?.contains("enableViewRecycling") != true) {
      "View recycling was already accessed before diagnostic configuration: $previous"
    }
    benchmarkRecycling = enabled
    check(ReactNativeFeatureFlags.enableViewRecycling() == enabled)
    Log.i("ZlRecycle", "configured=$enabled effective=${ReactNativeFeatureFlags.enableViewRecycling()} previous=$previous")
  }

  override val reactHost: ReactHost by lazy {
    hostCreated = true
    getDefaultReactHost(
      context = applicationContext,
      packageList =
        PackageList(this).packages.apply {
          add(ZlPackage()) // Fabric 네이티브 리스트(ZlNativeList) 베이스라인
        },
    )
  }

  override fun onCreate() {
    super.onCreate()
    loadReactNative(this)
  }
}

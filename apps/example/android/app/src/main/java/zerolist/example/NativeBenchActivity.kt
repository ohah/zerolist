package zerolist.example

import android.app.Activity
import android.os.Bundle

// 순수 네이티브 리스트 베이스라인 — React 0. 셀/리스트 코드는
// NativeList.kt 의 공유 빌더(buildNativeList)를 그대로 사용 →
// Fabric 임베드 뷰와 셀이 동일(공정 비교). adb am start 로 직접 실행.
// count 는 intent extra 로 받아 harness 엔진과 N 을 맞춘다(파리티).
class NativeBenchActivity : Activity() {
  override fun onCreate(savedInstanceState: Bundle?) {
    super.onCreate(savedInstanceState)
    val count = intent.getIntExtra("count", 20_000)
    setContentView(buildNativeList(this, count))
  }
}

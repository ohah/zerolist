package zerolist.example

import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity

// 순수 네이티브 리스트 베이스라인 — React 0. 셀/리스트 코드는
// NativeList.kt 공유 빌더(buildNativeList) → Fabric 임베드 뷰와
// 셀 동일. SoloActivity 가 ReactActivity(=AppCompatActivity)이므로
// 동일 window/decor 체인을 쓰도록 여기도 AppCompatActivity 로 맞춘다
// → native−nativepure 델타가 AppCompat decor 가 아닌 RN루트+Fabric
// mount 만 반영(공정, /simplify Finding 1). count 는 intent extra.
class NativeBenchActivity : AppCompatActivity() {
  override fun onCreate(savedInstanceState: Bundle?) {
    super.onCreate(savedInstanceState)
    val count = intent.getIntExtra("count", 20_000)
    setContentView(buildNativeList(this, count))
  }
}

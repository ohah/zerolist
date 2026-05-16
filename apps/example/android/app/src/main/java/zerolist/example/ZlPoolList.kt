package zerolist.example

import android.util.Log
import android.widget.FrameLayout
import com.facebook.react.uimanager.ThemedReactContext
import com.facebook.react.uimanager.ViewGroupManager
import com.facebook.react.uimanager.ViewManagerDelegate
import com.facebook.react.viewmanagers.ZlPoolListManagerDelegate
import com.facebook.react.viewmanagers.ZlPoolListManagerInterface

// ZeroList③ N1: JS 가 넘긴 풀 슬롯(JSX children, position:absolute)을
// 네이티브가 translationY 로 배치. JS 가 transform 을 안 주므로 이 값이
// Fabric commit 후에도 유지되는지 검증하는 게 N1 핵심 리스크.
// 위치 재적용을 onLayout(매 레이아웃/commit 후 호출)에서 하므로
// commit 이 transform 을 리셋해도 다음 레이아웃에 복원된다.
class ZlPoolListView(ctx: ThemedReactContext) : FrameLayout(ctx) {
  private var rowPxF = 0f
  private var logged = false

  fun setRowHeight(dp: Int) {
    rowPxF = dpF(resources.displayMetrics, dp.toFloat())
    requestLayout()
  }

  // changed 무시: Fabric commit 이 transform 을 리셋해도 매 레이아웃에
  // 무조건 복원해야 하므로(이게 N1 검증 대상).
  override fun onLayout(c: Boolean, l: Int, t: Int, r: Int, b: Int) {
    super.onLayout(c, l, t, r, b)
    // rowHeight prop 도착 전 onLayout 선행 시 전 슬롯 ty=0 겹침 방지.
    if (rowPxF <= 0f) return
    // 슬롯 i 를 i*rowHeight 픽셀에 — 네이티브가 직접(JS 0).
    for (i in 0 until childCount) getChildAt(i).translationY = i * rowPxF
    if (!logged && childCount > 0) {
      logged = true
      Log.i(
        "ZlPool",
        "children=$childCount rowPx=$rowPxF last.ty=${
          getChildAt(childCount - 1).translationY
        }",
      )
    }
  }
}

class ZlPoolListManager :
  ViewGroupManager<ZlPoolListView>(),
  ZlPoolListManagerInterface<ZlPoolListView> {

  private val delegate = ZlPoolListManagerDelegate(this)

  override fun getName() = "ZlPoolList"

  override fun createViewInstance(ctx: ThemedReactContext) =
    ZlPoolListView(ctx)

  override fun getDelegate(): ViewManagerDelegate<ZlPoolListView> = delegate

  override fun setRowHeight(view: ZlPoolListView, value: Int) {
    view.setRowHeight(value)
  }
}

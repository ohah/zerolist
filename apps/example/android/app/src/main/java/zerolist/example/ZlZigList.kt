package zerolist.example

import android.util.Log
import android.widget.FrameLayout
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.facebook.react.uimanager.SimpleViewManager
import com.facebook.react.uimanager.ThemedReactContext
import com.facebook.react.uimanager.ViewManagerDelegate
import com.facebook.react.viewmanagers.ZlZigListManagerDelegate
import com.facebook.react.viewmanagers.ZlZigListManagerInterface
import java.nio.ByteBuffer
import java.nio.ByteOrder

// ZeroList③ 아키텍처 PoC: 가시범위 결정을 네이티브 스크롤 스레드에서
// Zig(JNI, zero-copy direct ByteBuffer)로 계산 — 프레임당 JS 0. 셀은
// 기존 RecyclerView 베이스라인(buildNativeList) 재사용(공정 비교).
// 이 뷰는 데이터 경로의 실재·정합을 *검증* 하는 하네스다(RecyclerView
// 자체 가상화를 대체하지 않음). 성능 미검증(PoC).
class ZlZigListView(ctx: ThemedReactContext) : FrameLayout(ctx) {
  private var rv: RecyclerView? = null
  private var n = 0
  private var rowPx = 1
  private var builtRowPx = -1
  // Zig 가 zero-copy 로 읽는 누적 오프셋(네이티브 엔디안 direct buffer).
  private var offsets: ByteBuffer? = null
  private var checks = 0

  private val onScroll =
    object : RecyclerView.OnScrollListener() {
      override fun onScrolled(r: RecyclerView, dx: Int, dy: Int) {
        // 데이터 경로 정합을 PARITY_SAMPLES 프레임만 검증 후 자진 해제
        // (검증이 목적 — 이후 매 프레임 JNI 반복은 순수 낭비).
        if (checks >= PARITY_SAMPLES) {
          r.removeOnScrollListener(this)
          return
        }
        val off = offsets ?: return
        val lm = r.layoutManager as? LinearLayoutManager ?: return
        val cnt = n
        val scrollY = r.computeVerticalScrollOffset().toDouble()
        // 네이티브 스레드, JS 0회: Zig 가 가시범위 계산.
        val packed = ZlEngine.visibleRange(off, cnt, scrollY, r.height.toDouble())
        val zFirst = ZlEngine.firstOf(packed)
        val zLast = ZlEngine.lastOf(packed)
        val rvFirst = lm.findFirstVisibleItemPosition()
        val rvLast = lm.findLastVisibleItemPosition()
        if (rvFirst < 0) return
        checks++
        val ok = zFirst <= rvFirst && zLast >= rvLast
        Log.i(TAG, "scrollY=$scrollY zig=[$zFirst,$zLast) rv=[$rvFirst,$rvLast] ok=$ok")
      }
    }

  // 동기 rebuild — Fabric 레이아웃 패스 전에 자식(RecyclerView)을
  // 붙여야 측정/표시된다(post 로 미루면 0 크기 → 백지). 가드가
  // 중복 빌드를 막으므로 setter 2회라도 실질 빌드는 1회.
  fun setCount(value: Int) {
    n = value
    rebuild()
  }

  fun setRowHeight(value: Int) {
    rowPx = if (value > 0) value else 1
    rebuild()
  }

  private fun rebuild() {
    if (n <= 0) return
    if (offsets != null && rvCount() == n && builtRowPx == rowPx) return

    // heights(f32) → offsets(f64, n+1) : JNI→Zig zero-copy 1회.
    // buildNativeList 셀은 dp(88) 고정 → Zig 오프셋도 동일 px 로
    // (scrollY=computeVerticalScrollOffset 은 px). dp→px 변환 필수.
    val rowPxF = dpF(resources.displayMetrics, rowPx.toFloat())
    val h = ByteBuffer.allocateDirect(n * 4).order(ByteOrder.nativeOrder())
    val hf = h.asFloatBuffer()
    for (i in 0 until n) hf.put(i, rowPxF)
    val o = ByteBuffer.allocateDirect((n + 1) * 8).order(ByteOrder.nativeOrder())
    ZlEngine.buildOffsets(h, n, o)
    offsets = o
    builtRowPx = rowPx
    checks = 0

    val cur = rv
    if (cur == null) {
      val list = buildNativeList(context, n)
      list.addOnScrollListener(onScroll)
      rv = list
      addView(
        list,
        LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.MATCH_PARENT),
      )
    } else {
      cur.adapter?.notifyDataSetChanged()
    }
  }

  private fun rvCount(): Int = rv?.adapter?.itemCount ?: -1

  override fun onDetachedFromWindow() {
    rv?.removeOnScrollListener(onScroll)
    super.onDetachedFromWindow()
  }

  companion object {
    private const val TAG = "ZlZig"
    private const val PARITY_SAMPLES = 8
  }
}

class ZlZigListManager :
  SimpleViewManager<ZlZigListView>(),
  ZlZigListManagerInterface<ZlZigListView> {

  private val delegate = ZlZigListManagerDelegate(this)

  override fun getName() = "ZlZigList"

  override fun createViewInstance(ctx: ThemedReactContext) =
    ZlZigListView(ctx)

  override fun getDelegate(): ViewManagerDelegate<ZlZigListView> = delegate

  override fun setCount(view: ZlZigListView, value: Int) {
    view.setCount(value)
  }

  override fun setRowHeight(view: ZlZigListView, value: Int) {
    view.setRowHeight(value)
  }
}

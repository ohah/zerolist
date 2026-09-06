package zerolist.example

import com.zerolist.ZlPoolListView

import android.graphics.Rect
import android.util.Log
import android.view.View
import android.view.ViewGroup
import android.view.ViewTreeObserver
import android.widget.ScrollView
import android.widget.TextView
import kotlin.math.*

// 측정 전용. 모든 엔진의 실제 행 루트·텍스트·화면 좌표를 같은 방법으로 검사한다.
// OnDraw는 ZigPool의 OnPreDraw 배치가 끝난 뒤 호출된다. 실제 GPU 표시 시각은 아니다.
class CommonListProbe(private val root: View, private val count: Int, private val startupNs: Long? = null) : ViewTreeObserver.OnDrawListener {
  private var startupReported = false
  private var target: View? = null
  private var previous = setOf<Int>()
  private var rowHeight = 0.0
  private var frame = 0
  init { root.viewTreeObserver.addOnDrawListener(this) }
  fun close() { root.viewTreeObserver.removeOnDrawListener(this) }
  private fun findTarget(v: View): View? {
    if (v is ZlPoolListView || v is ScrollView) return v
    if (v is ViewGroup) for (i in 0 until v.childCount) findTarget(v.getChildAt(i))?.let { return it }
    return null
  }
  private fun rows(v: View, result: MutableList<View>) {
    if (v.visibility != View.VISIBLE || v.alpha <= 0) return
    if ((v.getTag(com.facebook.react.R.id.react_test_id) as? String)?.startsWith("zl-row-") == true) { result.add(v); return }
    if (v is ViewGroup) for (i in 0 until v.childCount) rows(v.getChildAt(i), result)
  }
  private fun title(v: View): Int? {
    if (v is TextView) Regex("^#(\\d+)").find(v.text.toString())?.let { return it.groupValues[1].toInt() }
    if (v is ViewGroup) for (i in 0 until v.childCount) title(v.getChildAt(i))?.let { return it }
    return null
  }
  override fun onDraw() {
    val scroll = target ?: findTarget(root)?.also { target = it } ?: return
    val candidates = mutableListOf<View>(); rows(scroll,candidates)
    if (rowHeight == 0.0) {
      val marker = candidates.firstOrNull()?.getTag(com.facebook.react.R.id.react_test_id) as? String ?: return
      rowHeight = (marker.substringAfter("-h").toDoubleOrNull() ?: return) * root.resources.displayMetrics.density
    }
    val y = if (scroll is ZlPoolListView) scroll.diagnosticScrollOffset().toDouble() else scroll.scrollY.toDouble()
    val origin = IntArray(2); scroll.getLocationOnScreen(origin)
    val start = max(0.0,-y); val stop = min(scroll.height.toDouble(),count*rowHeight-y)
    if (stop <= start) return
    val ready = mutableSetOf<Int>(); val spans = mutableListOf<Pair<Double,Double>>()
    var wrong = 0; var visible = 0
    for (v in candidates) {
      val location = IntArray(2); v.getLocationOnScreen(location)
      val top = (location[1]-origin[1]).toDouble(); val bottom = top+v.height
      val clipped = Rect()
      if (bottom <= start || top >= stop || !v.getGlobalVisibleRect(clipped)) continue
      visible++
      val expected = ((top+y)/rowHeight).roundToInt()
      val marker = (v.getTag(com.facebook.react.R.id.react_test_id) as String).removePrefix("zl-row-").substringBefore("-h").toIntOrNull()
      if (marker != expected || title(v) != expected) {
        wrong++
        if (frame % 120 == 0) Log.i("ZlCommonDetail", "expected=$expected marker=$marker title=${title(v)} top=$top y=$y rh=$rowHeight")
      } else ready.add(expected)
      spans.add(max(start,max(top,(clipped.top-origin[1]).toDouble())) to min(stop,min(bottom,(clipped.bottom-origin[1]).toDouble())))
    }
    var end=start; var covered=0.0; var overlap=0.0
    for ((a,b) in spans.sortedBy { it.first }) { if(b<=a) continue; overlap+=max(0.0,min(end,b)-a);covered+=max(0.0,b-max(end,a));end=max(end,b) }
    val first=max(0,floor(y/rowHeight).toInt());val last=min(count,ceil((y+scroll.height)/rowHeight).toInt())
    val expected=(first until last).toSet();val entered=expected-previous;previous=expected
    if (startupNs != null && !startupReported && visible > 0 && wrong == 0 && stop-start-covered <= 2 && overlap <= 2 && expected.all { it in ready }) {
      startupReported = true
      Log.i("ZlStartup", "phase=content_ready wall=${System.currentTimeMillis()} ms=${(System.nanoTime()-startupNs)/1e6}")
    }
    Log.i("ZlCommon", "frame=${++frame} ns=${System.nanoTime()} y=$y viewport=${stop-start} rh=$rowHeight visible=$visible attached=${candidates.size} entered=${entered.size} unready=${entered.count{it !in ready}} wrong=$wrong blank=${stop-start-covered} overlap=$overlap")
  }
}

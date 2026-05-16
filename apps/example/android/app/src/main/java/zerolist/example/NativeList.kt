package zerolist.example

import android.content.Context
import android.graphics.Color
import android.util.TypedValue
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.FrameLayout
import android.widget.LinearLayout
import android.widget.TextView
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.facebook.react.bridge.ReactApplicationContext
import com.facebook.react.bridge.ReactContext
import com.facebook.react.uimanager.SimpleViewManager
import com.facebook.react.uimanager.ThemedReactContext
import com.facebook.react.uimanager.ViewManagerDelegate
import com.facebook.react.viewmanagers.ZlNativeListManagerDelegate
import com.facebook.react.viewmanagers.ZlNativeListManagerInterface

// 순수 Native 액티비티와 Fabric 임베드 뷰가 **동일 셀 코드**를 쓰게
// 공유한다 — 두 베이스라인의 차이가 오로지 "Fabric host 래핑" 뿐이
// 되도록(공정 비교). harness 의 complex/fixed 셀 근사(88dp 고정).

private val WORDS =
  "lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut labore"
    .split(" ")

private fun dp(ctx: Context, v: Int): Int =
  TypedValue.applyDimension(
    TypedValue.COMPLEX_UNIT_DIP, v.toFloat(), ctx.resources.displayMetrics
  ).toInt()

private fun gen(seed: Int, n: Int): String {
  val sb = StringBuilder()
  for (i in 0 until n) sb.append(WORDS[(seed + i * 7) % WORDS.size]).append(' ')
  return sb.toString().trim()
}

private class Cell(val root: LinearLayout) : RecyclerView.ViewHolder(root) {
  val img: View = (root.getChildAt(0) as LinearLayout).getChildAt(0)
  val title: TextView
  val body: TextView

  init {
    val col = (root.getChildAt(0) as LinearLayout).getChildAt(1) as LinearLayout
    title = col.getChildAt(0) as TextView
    body = col.getChildAt(1) as TextView
  }
}

private class CellAdapter(val ctx: Context, var count: Int) :
  RecyclerView.Adapter<Cell>() {

  override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): Cell {
    val root = LinearLayout(ctx)
    root.orientation = LinearLayout.VERTICAL
    root.setPadding(dp(ctx, 14), dp(ctx, 10), dp(ctx, 14), dp(ctx, 10))
    root.layoutParams =
      RecyclerView.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(ctx, 88))

    val row = LinearLayout(ctx)
    row.orientation = LinearLayout.HORIZONTAL
    row.gravity = Gravity.CENTER_VERTICAL
    val thumb = View(ctx)
    thumb.layoutParams = LinearLayout.LayoutParams(dp(ctx, 56), dp(ctx, 56))
    row.addView(thumb)
    val col = LinearLayout(ctx)
    col.orientation = LinearLayout.VERTICAL
    val colLp =
      LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f)
    colLp.leftMargin = dp(ctx, 12)
    col.layoutParams = colLp
    val title = TextView(ctx)
    title.textSize = 15f
    title.setTextColor(Color.parseColor("#111111"))
    title.maxLines = 1
    val body = TextView(ctx)
    body.textSize = 13f
    body.setTextColor(Color.parseColor("#444444"))
    col.addView(title)
    col.addView(body)
    row.addView(col)
    root.addView(row)

    val tags = LinearLayout(ctx)
    tags.orientation = LinearLayout.HORIZONTAL
    val tagsLp =
      LinearLayout.LayoutParams(
        ViewGroup.LayoutParams.MATCH_PARENT,
        ViewGroup.LayoutParams.WRAP_CONTENT,
      )
    tagsLp.topMargin = dp(ctx, 8)
    tags.layoutParams = tagsLp
    for (t in 0 until 3) {
      val tag = TextView(ctx)
      tag.text = "tag$t"
      tag.textSize = 11f
      tag.setPadding(dp(ctx, 8), dp(ctx, 3), dp(ctx, 8), dp(ctx, 3))
      val lp =
        LinearLayout.LayoutParams(
          ViewGroup.LayoutParams.WRAP_CONTENT,
          ViewGroup.LayoutParams.WRAP_CONTENT,
        )
      lp.rightMargin = dp(ctx, 6)
      tag.layoutParams = lp
      tags.addView(tag)
    }
    val btn = TextView(ctx)
    btn.text = "open"
    btn.textSize = 12f
    btn.setTextColor(Color.WHITE)
    btn.setBackgroundColor(Color.parseColor("#222222"))
    btn.setPadding(dp(ctx, 12), dp(ctx, 5), dp(ctx, 12), dp(ctx, 5))
    tags.addView(btn)
    root.addView(tags)

    return Cell(root)
  }

  override fun getItemCount() = count

  override fun onBindViewHolder(h: Cell, i: Int) {
    h.title.text = "#$i ${gen(i, 3)}"
    h.body.text = gen(i + 1, 3 + (i * 37) % 18)
    val hue = ((i * 47) % 360).toFloat()
    h.root.setBackgroundColor(Color.HSVToColor(floatArrayOf(hue, 0.18f, 0.96f)))
    h.img.setBackgroundColor(Color.HSVToColor(floatArrayOf(hue, 0.5f, 0.8f)))
  }
}

/** 공유 빌더: 순수 Native 액티비티·Fabric 뷰 둘 다 이걸 쓴다. */
fun buildNativeList(ctx: Context, count: Int): RecyclerView {
  val rv = RecyclerView(ctx)
  rv.layoutManager = LinearLayoutManager(ctx)
  rv.setHasFixedSize(true)
  rv.adapter = CellAdapter(ctx, count)
  return rv
}

/** RN 내 Fabric 호스트 뷰 — 내부는 순수 Native 와 동일한 RecyclerView.
 * FrameLayout 1겹은 Fabric 호스트의 불가피한 비용으로 의도적으로
 * 포함(측정 대상이므로 제거 금지). 단 harness chrome+RN런타임 오염은
 * 별도 — chrome-free 루트(태스크 #18) 전엔 깨끗한 분리 아님. */
class ZlNativeListView(ctx: Context) : FrameLayout(ctx) {
  private var rv: RecyclerView? = null

  fun setCount(n: Int) {
    // 멱등: 동일 count 재호출(부모 리렌더) 시 전체 무효화 스파이크 방지.
    (rv?.adapter as? CellAdapter)?.let { if (it.count == n) return }
    if (rv == null) {
      rv = buildNativeList(context, n)
      addView(
        rv,
        LayoutParams(
          LayoutParams.MATCH_PARENT,
          LayoutParams.MATCH_PARENT,
        ),
      )
    } else {
      (rv!!.adapter as CellAdapter).let {
        it.count = n
        it.notifyDataSetChanged()
      }
    }
  }
}

class ZlNativeListManager :
  SimpleViewManager<ZlNativeListView>(),
  ZlNativeListManagerInterface<ZlNativeListView> {

  private val delegate = ZlNativeListManagerDelegate(this)

  override fun getName() = "ZlNativeList"

  override fun createViewInstance(ctx: ThemedReactContext) =
    ZlNativeListView(ctx)

  override fun getDelegate(): ViewManagerDelegate<ZlNativeListView> = delegate

  override fun setCount(view: ZlNativeListView, value: Int) {
    view.setCount(value)
  }
}

class ZlPackage : com.facebook.react.ReactPackage {
  override fun createNativeModules(ctx: ReactApplicationContext) =
    emptyList<com.facebook.react.bridge.NativeModule>()

  override fun createViewManagers(ctx: ReactApplicationContext) =
    listOf<com.facebook.react.uimanager.ViewManager<*, *>>(
      ZlNativeListManager(),
      ZlZigListManager(),
    )
}

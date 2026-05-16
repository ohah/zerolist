package zerolist.example

import android.app.Activity
import android.graphics.Color
import android.os.Bundle
import android.util.TypedValue
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.LinearLayout
import android.widget.TextView
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView

// 순수 네이티브 리스트 베이스라인 — React 0. RecyclerView 가 셀을
// 네이티브로 재활용한다. RN harness 의 'complex'(fixed) 셀과 유사
// 구성(이미지 자리 + 제목 + 본문 + 태그 3 + 버튼), 행 높이 88dp 고정.
// 측정: 동일 Maestro 플링 + adb gfxinfo (앱 밖 OS-truth).
class NativeBenchActivity : Activity() {

  private val count = 20_000
  private val words =
    "lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut labore"
      .split(" ")

  private fun dp(v: Int): Int =
    TypedValue.applyDimension(
      TypedValue.COMPLEX_UNIT_DIP, v.toFloat(), resources.displayMetrics
    ).toInt()

  private fun text(seed: Int, n: Int): String {
    val sb = StringBuilder()
    for (i in 0 until n) sb.append(words[(seed + i * 7) % words.size]).append(' ')
    return sb.toString().trim()
  }

  override fun onCreate(savedInstanceState: Bundle?) {
    super.onCreate(savedInstanceState)
    val rv = RecyclerView(this)
    rv.layoutManager = LinearLayoutManager(this)
    rv.setHasFixedSize(true)
    rv.adapter = Adapter()
    setContentView(rv)
  }

  private inner class VH(val root: LinearLayout) : RecyclerView.ViewHolder(root) {
    val img = root.getChildAt(0).let { (it as LinearLayout).getChildAt(0) }
    val title: TextView
    val body: TextView

    init {
      val col = (root.getChildAt(0) as LinearLayout).getChildAt(1) as LinearLayout
      title = col.getChildAt(0) as TextView
      body = col.getChildAt(1) as TextView
    }
  }

  private inner class Adapter : RecyclerView.Adapter<VH>() {
    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): VH {
      val root = LinearLayout(this@NativeBenchActivity)
      root.orientation = LinearLayout.VERTICAL
      root.setPadding(dp(14), dp(10), dp(14), dp(10))
      root.layoutParams =
        RecyclerView.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(88))

      val row = LinearLayout(this@NativeBenchActivity)
      row.orientation = LinearLayout.HORIZONTAL
      row.gravity = Gravity.CENTER_VERTICAL
      val thumb = View(this@NativeBenchActivity)
      thumb.layoutParams = LinearLayout.LayoutParams(dp(56), dp(56))
      row.addView(thumb)
      val col = LinearLayout(this@NativeBenchActivity)
      col.orientation = LinearLayout.VERTICAL
      val colLp =
        LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f)
      colLp.leftMargin = dp(12)
      col.layoutParams = colLp
      val title = TextView(this@NativeBenchActivity)
      title.textSize = 15f
      title.setTextColor(Color.parseColor("#111111"))
      title.maxLines = 1
      val body = TextView(this@NativeBenchActivity)
      body.textSize = 13f
      body.setTextColor(Color.parseColor("#444444"))
      col.addView(title)
      col.addView(body)
      row.addView(col)
      root.addView(row)

      val tags = LinearLayout(this@NativeBenchActivity)
      tags.orientation = LinearLayout.HORIZONTAL
      val tagsLp =
        LinearLayout.LayoutParams(
          ViewGroup.LayoutParams.MATCH_PARENT,
          ViewGroup.LayoutParams.WRAP_CONTENT,
        )
      tagsLp.topMargin = dp(8)
      tags.layoutParams = tagsLp
      for (t in 0 until 3) {
        val tag = TextView(this@NativeBenchActivity)
        tag.text = "tag$t"
        tag.textSize = 11f
        tag.setPadding(dp(8), dp(3), dp(8), dp(3))
        val lp =
          LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.WRAP_CONTENT,
            ViewGroup.LayoutParams.WRAP_CONTENT,
          )
        lp.rightMargin = dp(6)
        tag.layoutParams = lp
        tags.addView(tag)
      }
      val btn = TextView(this@NativeBenchActivity)
      btn.text = "open"
      btn.textSize = 12f
      btn.setTextColor(Color.WHITE)
      btn.setBackgroundColor(Color.parseColor("#222222"))
      btn.setPadding(dp(12), dp(5), dp(12), dp(5))
      tags.addView(btn)
      root.addView(tags)

      return VH(root)
    }

    override fun getItemCount() = count

    override fun onBindViewHolder(h: VH, i: Int) {
      h.title.text = "#$i ${text(i, 3)}"
      h.body.text = text(i + 1, 3 + (i * 37) % 18)
      val hue = ((i * 47) % 360).toFloat()
      h.root.setBackgroundColor(Color.HSVToColor(floatArrayOf(hue, 0.18f, 0.96f)))
      h.img.setBackgroundColor(Color.HSVToColor(floatArrayOf(hue, 0.5f, 0.8f)))
    }
  }
}

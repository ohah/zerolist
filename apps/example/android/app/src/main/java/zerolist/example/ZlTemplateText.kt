package zerolist.example

import android.graphics.Color
import android.graphics.Typeface
import android.text.TextUtils
import android.view.Gravity
import android.widget.TextView
import com.facebook.react.uimanager.SimpleViewManager
import com.facebook.react.uimanager.ThemedReactContext
import com.facebook.react.uimanager.ViewManagerDelegate
import com.facebook.react.viewmanagers.ZlTemplateTextManagerDelegate
import com.facebook.react.viewmanagers.ZlTemplateTextManagerInterface

// TextInput의 편집/상태 동기화 없이 실제 TextView 문자열만 갱신한다.
class ZlTemplateTextManager : SimpleViewManager<TextView>(), ZlTemplateTextManagerInterface<TextView> {
  private val delegate = ZlTemplateTextManagerDelegate(this)
  override fun getName() = "ZlTemplateText"
  override fun getDelegate(): ViewManagerDelegate<TextView> = delegate
  override fun createViewInstance(ctx: ThemedReactContext) = TextView(ctx).apply {
    setPadding(0, 0, 0, 0)
    includeFontPadding = false
    gravity = Gravity.TOP
    ellipsize = TextUtils.TruncateAt.END
  }
  override fun setContent(view: TextView, value: String?) { view.text = value.orEmpty() }
  override fun setKind(view: TextView, value: Int) {
    view.textSize = if (value == 0) 15f else 13f
    view.setTypeface(null, if (value == 0) Typeface.BOLD else Typeface.NORMAL)
    view.setTextColor(Color.parseColor(if (value == 0) "#111111" else "#444444"))
    view.maxLines = if (value == 1) 3 else 1
    val target = android.util.TypedValue.applyDimension(
      android.util.TypedValue.COMPLEX_UNIT_SP, if (value == 0) 20f else 18f, view.resources.displayMetrics)
    val metrics = view.paint.fontMetricsInt
    view.setLineSpacing(target - (metrics.descent - metrics.ascent), 1f)
  }
}

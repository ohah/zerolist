package zerolist.example

import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.view.View
import com.facebook.react.bridge.ReadableArray
import com.facebook.react.uimanager.SimpleViewManager
import com.facebook.react.uimanager.ThemedReactContext
import com.facebook.react.uimanager.ViewManagerDelegate
import com.facebook.react.viewmanagers.ZlTemplatePaletteManagerDelegate
import com.facebook.react.viewmanagers.ZlTemplatePaletteManagerInterface
import kotlin.math.*

// 장식용 64개 칸을 한 뷰에 그린다. 데이터/텍스트/행 수는 바꾸지 않는다.
class ZlTemplatePaletteView(ctx: ThemedReactContext) : View(ctx) {
  private val paint = Paint(Paint.ANTI_ALIAS_FLAG)
  private val colors = IntArray(64) { color(it*5.0) }
  var hue: Double = 0.0
    set(value) { if (field != value) { field=value; for (i in colors.indices) colors[i]=color(value+i*5); invalidate() } }
  private fun color(hue: Double): Int {
    val h=((hue % 360 + 360) % 360)/60
    val c=.36;val x=c*(1-abs(h%2-1));val m=.52
    val rgb=when(h.toInt()) { 0->doubleArrayOf(c,x,0.0);1->doubleArrayOf(x,c,0.0);2->doubleArrayOf(0.0,c,x);3->doubleArrayOf(0.0,x,c);4->doubleArrayOf(x,0.0,c);else->doubleArrayOf(c,0.0,x) }
    return Color.rgb(((rgb[0]+m)*255).roundToInt(),((rgb[1]+m)*255).roundToInt(),((rgb[2]+m)*255).roundToInt())
  }
  override fun onDraw(canvas: Canvas) {
    super.onDraw(canvas)
    val density=resources.displayMetrics.density
    val columns=max(1,floor((width/density+2)/20).toInt())
    for (i in 0 until 64) {
      val x=(i%columns)*20*density;val y=(i/columns)*20*density
      paint.color=colors[i]
      canvas.drawRoundRect(x,y,x+18*density,y+18*density,4*density,4*density,paint)
    }
  }
}
class ZlTemplatePaletteManager : SimpleViewManager<ZlTemplatePaletteView>(), ZlTemplatePaletteManagerInterface<ZlTemplatePaletteView> {
  private val delegate = ZlTemplatePaletteManagerDelegate(this)
  override fun getName() = "ZlTemplatePalette"
  override fun getDelegate(): ViewManagerDelegate<ZlTemplatePaletteView> = delegate
  override fun createViewInstance(ctx: ThemedReactContext) = ZlTemplatePaletteView(ctx)
  override fun setHue(view: ZlTemplatePaletteView, value: Double) { view.hue=value }
  override fun updateHue(view: ZlTemplatePaletteView, hue: Double) { view.hue=hue }
  override fun receiveCommand(view: ZlTemplatePaletteView, commandId: String, args: ReadableArray?) {
    delegate.receiveCommand(view, commandId, args)
  }
}

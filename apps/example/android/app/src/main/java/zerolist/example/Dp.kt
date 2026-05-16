package zerolist.example

import android.util.DisplayMetrics
import android.util.TypedValue

// dp→px 단일 소스(NativeList/ZlZigList/ZlPoolList 공유).
internal fun dpF(metrics: DisplayMetrics, v: Float): Float =
  TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_DIP, v, metrics)

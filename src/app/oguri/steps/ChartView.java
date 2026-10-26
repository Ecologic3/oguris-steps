package app.oguri.steps;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.DashPathEffect;
import android.graphics.Paint;
import android.graphics.Typeface;
import android.view.MotionEvent;
import android.view.View;

/** Bar chart for step history, final 1.2 design (approved from
 * renders): sparse real-date axis labels that never collide, value
 * labels only where they fit, a dashed average line in the units of
 * the view, the best bar bold in amber (slightly wider, bold amber
 * label), today in bright green, and tap-to-inspect: tapping a bar
 * selects it (bright green) and the activity shows its exact readout
 * in a pill above the chart. */
public class ChartView extends View {
    public interface BarTapListener {
        void onBarTapped(int index);
    }

    private int[] values = new int[0];
    private String[] labels = new String[0];
    private String[] valueLabels = new String[0];
    private int highlight = -1;
    private int best = -1;
    private int selected = -1;
    private float avgValue = -1f;
    private String avgLabel = null;
    private BarTapListener listener;

    private final Paint barPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint todayPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint bestPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint valuePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint bestValuePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint labelPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint basePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint avgPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint avgTextPaint = new Paint(Paint.ANTI_ALIAS_FLAG);

    public ChartView(Context ctx) {
        super(ctx);
        barPaint.setColor(Color.rgb(0x2E, 0x7D, 0x5F));
        todayPaint.setColor(Color.rgb(0x3D, 0xDC, 0x97));
        bestPaint.setColor(Color.rgb(0xF0, 0xB4, 0x54));
        valuePaint.setColor(Color.WHITE);
        valuePaint.setTextAlign(Paint.Align.CENTER);
        bestValuePaint.setColor(Color.rgb(0xF0, 0xB4, 0x54));
        bestValuePaint.setTextAlign(Paint.Align.CENTER);
        bestValuePaint.setTypeface(Typeface.DEFAULT_BOLD);
        labelPaint.setColor(Color.rgb(0x94, 0xA3, 0xB8));
        basePaint.setColor(Color.rgb(0x33, 0x3D, 0x52));
        basePaint.setStrokeWidth(2f);
        avgPaint.setColor(Color.rgb(0x94, 0xA3, 0xB8));
        avgPaint.setStrokeWidth(2f);
        avgTextPaint.setColor(Color.rgb(0x94, 0xA3, 0xB8));
    }

    public void setBarTapListener(BarTapListener l) {
        listener = l;
    }

    public void setData(int[] vals, String[] labs, String[] valueLabs,
                        int highlightIndex, int bestIndex, int selectedIndex,
                        float avg, String avgLab) {
        values = vals == null ? new int[0] : vals;
        labels = labs == null ? new String[0] : labs;
        valueLabels = valueLabs == null ? new String[0] : valueLabs;
        highlight = highlightIndex;
        best = bestIndex;
        selected = selectedIndex;
        avgValue = avg;
        avgLabel = avgLab;
        invalidate();
    }

    @Override
    public boolean onTouchEvent(MotionEvent e) {
        if (e.getAction() == MotionEvent.ACTION_UP && listener != null
                && values.length > 0) {
            float slot = (float) getWidth() / values.length;
            int idx = (int) (e.getX() / slot);
            if (idx >= 0 && idx < values.length) {
                listener.onBarTapped(idx);
                performClick();
                return true;
            }
        }
        return super.onTouchEvent(e);
    }

    @Override
    public boolean performClick() {
        super.performClick();
        return true;
    }

    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        if (values.length == 0) return;
        float density = getResources().getDisplayMetrics().density;
        float w = getWidth();
        float h = getHeight();
        float labelH = 18f * density;
        float chartTop = 17f * density;
        float chartBottom = h - labelH;
        float chartH = chartBottom - chartTop;
        if (chartH <= 0) return;

        int max = 1;
        for (int v : values) if (v > max) max = v;
        float scaleMax = Math.max(max, avgValue) * 1.12f;

        float slot = w / values.length;
        float barW = Math.max(2f * density, Math.min(slot * 0.6f, 26f * density));
        valuePaint.setTextSize(10.5f * density);
        bestValuePaint.setTextSize(11f * density);
        labelPaint.setTextSize(10.5f * density);
        avgTextPaint.setTextSize(10f * density);

        // Dashed average line, behind the bars, with its label at the
        // end that has clearance (fewer tall bars near the line).
        if (avgValue > 0 && avgLabel != null) {
            float ay = chartBottom - chartH * (avgValue / scaleMax);
            avgPaint.setPathEffect(new DashPathEffect(
                    new float[]{6f * density, 4f * density}, 0));
            canvas.drawLine(0, ay, w, ay, avgPaint);
            avgPaint.setPathEffect(null);
            float tw = avgTextPaint.measureText(avgLabel);
            boolean leftClear = sideClear(0, ay, chartTop, chartH, scaleMax);
            boolean rightClear = sideClear(1, ay, chartTop, chartH, scaleMax);
            float tx;
            if (leftClear) {
                avgTextPaint.setTextAlign(Paint.Align.LEFT);
                tx = 2f * density;
            } else if (rightClear) {
                avgTextPaint.setTextAlign(Paint.Align.RIGHT);
                tx = w - 2f * density;
            } else {
                avgTextPaint.setTextAlign(Paint.Align.LEFT);
                tx = 2f * density;
            }
            canvas.drawText(avgLabel, tx, ay - 4f * density, avgTextPaint);
        }

        canvas.drawLine(0, chartBottom, w, chartBottom, basePaint);

        for (int i = 0; i < values.length; i++) {
            float cx = slot * i + slot / 2f;
            float bh = chartH * (values[i] / scaleMax);
            float thisBarW = i == best ? barW * 1.2f : barW;
            float left = cx - thisBarW / 2f;
            float top = chartBottom - bh;
            Paint p = barPaint;
            if (i == best) p = bestPaint;
            else if (i == selected || i == highlight) p = todayPaint;
            if (values[i] > 0) {
                float r = Math.min(3f * density, thisBarW / 2f);
                canvas.drawRoundRect(left, top, left + thisBarW, chartBottom, r, r, p);
                canvas.drawRect(left, chartBottom - r, left + thisBarW, chartBottom, p);
            }
            if (i < valueLabels.length && valueLabels[i] != null && values[i] > 0) {
                Paint vp = i == best ? bestValuePaint : valuePaint;
                canvas.drawText(valueLabels[i], cx, top - 3f * density, vp);
            }
            if (i < labels.length && labels[i] != null && labels[i].length() > 0) {
                // Centre on the slot but clamp inside the view so edge
                // labels never clip or collide with a neighbour's slot.
                String s = labels[i];
                float tw = labelPaint.measureText(s);
                float tx = Math.max(0f, Math.min(cx - tw / 2f, w - tw));
                labelPaint.setTextAlign(Paint.Align.LEFT);
                canvas.drawText(s, tx, h - 4f * density, labelPaint);
            }
        }
        labelPaint.setTextAlign(Paint.Align.CENTER);
    }

    /** True when the bars near one end of the chart stay below the
     * average line, leaving room for its label. side 0 = left. */
    private boolean sideClear(int side, float ay, float chartTop,
                              float chartH, float scaleMax) {
        int n = values.length;
        int zone = Math.max(1, n / 5);
        for (int k = 0; k < zone; k++) {
            int i = side == 0 ? k : n - 1 - k;
            float top = (chartTop + chartH) - chartH * (values[i] / scaleMax);
            if (top < ay - 4f) return false;
        }
        return true;
    }
}

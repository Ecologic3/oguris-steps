package app.oguri.steps;

import android.app.PendingIntent;
import android.appwidget.AppWidgetManager;
import android.appwidget.AppWidgetProvider;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.util.TypedValue;
import android.widget.RemoteViews;

/** 1x1 transparent widget, matched to the previous pedometer widget:
 * just the step count in large white type with "steps" under it,
 * no background, no ring, no box. A soft shadow keeps it readable
 * on any wallpaper. Tap opens the app. */
public class StepsWidget extends AppWidgetProvider {

    @Override
    public void onUpdate(Context ctx, AppWidgetManager mgr, int[] ids) {
        for (int i = 0; i < ids.length; i++) {
            mgr.updateAppWidget(ids[i], buildViews(ctx));
        }
    }

    static RemoteViews buildViews(Context ctx) {
        StepStore store = new StepStore(ctx);
        RemoteViews views = new RemoteViews(ctx.getPackageName(), R.layout.widget_steps);
        String count = String.valueOf(store.todaySteps());
        views.setTextViewText(R.id.widget_steps, count);
        // The count never wraps (maxLines=1 in the layout); instead it
        // shrinks as it gains digits so 5+ digit days still fit the cell.
        int digits = count.length();
        float sp = digits <= 4 ? 30f : digits == 5 ? 24f : digits == 6 ? 20f : 17f;
        views.setTextViewTextSize(R.id.widget_steps, TypedValue.COMPLEX_UNIT_SP, sp);
        Intent open = new Intent(ctx, MainActivity.class);
        open.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
        PendingIntent pi = PendingIntent.getActivity(ctx, 0, open,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        views.setOnClickPendingIntent(R.id.widget_root, pi);
        return views;
    }

    public static void updateAll(Context ctx) {
        AppWidgetManager mgr = AppWidgetManager.getInstance(ctx);
        ComponentName name = new ComponentName(ctx, StepsWidget.class);
        int[] ids = mgr.getAppWidgetIds(name);
        for (int i = 0; i < ids.length; i++) {
            mgr.updateAppWidget(ids[i], buildViews(ctx));
        }
    }
}

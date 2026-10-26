package app.oguri.steps;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.os.Build;
import android.os.IBinder;

/** Foreground service listening to the hardware step counter.
 * The counter is a low-power sensor and cumulative since boot, so
 * counting survives the service being restarted: deltas are computed
 * against the last stored raw value, and a lower raw value means a
 * reboot happened (see StepStore). */
public class StepService extends Service implements SensorEventListener {
    private static final String CHANNEL = "steps";
    private static final int NOTIF_ID = 1;

    private SensorManager sensors;
    private Sensor counter;
    private long lastPushMs = 0;
    private int lastPushedSteps = -1;

    public static void start(Context ctx) {
        Intent i = new Intent(ctx, StepService.class);
        if (Build.VERSION.SDK_INT >= 26) ctx.startForegroundService(i);
        else ctx.startService(i);
    }

    @Override
    public void onCreate() {
        super.onCreate();
        createChannel();
        startForeground(NOTIF_ID, buildNotification(new StepStore(this).todaySteps()));
        sensors = (SensorManager) getSystemService(SENSOR_SERVICE);
        if (sensors != null) {
            counter = sensors.getDefaultSensor(Sensor.TYPE_STEP_COUNTER);
            registerQuietly();
        }
    }

    private void registerQuietly() {
        if (sensors == null || counter == null) return;
        try {
            sensors.registerListener(this, counter, SensorManager.SENSOR_DELAY_NORMAL);
        } catch (SecurityException ignored) {
            // ACTIVITY_RECOGNITION not granted yet; onStartCommand retries
            // after the user grants it from the app.
        }
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        // Re-register in case the system dropped the listener.
        if (sensors != null && counter != null) {
            sensors.unregisterListener(this);
            registerQuietly();
        }
        return START_STICKY;
    }

    @Override
    public void onDestroy() {
        if (sensors != null) sensors.unregisterListener(this);
        super.onDestroy();
    }

    @Override
    public IBinder onBind(Intent intent) { return null; }

    @Override
    public void onSensorChanged(SensorEvent event) {
        if (event.sensor.getType() != Sensor.TYPE_STEP_COUNTER) return;
        StepStore store = new StepStore(this);
        int today = store.onSensorValue(event.values[0]);
        long now = System.currentTimeMillis();
        // Throttle notification + widget pushes: at most every 5 seconds,
        // or immediately when the count actually changed since last push
        // and at least 1 second has passed.
        if (today != lastPushedSteps && now - lastPushMs >= 1000 || now - lastPushMs >= 5000) {
            lastPushMs = now;
            lastPushedSteps = today;
            NotificationManager nm = (NotificationManager) getSystemService(NOTIFICATION_SERVICE);
            if (nm != null) nm.notify(NOTIF_ID, buildNotification(today));
            StepsWidget.updateAll(this);
        }
    }

    @Override
    public void onAccuracyChanged(Sensor sensor, int accuracy) { }

    private void createChannel() {
        if (Build.VERSION.SDK_INT >= 26) {
            // MIN importance plus no POST_NOTIFICATIONS permission
            // anywhere: this notification exists only because Android
            // requires one for a foreground service, and it is kept as
            // invisible as the system allows.
            NotificationChannel ch = new NotificationChannel(CHANNEL, "Step counting",
                    NotificationManager.IMPORTANCE_MIN);
            ch.setDescription("Shows today's step count while counting is on");
            ch.setShowBadge(false);
            NotificationManager nm = (NotificationManager) getSystemService(NOTIFICATION_SERVICE);
            if (nm != null) nm.createNotificationChannel(ch);
        }
    }

    private Notification buildNotification(int today) {
        Intent open = new Intent(this, MainActivity.class);
        open.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
        PendingIntent pi = PendingIntent.getActivity(this, 0, open,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        StepStore store = new StepStore(this);
        String text = store.paused() ? "Counting paused"
                : String.format(java.util.Locale.US, "%,d steps today · %.2f km",
                        today, StepStore.distanceKm(today));
        Notification.Builder b = Build.VERSION.SDK_INT >= 26
                ? new Notification.Builder(this, CHANNEL)
                : new Notification.Builder(this);
        b.setSmallIcon(R.mipmap.ic_launcher)
         .setContentTitle("Oguri's Steps")
         .setContentText(text)
         .setContentIntent(pi)
         .setOngoing(true)
         .setPriority(Notification.PRIORITY_MIN)
         .setVisibility(Notification.VISIBILITY_SECRET)
         .setOnlyAlertOnce(true);
        return b.build();
    }
}

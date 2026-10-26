package app.oguri.steps;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

public class BootReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context ctx, Intent intent) {
        // The hardware counter resets on reboot; StepStore treats the
        // next reading as steps since boot, so just restart counting.
        StepService.start(ctx);
    }
}

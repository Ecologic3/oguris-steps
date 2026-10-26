package app.oguri.steps;

import android.content.Context;
import android.content.SharedPreferences;

import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.Collections;
import java.util.Comparator;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.TreeMap;

/** Persistent step history.
 *
 * History is kept in SharedPreferences as one string:
 *   "2026-10-26=8123;2026-10-25=4021;..."
 * That is plenty for years of daily totals and survives app updates.
 *
 * Counting state:
 *   last_raw   - last value of the hardware step counter (cumulative since boot)
 *   last_day   - day key that last_raw belongs to (for midnight rollover)
 *   paused     - user paused counting
 * No goals anywhere by design (26 Oct 2026): tracking only.
 */
public class StepStore {
    private static final String PREFS = "steps";
    private static final String KEY_HISTORY = "history";
    private static final String KEY_LAST_RAW = "last_raw";
    private static final String KEY_PAUSED = "paused";

    private final SharedPreferences prefs;

    public StepStore(Context ctx) {
        prefs = ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    public static String dayKey(long millis) {
        return new SimpleDateFormat("yyyy-MM-dd", Locale.US).format(new Date(millis));
    }

    public static String todayKey() {
        return dayKey(System.currentTimeMillis());
    }

    /** Day key n days before today (0 = today). */
    public static String dayKeyOffset(int daysAgo) {
        Calendar c = Calendar.getInstance();
        c.add(Calendar.DAY_OF_YEAR, -daysAgo);
        return dayKey(c.getTimeInMillis());
    }

    public synchronized Map<String, Integer> history() {
        Map<String, Integer> map = new TreeMap<String, Integer>();
        String raw = prefs.getString(KEY_HISTORY, "");
        if (raw != null && raw.length() > 0) {
            String[] parts = raw.split(";");
            for (int i = 0; i < parts.length; i++) {
                int eq = parts[i].indexOf('=');
                if (eq > 0) {
                    try {
                        map.put(parts[i].substring(0, eq),
                                Integer.parseInt(parts[i].substring(eq + 1)));
                    } catch (NumberFormatException ignored) { }
                }
            }
        }
        return map;
    }

    private synchronized void saveHistory(Map<String, Integer> map) {
        StringBuilder sb = new StringBuilder();
        for (Map.Entry<String, Integer> e : map.entrySet()) {
            if (sb.length() > 0) sb.append(';');
            sb.append(e.getKey()).append('=').append(e.getValue());
        }
        prefs.edit().putString(KEY_HISTORY, sb.toString()).apply();
    }

    public synchronized int stepsOn(String day) {
        Integer v = history().get(day);
        return v == null ? 0 : v;
    }

    public synchronized int todaySteps() {
        return stepsOn(todayKey());
    }

    /** Record a sensor reading. Returns today's total after the update. */
    public synchronized int onSensorValue(float rawValue) {
        long raw = (long) rawValue;
        long lastRaw = prefs.getLong(KEY_LAST_RAW, -1L);
        boolean paused = prefs.getBoolean(KEY_PAUSED, false);
        String today = todayKey();

        if (lastRaw < 0) {
            // First ever reading: baseline only, nothing to count yet.
            prefs.edit().putLong(KEY_LAST_RAW, raw).apply();
            return todaySteps();
        }

        long delta;
        if (raw < lastRaw) {
            // Counter reset = phone rebooted. The new raw value is the
            // number of steps taken since the reboot, so count all of it.
            delta = raw;
        } else {
            delta = raw - lastRaw;
        }
        prefs.edit().putLong(KEY_LAST_RAW, raw).apply();

        if (paused || delta <= 0) return todaySteps();
        if (delta > 50000) {
            // Sanity guard against a corrupt jump; never credit absurd leaps.
            return todaySteps();
        }

        Map<String, Integer> map = history();
        Integer cur = map.get(today);
        map.put(today, (cur == null ? 0 : cur) + (int) delta);
        saveHistory(map);
        return map.get(today);
    }

    public boolean paused() {
        return prefs.getBoolean(KEY_PAUSED, false);
    }

    public void setPaused(boolean paused) {
        // When pausing/resuming, drop the stored baseline so steps walked
        // while paused are never credited on resume; the next sensor event
        // simply re-baselines because we clear last_raw on a pause toggle.
        prefs.edit().putBoolean(KEY_PAUSED, paused)
                .putLong(KEY_LAST_RAW, -1L).apply();
    }

    /** Days sorted newest first. */
    public List<String> daysNewestFirst() {
        List<String> days = new ArrayList<String>(history().keySet());
        Collections.sort(days, new Comparator<String>() {
            @Override public int compare(String a, String b) { return b.compareTo(a); }
        });
        return days;
    }

    /** Totals for the last n days, oldest first, missing days = 0. */
    public int[] lastNDays(int n) {
        Map<String, Integer> map = history();
        int[] out = new int[n];
        for (int i = 0; i < n; i++) {
            Integer v = map.get(dayKeyOffset(n - 1 - i));
            out[i] = v == null ? 0 : v;
        }
        return out;
    }

    public String[] lastNDayKeys(int n) {
        String[] out = new String[n];
        for (int i = 0; i < n; i++) out[i] = dayKeyOffset(n - 1 - i);
        return out;
    }

    public static double distanceKm(int steps) {
        // Average stride 0.75 m.
        return steps * 0.75 / 1000.0;
    }

    public static int calories(int steps) {
        // Rough walking estimate, about 0.04 kcal per step.
        return (int) Math.round(steps * 0.04);
    }

    /** Import history from CSV text. Deliberately format-tolerant, because
     * exports differ: it recognises an ISO date (2026-10-26), a European
     * date (26.10.2026 or 26/10/2026), a compact date (20261026), and an
     * epoch-millis timestamp (the j4velin Pedometer export style), with
     * comma, semicolon or tab separators, and takes the first integer
     * after the date as the step count. Merging keeps the higher count
     * per day, so importing twice never doubles anything.
     * Returns the number of days added or raised. */
    public synchronized int importCsvText(String text) {
        if (text == null) return 0;
        Map<String, Integer> map = history();
        int changed = 0;
        java.util.regex.Pattern iso = java.util.regex.Pattern.compile("(\\d{4})-(\\d{2})-(\\d{2})");
        java.util.regex.Pattern eu = java.util.regex.Pattern.compile("(\\d{1,2})[./](\\d{1,2})[./](\\d{4})");
        java.util.regex.Pattern compact = java.util.regex.Pattern.compile("\\b(\\d{4})(\\d{2})(\\d{2})\\b");
        java.util.regex.Pattern epoch = java.util.regex.Pattern.compile("\\b(1\\d{12})\\b");
        String[] lines = text.split("\n");
        for (int li = 0; li < lines.length; li++) {
            String line = lines[li].trim();
            if (line.length() < 4) continue;
            String day = null;
            String rest = null;
            java.util.regex.Matcher m = iso.matcher(line);
            if (m.find()) {
                day = m.group(1) + "-" + m.group(2) + "-" + m.group(3);
                rest = line.substring(m.end());
            } else if ((m = eu.matcher(line)).find()) {
                int d = Integer.parseInt(m.group(1));
                int mo = Integer.parseInt(m.group(2));
                int y = Integer.parseInt(m.group(3));
                if (mo < 1 || mo > 12 || d < 1 || d > 31) continue;
                day = String.format(Locale.US, "%04d-%02d-%02d", y, mo, d);
                rest = line.substring(m.end());
            } else if ((m = epoch.matcher(line)).find()) {
                try {
                    day = dayKey(Long.parseLong(m.group(1)));
                } catch (NumberFormatException e) { continue; }
                rest = line.substring(m.end());
            } else if ((m = compact.matcher(line)).find()) {
                int mo = Integer.parseInt(m.group(2));
                int d = Integer.parseInt(m.group(3));
                if (mo < 1 || mo > 12 || d < 1 || d > 31) continue;
                day = m.group(1) + "-" + m.group(2) + "-" + m.group(3);
                rest = line.substring(m.end());
            }
            if (day == null || rest == null) continue;
            Integer steps = null;
            String[] tokens = rest.split("[;,\\t]");
            for (int t = 0; t < tokens.length; t++) {
                String digits = tokens[t].replaceAll("[^0-9]", "");
                if (digits.length() == 0) continue;
                try {
                    int v = Integer.parseInt(digits);
                    if (v >= 0 && v <= 300000) { steps = v; break; }
                } catch (NumberFormatException ignored) { }
            }
            if (steps == null) continue;
            Integer cur = map.get(day);
            if (cur == null || steps > cur) {
                map.put(day, steps);
                changed++;
            }
        }
        if (changed > 0) saveHistory(map);
        return changed;
    }

    public String toCsv() {
        StringBuilder sb = new StringBuilder("date,steps,distance_km,calories\n");
        List<String> days = new ArrayList<String>(history().keySet());
        Collections.sort(days);
        Map<String, Integer> map = history();
        for (String d : days) {
            int s = map.get(d);
            sb.append(d).append(',').append(s).append(',')
              .append(String.format(Locale.US, "%.2f", distanceKm(s))).append(',')
              .append(calories(s)).append('\n');
        }
        return sb.toString();
    }
}

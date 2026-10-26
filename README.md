# Oguri's Steps

A clean Android step counter. Counts with the phone's hardware step
sensor, works fully offline, and stores history only on the device.

## Features

- Today view: steps, distance, calories, approximate walking minutes
- 1x1 home-screen widget: transparent, just the step count
- History for 7 days, 30 days, 90 days and all time, with bar charts
  and a dashed average line; ranges past two months aggregate into
  weekly bars
- Averages count recorded days only; tap any bar for its exact date,
  steps and distance; the best day is highlighted in chart and list
- CSV export and import (days merge, keeping the higher count)
- No notifications, no accounts, no network, no goals

## Requirements

- Android 10 or newer with a hardware step counter sensor
- Physical activity permission; a battery-optimisation exemption is
  recommended so counting is not throttled

## Building

No Gradle: the app is plain Java on the Android framework, built with
aapt2, javac, d8, zipalign and apksigner from the Android SDK
build-tools and a JDK 17.

```sh
export JAVA_HOME=<jdk17>
export BT=<sdk>/build-tools/34.0.0
export ANDROID_JAR=<sdk>/platforms/android-34/android.jar
export PATH="$JAVA_HOME/bin:$BT:$PATH"
aapt2 compile --dir res -o build/res.zip
aapt2 link -o build/unsigned.apk -I $ANDROID_JAR \
    --manifest AndroidManifest.xml --java build/gen \
    --version-code 5 --version-name 1.2.2 build/res.zip
javac -encoding UTF-8 -source 8 -target 8 -cp $ANDROID_JAR \
    -d build/classes $(find src build/gen -name '*.java')
d8 --min-api 29 --output build/dex $(find build/classes -name '*.class')
(cd build/dex && zip ../unsigned.apk classes.dex)
zipalign -f -p 4 build/unsigned.apk build/aligned.apk
apksigner sign --ks oguris-steps.keystore --ks-key-alias oguris-steps \
    --out OgurisSteps-1.2.2.apk build/aligned.apk
```

The signing keystore is not in this repository. Package:
`app.oguri.steps`, minSdk 29, targetSdk 34.

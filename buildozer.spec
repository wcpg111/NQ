# Buildozer spec for NQ/MNQ 一键测算 (Android 快速版)

[app]
title = NQ_MNQ_一键测算
package.name = nqmnqcalc
package.domain = org.ck
source.dir = .
source.include_exts = py,png,jpg,kv
version = 0.1.0
requirements = python3,kivy
orientation = portrait
fullscreen = 0
android.api = 33
android.minapi = 21
android.archs = arm64-v8a,armeabi-v7a

# Entry point (we created main.py)
entrypoint = main.py

# Optional: app icon (uncomment and provide file)
# icon.filename = icon.png

[buildozer]
log_level = 2
warn_on_root = 0

[android]
# Permissions (uncomment if you later need storage/network)
# android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE


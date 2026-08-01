[app]
title = Paie Burkina Faso
package.name = paiebf
package.domain = org.gcmindustries

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json

version = 1.0

requirements = python3==3.11,hostpython3==3.11,kivy==2.3.1,requests,certifi
orientation = portrait
fullscreen = 0

icon.filename = %(source.dir)s/icon.png

android.permissions = INTERNET

# API/target Android - ajuste si besoin selon les exigences du Play Store
android.api = 34
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a

android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1

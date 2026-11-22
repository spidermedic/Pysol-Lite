[app]
title = PySol Lite
package.name = pysollite
package.domain = io.github.spidermedic
source.dir = ./stage
source.include_exts = py,png,wav,html,txt,css
source.exclude_exts = spec,gif
version.regex = VERSION = (.*)
version.filename = %(source.dir)s/version.txt
# charset_normalizer is spelled with an underscore on purpose: with a hyphen
# python-for-android picks an Android-only wheel that pip on a Mac refuses.
requirements = python3,kivy,pysol_cards,configobj,attrs,charset_normalizer==3.4.4
orientation = portrait, landscape
fullscreen = 0
android.presplash_color = #101010
android.permissions = WRITE_EXTERNAL_STORAGE, MANAGE_EXTERNAL_STORAGE
android.api = 34
android.minapi = 24
android.gradle_dependencies =
  androidx.appcompat:appcompat:1.4.2
android.enable_androidx = True
android.archs = arm64-v8a
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1

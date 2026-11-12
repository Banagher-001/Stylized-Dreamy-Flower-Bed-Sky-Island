#!/bin/sh
WEBKIT_RUNTIME=/workspace/.cache/ms-playwright/webkit-2336/minibrowser-gtk
export WEBKIT_EXEC_PATH="$WEBKIT_RUNTIME/bin"
export WEBKIT_INJECTED_BUNDLE_PATH="$WEBKIT_RUNTIME/lib"
export LD_LIBRARY_PATH="$WEBKIT_RUNTIME/lib:$WEBKIT_RUNTIME/sys/lib:/workspace/.cache/browser-deps/root/usr/lib/x86_64-linux-gnu"
exec "$WEBKIT_RUNTIME/bin/MiniBrowser" "$@"

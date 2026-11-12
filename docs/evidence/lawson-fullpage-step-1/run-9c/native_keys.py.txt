"""Send a browser-reserved Escape through XTest on this audit's private display."""
import ctypes as C
import ctypes.util
import os


class WindowAttributes(C.Structure):
    _fields_ = [('x', C.c_int), ('y', C.c_int), ('width', C.c_int), ('height', C.c_int), ('border_width', C.c_int), ('depth', C.c_int),
                ('visual', C.c_void_p), ('root', C.c_ulong), ('window_class', C.c_int), ('bit_gravity', C.c_int), ('win_gravity', C.c_int), ('backing_store', C.c_int),
                ('backing_planes', C.c_ulong), ('backing_pixel', C.c_ulong), ('save_under', C.c_int), ('colormap', C.c_ulong), ('map_installed', C.c_int), ('map_state', C.c_int),
                ('all_event_masks', C.c_long), ('your_event_mask', C.c_long), ('do_not_propagate_mask', C.c_long), ('override_redirect', C.c_int), ('screen', C.c_void_p)]


class ErrorEvent(C.Structure):
    _fields_ = [('type', C.c_int), ('display', C.c_void_p), ('resourceid', C.c_ulong), ('serial', C.c_ulong),
                ('error_code', C.c_ubyte), ('request_code', C.c_ubyte), ('minor_code', C.c_ubyte)]


class ClassHint(C.Structure):
    _fields_ = [('res_name', C.c_void_p), ('res_class', C.c_void_p)]


def browser_key(key='Escape'):
    assert key in ['Escape','new-tab']
    display_name = os.environ.get('DISPLAY', '')
    assert display_name in [':107', ':108'], 'Never address a shared/user display'
    x = C.CDLL(ctypes.util.find_library('X11'))
    test = C.CDLL(ctypes.util.find_library('Xtst'))
    x.XOpenDisplay.argtypes = [C.c_char_p]
    x.XOpenDisplay.restype = C.c_void_p
    x.XDefaultRootWindow.argtypes = [C.c_void_p]
    x.XDefaultRootWindow.restype = C.c_ulong
    x.XQueryTree.argtypes = [C.c_void_p, C.c_ulong, C.POINTER(C.c_ulong), C.POINTER(C.c_ulong), C.POINTER(C.POINTER(C.c_ulong)), C.POINTER(C.c_uint)]
    x.XFetchName.argtypes = [C.c_void_p, C.c_ulong, C.POINTER(C.c_void_p)]
    x.XGetWindowAttributes.argtypes = [C.c_void_p, C.c_ulong, C.POINTER(WindowAttributes)]
    x.XGetClassHint.argtypes = [C.c_void_p, C.c_ulong, C.POINTER(ClassHint)]
    x.XSetErrorHandler.argtypes = [C.c_void_p]
    x.XSetErrorHandler.restype = C.c_void_p
    x.XFree.argtypes = [C.c_void_p]
    x.XGetInputFocus.argtypes = [C.c_void_p, C.POINTER(C.c_ulong), C.POINTER(C.c_int)]
    x.XRaiseWindow.argtypes = [C.c_void_p, C.c_ulong]
    x.XSetInputFocus.argtypes = [C.c_void_p, C.c_ulong, C.c_int, C.c_ulong]
    x.XStringToKeysym.argtypes = [C.c_char_p]
    x.XStringToKeysym.restype = C.c_ulong
    x.XKeysymToKeycode.argtypes = [C.c_void_p, C.c_ulong]
    x.XKeysymToKeycode.restype = C.c_ubyte
    x.XSync.argtypes = [C.c_void_p, C.c_int]
    x.XCloseDisplay.argtypes = [C.c_void_p]
    test.XTestFakeKeyEvent.argtypes = [C.c_void_p, C.c_uint, C.c_int, C.c_ulong]
    d = x.XOpenDisplay(display_name.encode())
    assert d, display_name
    errors = []
    callback_type = C.CFUNCTYPE(C.c_int, C.c_void_p, C.POINTER(ErrorEvent))

    @callback_type
    def error_handler(display, event):
        errors.append({'errorCode': event.contents.error_code, 'requestCode': event.contents.request_code})
        return 0
    previous_handler = x.XSetErrorHandler(C.cast(error_handler, C.c_void_p))
    try:
        root = x.XDefaultRootWindow(d)
        found = []

        def walk(window, depth=0):
            title = C.c_void_p()
            text = ''
            if x.XFetchName(d, window, C.byref(title)) and title.value:
                text = C.string_at(title.value).decode(errors='replace')
                x.XFree(title)
            hint = ClassHint()
            classes = []
            if x.XGetClassHint(d, window, C.byref(hint)):
                for value in [hint.res_name, hint.res_class]:
                    if value:
                        classes.append(C.string_at(value).decode(errors='replace'))
                        x.XFree(value)
            identity = text + ' ' + ' '.join(classes)
            if 'lawson' in identity.lower() or 'chromium' in identity.lower():
                attrs = WindowAttributes()
                if x.XGetWindowAttributes(d, window, C.byref(attrs)) and attrs.map_state == 2 and attrs.width >= 500 and attrs.height >= 300:
                    found.append((10 if 'lawson' in identity.lower() else 1, window, identity, attrs.width, attrs.height))
            if depth >= 2:
                return
            r, parent, children, count = C.c_ulong(), C.c_ulong(), C.POINTER(C.c_ulong)(), C.c_uint()
            if x.XQueryTree(d, window, C.byref(r), C.byref(parent), C.byref(children), C.byref(count)):
                for i in range(count.value):
                    walk(children[i], depth + 1)
                if children:
                    x.XFree(children)
        walk(root)
        assert found, 'No original-page Chromium window on this private display'
        _, window, title, width, height = sorted(found, key=lambda v: v[0])[-1]
        before, revert = C.c_ulong(), C.c_int()
        x.XGetInputFocus(d, C.byref(before), C.byref(revert))
        x.XRaiseWindow(d, window)
        x.XSetInputFocus(d, window, 2, 0)
        x.XSync(d, 0)
        assert not errors, errors
        keycode = x.XKeysymToKeycode(d, x.XStringToKeysym(b'Escape' if key=='Escape' else b't'))
        assert keycode
        control = x.XKeysymToKeycode(d, x.XStringToKeysym(b'Control_L'))
        if key=='new-tab':test.XTestFakeKeyEvent(d, control, 1, 0)
        test.XTestFakeKeyEvent(d, keycode, 1, 0)
        test.XTestFakeKeyEvent(d, keycode, 0, 0)
        if key=='new-tab':test.XTestFakeKeyEvent(d, control, 0, 0)
        x.XSync(d, 0)
        assert not errors, errors
        return {'method': 'OS XTest '+('Escape; no document.exitFullscreen call' if key=='Escape' else 'Control+t; actual browser new tab'), 'display': display_name,
                'windowTitle': title, 'focusedWindow': window, 'windowSize': [width, height], 'previousFocus': before.value, 'keycode': keycode}
    finally:
        x.XCloseDisplay(d)
        x.XSetErrorHandler(previous_handler)


def escape():
    return browser_key('Escape')

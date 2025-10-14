# -*- coding: utf-8 -*-
import importlib.util
import sys

def _load_quick_app():
    path = 'Android_快速版_Kivy.py'
    spec = importlib.util.spec_from_file_location('android_quick_loaded', path)
    if spec is None or spec.loader is None:
        raise ImportError(f'无法加载 {path}')
    mod = importlib.util.module_from_spec(spec)
    sys.modules['android_quick_loaded'] = mod
    spec.loader.exec_module(mod)  # type: ignore
    return mod.QuickCalcApp

if __name__ == '__main__':
    QuickCalcApp = _load_quick_app()
    QuickCalcApp().run()

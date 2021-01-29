# this is a namespace package
try:
    import pkg_resources
    pkg_resources.declare_namespace(__name__)
    import pydevd_pycharm

    pydevd_pycharm.settrace('172.31.0.6', port=57892, stdoutToServer=True, stderrToServer=True, suspend=False)
except ImportError:
    import pkgutil
    __path__ = pkgutil.extend_path(__path__, __name__)

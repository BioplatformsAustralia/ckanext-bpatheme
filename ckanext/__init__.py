# this is a namespace package
try:
    import pkg_resources
    pkg_resources.declare_namespace(__name__)
    import pydevd_pycharm

    pydevd_pycharm.settrace('localhost', port=57891, stdoutToServer=True, stderrToServer=True)
except ImportError:
    import pkgutil
    __path__ = pkgutil.extend_path(__path__, __name__)

# this is a namespace package
try:
    import pkg_resources
    pkg_resources.declare_namespace(__name__)
    import pydevd_pycharm
    import os

    pydevd_pycharm.settrace('0.0.0.0', port=os.environ.get("DOCKER_DEBUG_PORT"), stdoutToServer=True, stderrToServer=True, suspend=False)
except ImportError:
    import pkgutil
    __path__ = pkgutil.extend_path(__path__, __name__)

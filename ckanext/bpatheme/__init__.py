import pydevd_pycharm
pydevd_pycharm.settrace('host.docker.internal', port=57892, stdoutToServer=True, stderrToServer=True, suspend=False)

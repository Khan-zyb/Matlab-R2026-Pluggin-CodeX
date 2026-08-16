# Contributing

Contributions are welcome for reliability, documentation, tests, and additional safe read-only tools.

Before opening a pull request:

1. Keep the plugin identifier and folder name as `matlab-r2026a`.
2. Do not weaken the R2026a release check or tool safety annotations.
3. Do not add MathWorks logos, proprietary MATLAB files, or license material.
4. Run `python -m unittest discover -s tests -v`.
5. Run `python -m py_compile plugins/matlab-r2026a/scripts/matlab_mcp_server.py`.
6. Test `matlab_info` on MATLAB R2026a when changing process-launch code.

Please describe the operating system, Python version, MATLAB update number, and expected behavior in bug reports without including sensitive paths or license information.

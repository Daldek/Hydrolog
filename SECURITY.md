# Security policy

## Supported versions

Security fixes go into the latest release of Hydrolog (and the development branch
`develop`). Older releases are not patched.

## Reporting a vulnerability

Please do not report vulnerabilities in public issues or pull requests.

Use GitHub's private vulnerability reporting: open the **Security** tab of
<https://github.com/Daldek/Hydrolog>, choose **Report a vulnerability** and describe
the problem, the affected version and, if possible, how to reproduce it. You get an
answer as soon as the maintainer can read the report; a fix is released as a patch
version and credited in the CHANGELOG unless you prefer otherwise.

## Scope

Hydrolog performs calculations on local files and makes no network requests. Reports
about path handling (the sandbox of the MCP server, `--allow-dir`), unsafe parsing of
input files or the supply chain of the package are in scope.

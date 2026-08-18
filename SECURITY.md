# Security Policy

## Supported Versions

OpenDHFS is currently experimental forensic research software and has not yet reached a stable release.

Until stable releases are available, security fixes will normally be applied to the current development version.

| Version | Supported |
| ------- | --------- |
| Development branch | Yes |
| Historical/experimental code | No |

## Reporting a Vulnerability

Please do not report security vulnerabilities through public GitHub issues.

Security vulnerabilities should be reported privately through the contact information published on the official OpenDHFS GitHub profile.

A useful vulnerability report should include, where possible:

- the affected OpenDHFS component;
- the OpenDHFS version or commit;
- operating system and relevant environment information;
- steps required to reproduce the issue;
- expected and observed behavior;
- potential security impact;
- and any proposed mitigation, if known.

Do not include confidential evidence, private surveillance footage, credentials, forensic images, personally identifiable information, or other sensitive case material in an initial vulnerability report.

## Forensic Data

OpenDHFS may be used with forensic images and other potentially sensitive data.

Security reports involving forensic workflows should use synthetic or appropriately sanitized examples whenever possible.

Never upload forensic images, recovered surveillance footage, credentials, client information, or confidential evidence to a public GitHub issue.

## Scope

Examples of security issues that may be relevant include:

- unintended modification of source evidence;
- unsafe handling of file paths or external processes;
- command injection;
- arbitrary file overwrite;
- unsafe temporary-file handling;
- maliciously crafted input causing unintended code execution;
- dependency vulnerabilities with practical impact on OpenDHFS;
- incorrect isolation between source evidence and derived artifacts;
- and security defects affecting the integrity or reproducibility of forensic output.

Recovery failure, unsupported storage formats, incomplete video reconstruction, incorrect assumptions about damaged metadata, and ordinary decoding failures are generally technical or forensic issues rather than security vulnerabilities.

Those may be reported through the normal issue tracker provided that no sensitive evidence is disclosed.

## Disclosure

Please allow the maintainers a reasonable opportunity to investigate and address a reported vulnerability before public disclosure.

OpenDHFS will attempt to document security-relevant fixes transparently while avoiding publication of information that unnecessarily exposes users to active exploitation.

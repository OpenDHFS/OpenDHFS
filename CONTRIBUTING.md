# Contributing to OpenDHFS

Thank you for your interest in contributing to OpenDHFS.

OpenDHFS is an open-source forensic research project focused on rigorous, reproducible analysis and recovery of video data from DVR/NVR storage.

Contributions are welcome, including code, documentation, format research, test cases, validation methodology, and technically supported observations.

## Core Contribution Principle

OpenDHFS should report what the evidence supports, not what the operator expects to find.

Contributions should preserve the distinction between:

- detection and validation;
- structural plausibility and decoder validity;
- recovered video and evidentiary relevance;
- temporal inference and confirmed timestamps;
- visual camera recognition and metadata-supported channel attribution;
- and recovery completion and demonstrated recovery-surface exhaustion.

## Before Contributing

Please check existing issues and discussions before starting substantial work.

For significant architectural changes, new storage formats, new recovery strategies, or changes to forensic classifications, opening a discussion or issue before implementation is recommended.

This helps avoid duplicated work and allows the underlying forensic assumptions to be reviewed before they become implementation decisions.

## Sensitive Evidence

Do not submit real confidential evidence to this repository.

This includes:

- forensic disk images;
- private CCTV footage;
- recovered surveillance video;
- client or case identifiers;
- credentials;
- personally identifiable information;
- confidential timestamps or location information;
- proprietary evidence obtained under restricted access;
- and artifacts that could identify an investigation.

Use synthetic, generated, public, or appropriately sanitized test material.

If a technical problem cannot be demonstrated without sensitive evidence, contact the project privately before sharing any material.

## Code Contributions

Code contributions should aim to be:

- readable;
- modular;
- reproducible;
- conservative in forensic conclusions;
- explicit about assumptions;
- and testable where practical.

Recovery logic should not silently transform uncertain observations into confirmed forensic conclusions.

When adding a recovery technique, document:

1. what structure or condition it detects;
2. what assumptions it makes;
3. what source data it reads;
4. whether it creates derived artifacts;
5. how results are validated;
6. known failure conditions;
7. and what conclusions the result does and does not support.

## Source Evidence

Code intended to operate on forensic images should use read-only access wherever technically possible.

A contribution that modifies source evidence, intentionally or unintentionally, will not be accepted as part of the standard forensic recovery workflow.

Derived artifacts should be written to separate output locations.

## Validation

Successful file creation is not sufficient validation.

Where appropriate, contributions should distinguish among:

- structural detection;
- syntactic validity;
- codec validity;
- successful decoding;
- temporal consistency;
- physical continuity;
- and forensic interpretation.

External validation using established tools such as FFmpeg and FFprobe is encouraged when appropriate.

## Camera and Channel Attribution

Do not infer camera, lens, or channel identity solely from visual appearance when presenting metadata-derived results.

Visual interpretation may be useful to an investigator, but it must remain distinguishable from attribution supported by surviving source metadata.

## Negative Results

Negative results are valuable.

A technique that reliably demonstrates why a candidate is undecodable, structurally incomplete, unsupported, or exhausted may be as useful as a technique that recovers additional video.

Do not suppress negative results merely to improve apparent recovery rates.

## Tests

New parsing, reconstruction, classification, and validation logic should include tests whenever practical.

Tests should preferably use:

- synthetic fixtures;
- minimal binary samples created specifically for testing;
- publicly redistributable material;
- or sanitized data for which redistribution is explicitly permitted.

Do not commit copyrighted or confidential surveillance material merely because it is useful as a test fixture.

## Documentation

Technical documentation should clearly distinguish:

- observed behavior;
- experimentally demonstrated behavior;
- inference;
- hypothesis;
- and known limitation.

Device-specific observations should not automatically be generalized to all DVR/NVR implementations.

## Pull Requests

Pull requests should provide:

- a concise description of the change;
- the problem being addressed;
- relevant technical or forensic rationale;
- testing performed;
- known limitations;
- and any effect on existing recovery classifications or output.

Small, focused pull requests are preferred over unrelated collections of changes.

## Security Issues

Do not disclose security vulnerabilities through ordinary public issues.

See `SECURITY.md` for responsible disclosure guidance.

## Licensing

By contributing to OpenDHFS, you agree that your contribution may be distributed under the project's Apache License 2.0.

Contributors must have the right to submit the code, documentation, test data, or other material included in their contribution.

## Scientific and Forensic Rigor

OpenDHFS does not measure success solely by how much data it recovers.

A technically justified negative conclusion is preferable to an unsupported positive result.

Contributions that increase recovery capability are welcome.

Contributions that improve our ability to determine when recovery is not technically supported are equally valuable.

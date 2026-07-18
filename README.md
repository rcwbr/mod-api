# mod-api<a name="new_project"></a>

[![PyPI - Version](https://img.shields.io/pypi/v/mod-api?style=flat-square&color=yellow)](https://pypi.org/project/mod-api/)
[![codecov](https://codecov.io/github/rcwbr/mod-api/graph/badge.svg?token=3407T4QQ6C&style=flat-square)](https://codecov.io/github/rcwbr/mod-api)
[![Python Black](https://img.shields.io/badge/code_style-black-black?style=flat-square&logo=black&logoColor=white)](https://github.com/psf/black?tab=readme-ov-file)
[![Dive Docker efficiency](<https://img.shields.io/badge/dynamic/regex?label=dive%20efficiency&logo=docker&logoColor=white&style=flat-square&url=https%3A%2F%2Fgithub.com%2Frcwbr%2Fmod-api%2Freleases%2Flatest%2Fdownload%2Fdive.json&search=%22efficiencyScore%22%3A%20%5B0-9%5D%2B.(%5B0-9%5D%7B2%7D)(%5B0-9%5D%7B2%7D)&replace=%241.%242%25>)](https://github.com/wagoodman/dive)
[![GitHub Release](https://img.shields.io/github/v/release/rcwbr/mod-api?logo=semver&style=flat-square)](https://github.com/rcwbr/mod-api/releases/latest)
[![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/rcwbr/mod-api/push-workflow.yaml?logo=github&style=flat-square)](https://github.com/rcwbr/mod-api/actions/workflows/push-workflow.yaml?query=branch%3Amain)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white&style=flat-square)](https://github.com/pre-commit/pre-commit)
[![Commitlint](https://img.shields.io/badge/commitlint-enabled-navy?style=flat-square&logo=commitlint)](https://github.com/conventional-changelog/commitlint)
[![Conventional Commits](https://img.shields.io/badge/conventional_commits-compliant-pink?style=flat-square&logo=conventionalcommits&logoColor=white)](https://www.conventionalcommits.org)

PLACEHOLDER: Project description.

<!-- mdformat-toc start --slug=github --maxlevel=6 --minlevel=1 -->

- [mod-api](#new_project)
  - [Overview](#overview)
  - [Usage](#usage)
  - [Contributing](#contributing)
    - [devcontainer](#devcontainer)
      - [devcontainer basic usage](#devcontainer-basic-usage)
      - [devcontainer Codespaces usage](#devcontainer-codespaces-usage)
      - [devcontainer pre-commit usage](#devcontainer-pre-commit-usage)
    - [CI/CD](#cicd)
    - [Settings](#settings)

<!-- mdformat-toc end -->

## Overview<a name="overview"></a>

PLACEHOLDER: Brief overview of what the project does.

## Usage<a name="usage"></a>

PLACEHOLDER: Add usage instructions using type-specific methods.

## Contributing<a name="contributing"></a>

### devcontainer<a name="devcontainer"></a>

This repo contains a [devcontainer definition](https://containers.dev/) in the `.devcontainer`
folder. It leverages the
[devcontainer cache build tool](https://github.com/rcwbr/devcontainer-cache-build) and
[layers defined in the dockerfile-partials repo](https://github.com/rcwbr/dockerfile-partials).

#### devcontainer basic usage<a name="devcontainer-basic-usage"></a>

The [devcontainer cache build tool](https://github.com/rcwbr/devcontainer-cache-build) requires
authentication to the GitHub package registry, as a token stored as
`MOD_API_DEVCONTAINER_INITIALIZE` (see
[instructions](https://github.com/rcwbr/devcontainer-cache-build/tree/main?tab=readme-ov-file#initialize-script-github-container-registry-setup)).

#### devcontainer Codespaces usage<a name="devcontainer-codespaces-usage"></a>

For use with Codespaces, the `MOD_API_DEVCONTAINER_INITIALIZE` token (see
[devcontainer basic usage](#devcontainer-basic-usage)) must be stored as a Codespaces secret (see
[instructions](https://github.com/rcwbr/devcontainer-cache-build/tree/main?tab=readme-ov-file#initialize-script-github-container-registry-setup)),
as must values for `USER`, and `UID` (see [useradd Codespaces usage](#useradd-codespaces-usage)).

#### devcontainer pre-commit usage<a name="devcontainer-pre-commit-usage"></a>

By default, the devcontainer configures [pre-commit](https://pre-commit.com/) hooks in the
repository to ensure commits pass basic testing. This includes enforcing
[conventional commit messages](https://www.conventionalcommits.org/en/v1.0.0/) as the standard for
this repository, via [commitlint](https://github.com/conventional-changelog/commitlint).

### CI/CD<a name="cicd"></a>

This repo uses the [release-it-gh-workflow](https://github.com/rcwbr/release-it-gh-workflow), with
the conventional-changelog image defined at any given ref, as its automation. It leverages the
[devcontainer-cache-build workflow](https://github.com/rcwbr/devcontainer-cache-build/blob/main/.github/workflows/devcontainer-cache-build.yaml)
to pre-generate devcontainer images, which are also used for the
[pre-commit workflow](https://github.com/rcwbr/dockerfile-partials/blob/main/.github/workflows/pre-commit.yaml).

### Settings<a name="settings"></a>

The GitHub repo settings for this repo are defined as code using the
[Probot settings GitHub App](https://probot.github.io/apps/settings/). Settings values are defined
in the `.github/settings.yml` file. Enabling automation of settings via this file requires
installing the app.

The settings applied are as recommended in the
[release-it-gh-workflow usage](https://github.com/rcwbr/release-it-gh-workflow/blob/4dea4eaf328b60f92dab1b5bd2a63daefa85404b/README.md?plain=1#L58),
including tag and branch protections, GitHub App and environment authentication, and required
checks.

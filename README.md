# GitHub Pull Request Average Review Time

This Python script fetches and analyzes GitHub pull requests to determine the average time it takes each user to get an approval.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)

## Prerequisites

- Python 3
- GitHub Personal Access Token

## Installation

1. Clone the repository:

```bash
git clone https://github.com/m-sanchez-dev/github-average-review-time.git
cd github-average-review-time
```

1. Install dependencies:

``` bash
pip install -r requirements.txt
```

## Usage

Run the main script to fetch and analyze pull request statistics:

``` bash
python average-time.py
```

## Configuration

Before running the script, ensure you set the required environment variables:

__`GITHUB_ACCESS_TOKEN`__: Your GitHub Personal Access Token.
__`GITHUB_REPO_OWNER`__: Owner of the GitHub repository.
__`GITHUB_REPO_NAME`__: Name of the GitHub repository.
__`LATEST_DATE`__: The latest date to consider for filtering old pull requests.

``` bash
export GITHUB_ACCESS_TOKEN="your-token"
export GITHUB_REPO_OWNER="your-username"
export GITHUB_REPO_NAME="your-repo"
export LATEST_DATE="2023-01-01"
```
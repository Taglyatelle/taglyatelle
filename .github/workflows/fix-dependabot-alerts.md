---
name: Fix Dependabot Alerts
description: Automatically create PRs to fix Dependabot security alerts by updating pyproject.toml
on:
  workflow_dispatch:
  schedule: weekly

permissions:
  contents: read
  pull-requests: read
  issues: read
  security-events: read

safe-outputs:
  create-pull-request:
    draft: false
    labels: [dependencies, security]

tools:
  github:
    toolsets: [repos, issues, pull_requests]

timeout-minutes: 20

engine:
  id: copilot
  model: gpt-4o
---

# Fix Dependabot Alerts

You are an AI agent tasked with fixing Dependabot security alerts in this Python project.

## Your Task

1. **Check for Dependabot alerts**:
   - Use GitHub tools to list open Dependabot alerts in the repository
   - Focus on alerts related to Python dependencies in `pyproject.toml`

2. **Analyze the alerts**:
   - Identify which dependencies need to be updated
   - Check the recommended versions to fix vulnerabilities
   - Understand the severity and impact of each alert

3. **Create a branch**:
   - Create a new branch with a descriptive name like `dependabot-fixes-YYYY-MM-DD`
   - Use the branch to make your changes

4. **Update pyproject.toml**:
   - Read the current `pyproject.toml` file
   - Update the vulnerable dependencies to their fixed versions
   - Ensure version constraints are appropriate (use `>=` for minimum versions where security fixes are needed)
   - Make sure to update dependencies in the correct section (`dependencies`, `optional-dependencies`, etc.)

5. **Create a Pull Request**:
   - Use the `create-pull-request` safe output to create a PR with your changes
   - Include a clear title like "Fix Dependabot security alerts"
   - In the PR description:
     - List all the vulnerabilities being fixed
     - Include CVE numbers and severity levels
     - Explain what dependencies were updated and to which versions
     - Link to the relevant Dependabot alerts

## Important Guidelines

- **Only update dependencies** that have active Dependabot alerts
- **Do not make breaking changes** - be conservative with version updates
- **Test compatibility** - check if the new versions are compatible with the Python version constraint (3.12)
- **Be thorough** - include all relevant security context in your PR description
- **If no alerts exist**, do not create a PR - just report that there are no active alerts to fix

## Safe Output Usage

When creating the pull request, use the `create-pull-request` safe output with:
- `head`: Your new branch name
- `base`: main (or the default branch)
- `title`: Clear, descriptive title
- `body`: Detailed description of fixes

## Example Workflow

1. List alerts: Check for Python dependency alerts
2. If alerts exist:
   - Create branch: `dependabot-fixes-YYYY-MM-DD` (use current date)
   - Update `pyproject.toml` with fixed versions
   - Commit changes with clear message
   - Create PR with detailed description
3. If no alerts exist:
   - Report: "No active Dependabot alerts found"

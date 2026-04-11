# Contributing to AI Research Agent

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Table of Contents

- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
- [Code Style](#code-style)
- [Submitting a Pull Request](#submitting-a-pull-request)
- [Reporting Issues](#reporting-issues)

## Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/research_agent.git
   cd research_agent
   ```
3. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and configure your environment variables.
5. Make sure [Ollama](https://ollama.ai/) is installed and running with your chosen model.

## How to Contribute

### Bug Fixes
- Check the [Issues](https://github.com/eboekenh/research_agent/issues) page first to see if the bug is already reported.
- If not, open a new issue describing the bug, steps to reproduce, and expected vs actual behavior.
- Reference the issue number in your PR.

### New Features
- Open an issue to discuss the feature before starting work.
- Keep changes focused — one feature per PR.

### Documentation
- Improvements to README, docstrings, or `docs/` are always welcome.

## Code Style

- Follow [PEP 8](https://pep8.org/) for Python code.
- Use type hints where possible.
- Write clear, descriptive commit messages (e.g., `fix: handle empty search results gracefully`).
- Add docstrings to new functions and classes.

## Submitting a Pull Request

1. Create a new branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Make your changes and commit:
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```
3. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
4. Open a Pull Request against the `main` branch.
5. Describe what your PR does and link any related issues.

## Reporting Issues

When reporting a bug, please include:
- Python version and OS
- Ollama model being used
- Steps to reproduce the issue
- Error message / traceback (if any)

---

Thank you for helping improve the AI Research Agent!

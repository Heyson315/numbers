# Contributing to vigilant-octo-engine

First off, thank you for considering contributing to vigilant-octo-engine! It's people like you that make this project such a great tool.

## Where do I go from here?

If you've noticed a bug or have a question, [search the issue tracker](https://github.com/HHR-CPA/vigilant-octo-engine/issues) to see if someone else has already created a ticket. If not, go ahead and [create a new one](https://github.com/HHR-CPA/vigilant-octo-engine/issues/new)!

## Fork & create a branch

If you want to contribute with code, please fork the repository and create a new branch from `main`.

## Get the code

```bash
git clone https://github.com/<your-username>/vigilant-octo-engine.git
cd vigilant-octo-engine
```

## Using GitHub Copilot

This repository is configured with GitHub Copilot instructions to help AI assistants understand our codebase better. If you're using GitHub Copilot or similar AI coding assistants:

- Review [`.github/copilot-instructions.md`](.github/copilot-instructions.md) for project-specific conventions and best practices
- Our custom security auditor agent can help identify compliance and security issues
- Follow the coding conventions and security guidelines outlined in the instructions

## Set up your environment

This project uses Python 3.8+ and Node.js.

### Backend (Python)

Create a virtual environment and install the dependencies:

```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt
```

### Frontend (TypeScript/React)

Install the dependencies:

```bash
cd frontend
npm install
```

## Running the application

### Backend

```bash
python src/api.py
```

### Frontend

```bash
cd frontend
npm run dev
```

## Running tests

### Backend

```bash
pytest
```

### Frontend

```bash
cd frontend
npm test
```

## Submitting a pull request

When you're ready to submit a pull request, please make sure to:

- Run all the tests to ensure everything is working correctly.
- Update the documentation if you've made any changes to the API or added new features.
- Add a descriptive title and a detailed description to your pull request.
- Reference any related issues in your pull request description.

Thank you for your contribution!

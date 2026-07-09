# AGENTS.md

## Project context

This is a portfolio backend project: Helpdesk API for Junior Python Backend Developer position.

The goal is to show clean backend skills:
- FastAPI
- PostgreSQL
- SQLAlchemy 2.0
- Alembic
- Pydantic v2
- JWT authentication
- Docker
- pytest
- clean project structure

## Coding rules

- Do not put all code in one file.
- Keep routes, schemas, models, services and dependencies separated.
- Use type hints.
- Use SQLAlchemy 2.0 style.
- Use Pydantic v2 style.
- Do not store secrets in code.
- Read settings from environment variables.
- Prefer simple readable code over clever abstractions.
- Do not add new dependencies without explaining why.
- Do not rewrite existing architecture without asking.

## Project structure

Use this structure:

app/
  main.py
  core/
  models/
  schemas/
  api/
    deps.py
    routes/
  services/
tests/
alembic/

## Before finishing a task

After making code changes:
- run ruff if available;
- run tests if available;
- check that imports are valid;
- in the final response, list changed files;
- explain how to run the project.

## Style

This is a portfolio project. Code should be understandable during an interview.
Avoid overengineering.

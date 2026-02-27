# Do NOT import app from app.main here!
# This causes circular dependencies when Uvicorn tries to import app.main:app
# Uvicorn will directly import from app.main instead.

__all__ = []

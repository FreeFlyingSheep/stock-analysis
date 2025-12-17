"""Base model and utility functions for database models."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all database models.

    This class serves as the declarative base for SQLAlchemy ORM models,
    providing common functionality and configuration for all database tables.
    """

"""Base class and configuration for SQLAlchemy ORM database models."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM database models.

    This declarative base class provides common functionality and configuration
    for all database models, enabling SQLAlchemy ORM mapping of Python classes
    to database tables.
    """

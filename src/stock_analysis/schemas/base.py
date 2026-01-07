"""Base schema for stock analysis application."""

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class BaseSchema(BaseModel):
    """Base schema with common Pydantic configuration.

    Provides common configuration for all schema classes including camelCase
    alias generation, validation settings, and attribute handling.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        validate_by_name=True,
        validate_by_alias=True,
        from_attributes=True,
        arbitrary_types_allowed=True,
    )

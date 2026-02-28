"""
Data Validation Template
Features: Pydantic schemas, custom validators, batch validation
"""
from datetime import datetime
from typing import Optional, List
from enum import Enum

from pydantic import BaseModel, Field, validator, ValidationError


class DataQuality(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ProductRecord(BaseModel):
    """Example schema for product data validation."""
    
    id: str = Field(..., min_length=1, description="Unique identifier")
    name: str = Field(..., min_length=1, max_length=255)
    price: float = Field(..., gt=0)
    currency: str = Field(default="USD", regex="^[A-Z]{3}$")
    category: str
    in_stock: bool = True
    created_at: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)
    
    @validator("name")
    def name_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Name cannot be empty or whitespace")
        return v.strip()
    
    @validator("price")
    def reasonable_price(cls, v):
        if v > 1_000_000:
            raise ValueError("Price seems unreasonably high")
        return v
    
    @validator("tags")
    def normalize_tags(cls, v):
        return [tag.lower().strip() for tag in v if tag.strip()]
    
    class Config:
        extra = "forbid"  # Reject unknown fields


class ValidationResult:
    """Container for batch validation results."""
    
    def __init__(self):
        self.valid: List[BaseModel] = []
        self.invalid: List[tuple] = []  # (record, error_message)
    
    @property
    def success_rate(self) -> float:
        total = len(self.valid) + len(self.invalid)
        return len(self.valid) / total if total > 0 else 0.0
    
    @property
    def quality_score(self) -> DataQuality:
        rate = self.success_rate
        if rate >= 0.95:
            return DataQuality.HIGH
        elif rate >= 0.80:
            return DataQuality.MEDIUM
        return DataQuality.LOW
    
    def summary(self) -> dict:
        return {
            "valid_count": len(self.valid),
            "invalid_count": len(self.invalid),
            "success_rate": f"{self.success_rate:.1%}",
            "quality": self.quality_score.value,
        }


def validate_batch(records: List[dict], model_class=ProductRecord) -> ValidationResult:
    """Validate a batch of records against a schema."""
    result = ValidationResult()
    
    for record in records:
        try:
            validated = model_class(**record)
            result.valid.append(validated)
        except ValidationError as e:
            error_msg = e.errors()[0]["msg"] if e.errors() else "Unknown error"
            result.invalid.append((record, error_msg))
    
    return result


# Example usage
if __name__ == "__main__":
    test_data = [
        {"id": "1", "name": "Widget", "price": 19.99, "category": "electronics"},
        {"id": "2", "name": "", "price": 9.99, "category": "toys"},  # Invalid: empty name
        {"id": "3", "name": "Gadget", "price": -5, "category": "electronics"},  # Invalid: negative price
    ]
    
    result = validate_batch(test_data)
    print(result.summary())

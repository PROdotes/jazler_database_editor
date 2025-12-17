from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum

class ValidationLevel(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

@dataclass
class ValidationIssue:
    message: str
    level: ValidationLevel = ValidationLevel.WARNING
    field: Optional[str] = None

@dataclass
class ValidationResult:
    is_valid: bool = True
    issues: List[ValidationIssue] = field(default_factory=list)
    
    def add_error(self, message: str, field_name: str = None):
        self.is_valid = False
        self.issues.append(ValidationIssue(message, ValidationLevel.ERROR, field_name))
        
    def add_warning(self, message: str, field_name: str = None):
        # Warnings don't necessarily make is_valid False, depends on business logic. 
        # In current app, warnings often stop save (e.g. "Year not set" shows warning dialog).
        # We'll treat them as issues.
        self.issues.append(ValidationIssue(message, ValidationLevel.WARNING, field_name))
        
    @property
    def has_issues(self):
        return len(self.issues) > 0

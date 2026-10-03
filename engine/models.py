"""Data models for Indonesian Legal AI Agent."""
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class RegulationStatus(str, Enum):
    BERLAKU = "BERLAKU"
    DICABUT_SEBAGIAN = "DICABUT_SEBAGIAN"
    DICABUT_SELURUHNYA = "DICABUT_SELURUHNYA"
    MENGUBAH = "MENGUBAH"
    DIUJI_MK = "DIUJI_MK"


class LegalHierarchyLevel(str, Enum):
    UUD1945 = "UUD_1945"
    TAP_MPR = "TAP_MPR"
    UU_PERPPU = "UU_PERPPU"
    PP = "PP"
    PERPRES = "PERPRES"
    PERMEN = "PERMEN"
    PUTUSAN_MK = "PUTUSAN_MK"
    YURISPRUDENSI_MA = "YURISPRUDENSI_MA"


class LegalArticle(BaseModel):
    """Represents a specific legal article / pasal."""
    id: str
    regulation_name: str
    regulation_number: str
    regulation_year: int
    hierarchy_level: LegalHierarchyLevel
    status: RegulationStatus = RegulationStatus.BERLAKU
    chapter: Optional[str] = None  # BAB
    part: Optional[str] = None     # Bagian
    article_number: str            # e.g. "340", "1 angka 14", "459"
    content: str                   # Isi teks pasal
    explanation: Optional[str] = None  # Penjelasan resmi
    effective_date: Optional[str] = None
    notes: Optional[str] = None    # Catatan peralihan / putusan MK


class FactCompleteness(BaseModel):
    """Evaluation of fact completeness for a legal query."""
    score: float = Field(ge=0.0, le=1.0, description="Completeness score 0.0 - 1.0")
    identified_elements: Dict[str, Any] = Field(default_factory=dict)
    missing_critical_elements: List[str] = Field(default_factory=list)
    needs_clarification: bool = False
    clarification_reasons: List[str] = Field(default_factory=list)


class ClarificationOption(BaseModel):
    label: str
    description: str
    legal_implication: str


class ClarificationQuestion(BaseModel):
    id: str
    question: str
    context_why_needed: str
    options: List[ClarificationOption] = Field(default_factory=list)
    allow_custom_input: bool = True


class LegalAssessment(BaseModel):
    """Structured IRAC legal assessment."""
    case_summary: str
    issue: str  # Isu hukum utama
    applicable_rules: List[LegalArticle]  # Pasal yang berlaku
    application_analysis: str  # Subsumpsi fakta ke unsur pasal (actus reus & mens rea)
    conclusion: str  # Kesimpulan sanksi / hak tersangka
    aggravating_factors: List[str] = Field(default_factory=list)  # Hal memberatkan
    mitigating_factors: List[str] = Field(default_factory=list)   # Hal meringankan
    procedural_steps: List[str] = Field(default_factory=list)     # Alur prosedural (misal penetapan tersangka)
    legal_disclaimer: str

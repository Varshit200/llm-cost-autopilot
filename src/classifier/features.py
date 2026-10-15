import re
from typing import Dict, Any, List
import numpy as np

SIMPLE_KEYWORDS = [
    r"\bextract\b", r"\breformat\b", r"\bconvert\b", r"\blookup\b", r"\bcapitalize\b",
    r"\blowercase\b", r"\buppercase\b", r"\bformat\b", r"\bparse\b", r"\bfind\b",
    r"\bdate\b", r"\bphone\b", r"\bemail\b", r"\breplace\b", r"\btrim\b", r"\bsplit\b"
]

MODERATE_KEYWORDS = [
    r"\bsummarize\b", r"\bsummary\b", r"\bclassify\b", r"\bcategorize\b", r"\bsentiment\b",
    r"\bexplain\b", r"\bdescribe\b", r"\boutline\b", r"\btable\b", r"\btranslate\b",
    r"\bbullet points\b", r"\bpros and cons\b", r"\bdraft\b", r"\bcondense\b"
]

COMPLEX_KEYWORDS = [
    r"\banalyze\b", r"\bcompare\b", r"\bcontrast\b", r"\bcritique\b", r"\bsynthesize\b",
    r"\barchitect\b", r"\bdesign\b", r"\bprove\b", r"\breason\b", r"\bdiagnose\b",
    r"\bevaluate\b", r"\bdebate\b", r"\btrade-off\b", r"\bstep-by-step\b", r"\bmulti-step\b",
    r"\bmathematical\b", r"\bheuristic\b", r"\bstrategy\b", r"\broot cause\b", r"\boptimize\b"
]

CONSTRAINT_KEYWORDS = [
    r"\bmust\b", r"\bcannot\b", r"\bdo not\b", r"\bdon't\b", r"\bat least\b", r"\bat most\b",
    r"\blimit\b", r"\bstrictly\b", r"\bonly\b", r"\bunder \d+\b", r"\bno more than\b",
    r"\bwithout using\b", r"\brequirements\b", r"\bconstraint\b"
]

STRUCTURE_KEYWORDS = [
    r"\bjson\b", r"\byaml\b", r"\bschema\b", r"\bsql\b", r"\bmarkdown table\b",
    r"\bregex\b", r"\bapi\b", r"\bxml\b", r"\btyped dict\b"
]

def extract_features(prompt: str) -> Dict[str, float]:
    """
    Extracts high-signal complexity features from an incoming prompt.
    Returns a dictionary of numerical feature values.
    """
    text = prompt.lower()
    words = text.split()
    word_count = len(words)
    char_length = len(text)
    
    # 1. Length & volume features
    token_count_approx = max(1.0, float(word_count * 1.35))
    
    # 2. Context detection
    has_context = 1.0 if any(k in text for k in ["context:", "given text:", "passage:", "background:", "document:", "input data:"]) or char_length > 600 else 0.0
    
    # 3. Instruction verb frequencies
    simple_verb_count = sum(len(re.findall(pat, text)) for pat in SIMPLE_KEYWORDS)
    moderate_verb_count = sum(len(re.findall(pat, text)) for pat in MODERATE_KEYWORDS)
    complex_verb_count = sum(len(re.findall(pat, text)) for pat in COMPLEX_KEYWORDS)
    
    # 4. Constraint count
    constraint_count = sum(len(re.findall(pat, text)) for pat in CONSTRAINT_KEYWORDS)
    
    # 5. Output structural complexity
    structure_score = sum(len(re.findall(pat, text)) for pat in STRUCTURE_KEYWORDS)
    
    # 6. Question and logical markers
    question_count = text.count("?")
    has_code_syntax = 1.0 if ("def " in text or "```" in text or "function" in text or "class " in text) else 0.0

    return {
        "token_count": token_count_approx,
        "char_length": float(char_length),
        "has_context": has_context,
        "simple_verb_count": float(simple_verb_count),
        "moderate_verb_count": float(moderate_verb_count),
        "complex_verb_count": float(complex_verb_count),
        "constraint_count": float(constraint_count),
        "structure_score": float(structure_score),
        "question_count": float(question_count),
        "has_code_syntax": has_code_syntax,
    }

FEATURE_NAMES = [
    "token_count",
    "char_length",
    "has_context",
    "simple_verb_count",
    "moderate_verb_count",
    "complex_verb_count",
    "constraint_count",
    "structure_score",
    "question_count",
    "has_code_syntax"
]

def features_to_vector(features: Dict[str, float]) -> np.ndarray:
    """Converts feature dictionary to ordered numpy 1D vector."""
    return np.array([features[name] for name in FEATURE_NAMES], dtype=np.float32)

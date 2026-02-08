#!/usr/bin/env python3
"""
Shared paper analysis module for LLM copyright protection research.

This module provides reusable components for analyzing papers:
- Classification categories
- LLM API client wrapper
- Paper analysis functions
"""

import json
import logging
from dataclasses import dataclass
from typing import Dict, Any, Optional

from openai import OpenAI

logger = logging.getLogger(__name__)

# ============================================================================
# Classification Categories
# ============================================================================

CATEGORIES = {
    "invasive": {
        "name": "Invasive Fingerprinting",
        "description": "Methods that embed information into the model's weights to construct fingerprint features for authentication and copyright protection.",
        "subcategories": {
            "weight_watermark": "Weight Watermark As Fingerprint - Embedding watermark information into model weights, biases, or other model parameters during training. The fingerprint can be extracted by comparing parameter fingerprints from a suspicious model with those in the owner's model.",
            "backdoor_watermark": "Backdoor Watermark As Fingerprint - Constructing special backdoor datasets and implanting them into the model, enabling the backdoored model to trigger predefined backdoor responses when encountering specific triggers. Suitable for black-box environments.",
            "knowledge_editing": "Knowledge Editing - Using localized knowledge editing to embed controllable fingerprint behaviors. By selectively modifying internal knowledge representations, it enables precise insertion of fingerprint triggers in specific semantic regions while preserving overall performance.",
        }
    },
    "non_invasive": {
        "name": "Non-invasive Fingerprinting",
        "description": "Methods that leverage inherent properties of language models without requiring modifications to their architecture or training process.",
        "subcategories": {
            "parameter_feature": "Parameter Feature as Fingerprint - Analyzing the weight space of language models to identify unique patterns and characteristics, such as singular values, eigenvalues, or weight matrix statistics.",
            "representation_feature": "Representation Feature as Fingerprint - Analyzing internal representations including activation patterns, hidden states, and output logits. These representations serve as intrinsic features for model identification.",
            "semantic_feature": "Semantic Feature as Fingerprint - Statistical analysis on generated content, exploiting linguistic patterns and semantic preferences exhibited by various LLMs as unique fingerprints.",
            "adversarial_example": "Adversarial Example as Fingerprint - Prompt optimization-based fingerprinting that optimizes prompts to produce predefined responses. The optimized prompt is effective only for the target model, serving as a stable fingerprint.",
        }
    },
    "fingerprint_transfer": {
        "name": "Fingerprint Transfer",
        "description": "Methods for transferring fingerprints across different models, enabling scalable protection by decoupling ownership signals from task learning.",
        "subcategories": {
            "transfer": "Fingerprint Transfer - Decoupling fingerprint from core task knowledge and transferring it to other models via LoRA adapters, task vectors, or weight manipulations. Enables 'fingerprint once, transfer many times' paradigm.",
        }
    },
    "fingerprint_removal": {
        "name": "Fingerprint Removal/Detection",
        "description": "Techniques for eliminating or detecting fingerprint information from a model, from an adversarial perspective.",
        "subcategories": {
            "inference_time": "Inference-time Removal - Techniques that suppress or bypass fingerprint signal activation during generation without retraining. Includes token forcing and generation revision intervention.",
            "training_time": "Training-time Removal - Targeted training procedures designed to disrupt fingerprint information embedded in model parameters, such as mismatched data fine-tuning.",
        }
    }
}

# ============================================================================
# Generation Configuration
# ============================================================================

@dataclass
class GenerationConfig:
    """Configuration for text generation."""
    max_tokens: int = 1024
    temperature: float = 0.3
    top_p: float = 0.9
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API call kwargs."""
        return {
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
        }


DEFAULT_GENERATION_CONFIG = GenerationConfig(
    max_tokens=1024,
    temperature=0.3,
    top_p=0.9,
)

# ============================================================================
# OpenAI API Client Wrapper
# ============================================================================

class OpenAIClientWrapper:
    """Wrapper for OpenAI-compatible API client."""

    def __init__(
        self,
        api_base: str,
        api_key: str = "EMPTY",
        model_name: Optional[str] = None,
        generation_config: Optional[GenerationConfig] = None,
    ):
        self.client = OpenAI(
            api_key=api_key,
            base_url=api_base,
        )
        self.generation_config = generation_config or DEFAULT_GENERATION_CONFIG
        
        # Use provided model name, or get from API
        if model_name:
            self.model_name = model_name
            logger.info(f"Using specified model: {self.model_name}")
        else:
            try:
                models = self.client.models.list()
                self.model_name = models.data[0].id if models.data else None
                logger.info(f"Connected to API. Model: {self.model_name}")
            except Exception as e:
                logger.warning(f"Could not get model name from API: {e}")
                self.model_name = None

    def generate(
        self,
        system_prompt: str,
        user_message: str,
        generation_config: Optional[GenerationConfig] = None,
    ) -> str:
        """Generate response with system prompt and user message.
        
        Args:
            system_prompt: The system prompt to set context
            user_message: The user's message/query
            generation_config: Optional override for generation settings
            
        Returns:
            Generated response text
        """
        config = generation_config or self.generation_config
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                **config.to_dict()
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"API call failed: {e}")
            raise

# ============================================================================
# Paper Analysis Functions
# ============================================================================

def build_classification_prompt() -> str:
    """Build the system prompt for paper classification."""
    categories_desc = []
    for cat_key, cat_info in CATEGORIES.items():
        categories_desc.append(f"\n## {cat_info['name']}")
        for sub_key, sub_desc in cat_info['subcategories'].items():
            categories_desc.append(f"  - {sub_key}: {sub_desc}")
    
    system_prompt = f"""You are an expert in LLM copyright protection research. Your task is to analyze academic paper abstracts and determine:

1. Whether the paper focuses on MODEL copyright protection (protecting the LLM model itself from unauthorized use, copying, or derivative works) - NOT text watermarking (which is about marking generated text to trace its origin).

2. If it is about model copyright protection, classify it into the appropriate category.

**IMPORTANT DISTINCTION:**
- MODEL copyright protection: Techniques to protect the model's intellectual property, trace model origins, verify model ownership, detect model theft/copying. This includes model fingerprinting, model watermarking (embedding marks in model weights or behavior), ownership verification.
- TEXT watermarking (NOT what we want): Techniques to mark/watermark the TEXT OUTPUT generated by LLMs to detect AI-generated content. This is about tracing text origin, not model origin.

**Categories for MODEL copyright protection:**
{chr(10).join(categories_desc)}

**Response Format (JSON):**
{{
    "is_model_copyright_protection": true/false,
    "reasoning": "Brief explanation of why this is/isn't about model copyright protection",
    "category": "category_key" or null,
    "subcategory": "subcategory_key" or null,
    "classification_confidence": "high/medium/low",
    "brief_summary": "One-sentence summary of the paper's contribution"
}}

If the paper is about TEXT watermarking (marking LLM-generated text), set is_model_copyright_protection to false.
If the paper is about general deep learning watermarking but not specifically for LLMs, note this in reasoning but still classify if applicable.
"""
    return system_prompt


def analyze_paper(
    client: OpenAIClientWrapper,
    paper: Dict[str, Any],
    include_extra_fields: bool = False
) -> Dict[str, Any]:
    """
    Analyze a paper using the LLM API to determine if it's about model copyright protection.
    
    Args:
        client: The OpenAI client wrapper
        paper: Paper dictionary with title and abstract (and optionally year, venue)
        include_extra_fields: If True, include year and venue in the analysis prompt
        
    Returns:
        Analysis result dictionary
    """
    system_prompt = build_classification_prompt()
    
    abstract = paper.get("abstract", "")
    if not abstract:
        abstract = "(Abstract not available)"
    
    # Build user message
    user_message_parts = [
        "Please analyze the following paper:",
        "",
        f"**Title:** {paper['title']}",
        "",
        f"**Abstract:**",
        abstract,
    ]
    
    if include_extra_fields:
        user_message_parts.extend([
            "",
            f"**Year:** {paper.get('year', 'Unknown')}",
            f"**Venue:** {paper.get('venue', 'Unknown')}",
        ])
    
    user_message_parts.extend([
        "",
        "Determine if this paper is about MODEL copyright protection (not text watermarking) and classify it accordingly."
    ])
    
    user_message = "\n".join(user_message_parts)

    try:
        response = client.generate(system_prompt, user_message)
        
        # Try to parse JSON from response
        # Find JSON in response (it might have extra text)
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        
        if json_start != -1 and json_end > json_start:
            json_str = response[json_start:json_end]
            result = json.loads(json_str)
        else:
            # If no valid JSON, create a default response
            paper_title = paper.get('title', 'Unknown')[:50]
            logger.warning(f"Could not parse JSON from response for paper: {paper_title}")
            result = {
                "is_model_copyright_protection": False,
                "reasoning": f"Failed to parse LLM response: {response[:200]}",
                "category": None,
                "subcategory": None,
                "classification_confidence": "low",
                "brief_summary": "Analysis failed"
            }
            
    except json.JSONDecodeError as e:
        paper_title = paper.get('title', 'Unknown')[:50]
        logger.warning(f"JSON decode error for paper {paper_title}: {e}")
        result = {
            "is_model_copyright_protection": False,
            "reasoning": f"JSON parse error: {str(e)}",
            "category": None,
            "subcategory": None,
            "classification_confidence": "low",
            "brief_summary": "Analysis failed"
        }
    except Exception as e:
        paper_title = paper.get('title', 'Unknown')[:50]
        logger.error(f"Error analyzing paper {paper_title}: {e}")
        result = {
            "is_model_copyright_protection": False,
            "reasoning": f"Analysis error: {str(e)}",
            "category": None,
            "subcategory": None,
            "classification_confidence": "low",
            "brief_summary": "Analysis failed"
        }
    
    return result

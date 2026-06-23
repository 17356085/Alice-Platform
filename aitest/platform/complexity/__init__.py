"""Complexity Routing — 自适应 SOP 流水线路由。

用法:
    from aitest.platform.complexity import ComplexityClassifier, complexity_assess
    classifier = ComplexityClassifier()
    profile = classifier.classify(discovery_data)
    pipeline = pipeline_for_tier(profile.tier)
"""
from aitest.platform.complexity.factors import (
    ComplexityTier, PageComplexityProfile,
    SIMPLE_PIPELINE, STANDARD_PIPELINE, COMPLEX_PIPELINE,
    pipeline_for_tier, score_to_tier,
)
from aitest.platform.complexity.classifier import ComplexityClassifier


def complexity_assess(page_data: dict = None, page_title: str = "") -> dict:
    """快捷函数：评估页面复杂度并返回 pipeline。

    Returns:
        {"tier": "simple"|"standard"|"complex",
         "score": 0-100,
         "pipeline": ["agent1", "agent2", ...],
         "profile": PageComplexityProfile}
    """
    classifier = ComplexityClassifier()
    profile = classifier.classify(page_data, page_title)
    return {
        "tier": profile.tier.value,
        "score": profile.score,
        "pipeline": pipeline_for_tier(profile.tier),
        "profile": profile,
    }

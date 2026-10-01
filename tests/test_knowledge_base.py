"""
Unit tests for Knowledge Base queries and Agri-Assistant Q&A.
"""
from utils.knowledge_base import KnowledgeBase


def test_knowledge_base_loading():
    """Verify knowledge base loads curated crops successfully."""
    kb = KnowledgeBase()
    crops = kb.get_all_crops()
    assert len(crops) >= 15, "Should have at least 15 crops in knowledge base"
    assert "rice" in crops
    assert "wheat" in crops
    assert "cotton" in crops


def test_get_specific_crop():
    """Verify specific crop retrieval."""
    kb = KnowledgeBase()
    rice = kb.get_crop("rice")
    assert rice is not None
    assert rice["name"] == "Rice"
    assert "suitable_soil" in rice
    assert "irrigation_guidance" in rice


def test_assistant_qa():
    """Verify keyword Q&A engine responds sensibly."""
    kb = KnowledgeBase()
    
    # Test high rainfall query
    ans_rain = kb.answer_query("What crop is suitable for high rainfall?")
    assert "Rice" in ans_rain["answer"] or "Banana" in ans_rain["answer"] or "Jute" in ans_rain["answer"]

    # Test soil for rice
    ans_rice = kb.answer_query("What soil conditions are suitable for rice?")
    assert "Soil" in ans_rice["answer"] or "Clayey" in ans_rice["answer"] or "Rice" in ans_rice["answer"]

    # Test wheat season
    ans_wheat = kb.answer_query("What is the recommended season for wheat?")
    assert "Rabi" in ans_wheat["answer"] or "Wheat" in ans_wheat["answer"]

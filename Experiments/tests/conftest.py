"""
Pytest configuration and shared fixtures.
"""

import pytest
import pandas as pd
import tempfile
from pathlib import Path


@pytest.fixture
def sample_base_data():
    """Create sample base dataset for testing."""
    return pd.DataFrame({
        'paragraph': ['para1', 'para2', 'para3', 'para4'],
        'report': ['report1.pdf', 'report1.pdf', 'report2.pdf', 'report2.pdf'],
        'question': ['q1', 'q1', 'q2', 'q2'],
        'relevance': [0.0, 1.0, 2.0, 3.0],
        'relevant_text': ['text1', 'text2', 'text3', 'text4'],
        'relevant_text_sim': [0.5, 0.6, 0.7, 0.8],
        'sim_text_relevance': [1.0, 2.0, 2.0, 3.0],
    })


@pytest.fixture
def sample_search_data():
    """Create sample search results for testing."""
    return pd.DataFrame({
        'paragraph': ['para1', 'para2', 'para3'],
        'report': ['./Reports/report1.pdf', './Reports/report1.pdf', './Reports/report2.pdf'],
        'question': ['q1', 'q1', 'q2'],
        'relevance': [0.0, 0.0, 0.0],
        'question__question_with_IR_150len': [0, 1, 0],
        'simple_IR__question_with_IR_150len': [1, 1, 1],
    })


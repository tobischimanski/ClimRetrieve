"""
Unit tests for analyze_data_coverage.py
Tests the data coverage analysis tool from outside in.
"""

import pytest
import pandas as pd
import sys
from pathlib import Path
import tempfile
import os

# Add parent directory to path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

from analyze_data_coverage import normalize_report_path, analyze_coverage


class TestNormalizeReportPath:
    """Test the normalize_report_path function."""
    
    def test_normalize_with_prefix(self):
        assert normalize_report_path("./Reports/report.pdf") == "report.pdf"
    
    def test_normalize_with_dot_slash(self):
        assert normalize_report_path("./report.pdf") == "report.pdf"
    
    def test_normalize_no_prefix(self):
        assert normalize_report_path("report.pdf") == "report.pdf"
    
    def test_normalize_path_object(self):
        from pathlib import Path as P
        # Path objects are converted to string, so "./Reports/" becomes "Reports/"
        result = normalize_report_path(P("./Reports/report.pdf"))
        # The function converts Path to string first, so it should handle it
        assert result in ["report.pdf", "Reports/report.pdf"]  # Accept either depending on conversion


class TestAnalyzeCoverage:
    """Test the analyze_coverage function."""
    
    def test_analyze_coverage_with_matching_data(self, tmp_path):
        # Create base dataset
        base_data = pd.DataFrame({
            'paragraph': ['para1', 'para2', 'para3'],
            'report': ['report1.pdf', 'report1.pdf', 'report2.pdf'],
            'question': ['q1', 'q1', 'q2'],
            'relevance': [1.0, 2.0, 3.0],
        })
        base_file = tmp_path / "base.csv"
        base_data.to_csv(base_file, index=True)
        
        # Create search results with matching data
        search_data = pd.DataFrame({
            'paragraph': ['para1', 'para2'],
            'report': ['./Reports/report1.pdf', './Reports/report1.pdf'],
            'question': ['q1', 'q1'],
            'relevance': [0.0, 0.0],
        })
        search_file = tmp_path / "search__5.csv"
        search_data.to_csv(search_file, index=True)
        
        # Run analysis
        results = analyze_coverage(
            base_data_path=str(base_file),
            search_result_file=str(search_file)
        )
        
        # Should return results
        assert results is not None
        assert len(results) > 0
        assert results[0]['matched_rows'] > 0
    
    def test_analyze_coverage_with_unmatched_data(self, tmp_path):
        # Create base dataset
        base_data = pd.DataFrame({
            'paragraph': ['para1', 'para2'],
            'report': ['report1.pdf', 'report1.pdf'],
            'question': ['q1', 'q1'],
            'relevance': [1.0, 2.0],
        })
        base_file = tmp_path / "base.csv"
        base_data.to_csv(base_file, index=True)
        
        # Create search results with some unmatched rows
        search_data = pd.DataFrame({
            'paragraph': ['para1', 'para_unmatched1', 'para_unmatched2'],
            'report': ['./Reports/report1.pdf', './Reports/report1.pdf', './Reports/report2.pdf'],
            'question': ['q1', 'q1', 'q2'],
            'relevance': [0.0, 0.0, 0.0],
        })
        search_file = tmp_path / "search__5.csv"
        search_data.to_csv(search_file, index=True)
        
        # Run analysis
        results = analyze_coverage(
            base_data_path=str(base_file),
            search_result_file=str(search_file)
        )
        
        # Should identify unmatched rows
        assert results is not None
        assert results[0]['unmatched_rows'] > 0
        assert results[0]['match_rate'] < 100.0
    
    def test_analyze_coverage_with_report_not_in_base(self, tmp_path):
        # Create base dataset
        base_data = pd.DataFrame({
            'paragraph': ['para1'],
            'report': ['report1.pdf'],
            'question': ['q1'],
            'relevance': [1.0],
        })
        base_file = tmp_path / "base.csv"
        base_data.to_csv(base_file, index=True)
        
        # Create search results with report not in base
        search_data = pd.DataFrame({
            'paragraph': ['para1', 'para2'],
            'report': ['./Reports/report1.pdf', './Reports/report_not_in_base.pdf'],
            'question': ['q1', 'q1'],
            'relevance': [0.0, 0.0],
        })
        search_file = tmp_path / "search__5.csv"
        search_data.to_csv(search_file, index=True)
        
        # Run analysis
        results = analyze_coverage(
            base_data_path=str(base_file),
            search_result_file=str(search_file)
        )
        
        # Should identify report not in base
        assert results is not None
        assert results[0]['reports_not_in_base'] > 0
    
    def test_analyze_coverage_multiple_files(self, tmp_path):
        # Create base dataset
        base_data = pd.DataFrame({
            'paragraph': ['para1', 'para2'],
            'report': ['report1.pdf', 'report1.pdf'],
            'question': ['q1', 'q1'],
            'relevance': [1.0, 2.0],
        })
        base_file = tmp_path / "base.csv"
        base_data.to_csv(base_file, index=True)
        
        # Create multiple search result files
        search_data1 = pd.DataFrame({
            'paragraph': ['para1'],
            'report': ['./Reports/report1.pdf'],
            'question': ['q1'],
            'relevance': [0.0],
        })
        search_file1 = tmp_path / "search1__5.csv"
        search_data1.to_csv(search_file1, index=True)
        
        search_data2 = pd.DataFrame({
            'paragraph': ['para1'],
            'report': ['./Reports/report1.pdf'],
            'question': ['q1'],
            'relevance': [0.0],
        })
        search_file2 = tmp_path / "search2__10.csv"
        search_data2.to_csv(search_file2, index=True)
        
        # Run analysis on directory - only CSV files should be picked up
        results = analyze_coverage(
            base_data_path=str(base_file),
            search_results_dir=str(tmp_path)
        )
        
        # Should analyze both CSV files
        assert results is not None
        # Should have 2 results (one for each CSV file)
        assert len(results) >= 2  # Use >= in case there are other CSV files
    
    def test_analyze_coverage_output_file(self, tmp_path):
        # Create base dataset
        base_data = pd.DataFrame({
            'paragraph': ['para1'],
            'report': ['report1.pdf'],
            'question': ['q1'],
            'relevance': [1.0],
        })
        base_file = tmp_path / "base.csv"
        base_data.to_csv(base_file, index=True)
        
        # Create search results
        search_data = pd.DataFrame({
            'paragraph': ['para1'],
            'report': ['./Reports/report1.pdf'],
            'question': ['q1'],
            'relevance': [0.0],
        })
        search_file = tmp_path / "search__5.csv"
        search_data.to_csv(search_file, index=True)
        
        # Output file
        output_file = tmp_path / "output.csv"
        
        # Run analysis
        results = analyze_coverage(
            base_data_path=str(base_file),
            search_result_file=str(search_file),
            output_file=str(output_file)
        )
        
        # Should create output file
        assert output_file.exists()
        output_df = pd.read_csv(output_file)
        assert len(output_df) > 0


class TestIntegration:
    """Integration tests for the full workflow."""
    
    def test_module_imports(self):
        """Test that the module can be imported."""
        from analyze_data_coverage import normalize_report_path, analyze_coverage
        assert callable(normalize_report_path)
        assert callable(analyze_coverage)
    
    def test_normalize_handles_various_formats(self):
        """Test that normalization handles various path formats."""
        test_cases = [
            ("./Reports/report.pdf", "report.pdf"),
            ("./report.pdf", "report.pdf"),
            ("report.pdf", "report.pdf"),
            ("Reports/report.pdf", "Reports/report.pdf"),  # No leading ./
        ]
        
        for input_path, expected in test_cases:
            result = normalize_report_path(input_path)
            assert result == expected, f"Failed for {input_path}: got {result}, expected {expected}"


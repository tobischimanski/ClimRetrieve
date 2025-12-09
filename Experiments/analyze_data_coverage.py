"""
Analysis tool for data coverage and matching between base dataset and search results.

This script analyzes:
- Match rates between base dataset and search results
- Unmatched rows and why they can't be matched
- Reports and questions coverage
- Paragraphs not in base dataset
"""

import pandas as pd
import glob
import argparse
from pathlib import Path


def normalize_report_path(report_path):
    """Normalize report paths for comparison."""
    return str(report_path).replace("./Reports/", "").replace("./", "")


def analyze_coverage(base_data_path, search_results_dir=None, search_result_file=None, output_file=None):
    """
    Analyze data coverage between base dataset and search results.
    
    Parameters:
    -----------
    base_data_path : str
        Path to the base dataset CSV file
    search_results_dir : str, optional
        Directory containing search result CSV files (analyzes all)
    search_result_file : str, optional
        Single search result CSV file to analyze
    output_file : str, optional
        Path to save detailed analysis report (CSV)
    """
    # Load base dataset
    print("Loading base dataset...")
    base = pd.read_csv(base_data_path, index_col=0)
    base["report_normalized"] = base["report"]
    
    # Determine which search result files to analyze
    if search_result_file:
        search_files = [search_result_file]
    elif search_results_dir:
        search_files = glob.glob(f"{search_results_dir}/*.csv")
    else:
        # Default to Experiments/Embedding_Search_Results
        search_files = glob.glob("./Embedding_Search_Results/*.csv")
    
    if not search_files:
        print("No search result files found!")
        return
    
    print(f"Found {len(search_files)} search result file(s) to analyze\n")
    
    # Analyze each search result file
    all_results = []
    
    for search_file in search_files:
        print("=" * 80)
        print(f"Analyzing: {Path(search_file).name}")
        print("=" * 80)
        
        # Load search results
        search = pd.read_csv(search_file, index_col=0)
        search["report_normalized"] = search["report"].apply(normalize_report_path)
        
        # Perform merge
        merged = search.merge(
            base[["paragraph", "report_normalized", "question", "relevance"]],
            on=["paragraph", "report_normalized", "question"],
            how="left",
            suffixes=("_old", "_new"),
            indicator=True
        )
        
        # Calculate statistics
        total_rows = len(search)
        matched_rows = len(merged[merged["_merge"] == "both"])
        unmatched_rows = len(merged[merged["_merge"] == "left_only"])
        match_rate = (matched_rows / total_rows * 100) if total_rows > 0 else 0
        
        print(f"\n📊 OVERALL STATISTICS")
        print(f"   Total rows in search results: {total_rows:,}")
        print(f"   Matched rows: {matched_rows:,} ({match_rate:.1f}%)")
        print(f"   Unmatched rows: {unmatched_rows:,} ({100-match_rate:.1f}%)")
        
        # Analyze unmatched rows
        unmatched = merged[merged["_merge"] == "left_only"].copy()
        
        # Initialize variables for cases with no unmatched rows
        unmatched_paras = set()
        paras_not_in_base = set()
        reports_not_in_base = set()
        
        if len(unmatched) > 0:
            print(f"\n🔍 UNMATCHED ROWS ANALYSIS")
            
            # 1. Paragraphs not in base dataset
            unmatched_paras = set(unmatched["paragraph"].unique())
            base_paras = set(base["paragraph"].unique())
            paras_not_in_base = unmatched_paras - base_paras
            
            print(f"\n   1. Paragraphs not in base dataset:")
            print(f"      - Unique unmatched paragraphs: {len(unmatched_paras):,}")
            print(f"      - Paragraphs that don't exist in base: {len(paras_not_in_base):,}")
            print(f"      - Paragraphs that exist but don't match: {len(unmatched_paras - paras_not_in_base):,}")
            print(f"      → These are paragraphs retrieved by embedding search that were")
            print(f"        NOT manually annotated in the expert-annotated dataset")
            
            # 2. Reports not in base dataset
            reports_not_in_base = set(unmatched["report_normalized"].unique()) - set(base["report_normalized"].unique())
            print(f"\n   2. Reports not in base dataset: {len(reports_not_in_base)}")
            if len(reports_not_in_base) > 0:
                for report in sorted(reports_not_in_base):
                    count = len(unmatched[unmatched["report_normalized"] == report])
                    print(f"      - {report}: {count:,} unmatched rows")
            
            # 3. Breakdown by report
            print(f"\n   3. Unmatched rows by report (top 10):")
            unmatched_by_report = unmatched["report_normalized"].value_counts().head(10)
            for report, count in unmatched_by_report.items():
                in_base = report in base["report_normalized"].unique()
                marker = "✓" if in_base else "✗"
                pct = (count / len(unmatched) * 100)
                print(f"      {marker} {report}: {count:,} rows ({pct:.1f}%)")
            
            # 4. Breakdown by question
            print(f"\n   4. Unmatched rows by question (top 10):")
            unmatched_by_question = unmatched["question"].value_counts().head(10)
            for question, count in unmatched_by_question.items():
                pct = (count / len(unmatched) * 100)
                question_short = question[:70] + "..." if len(question) > 70 else question
                print(f"      - {question_short}: {count:,} rows ({pct:.1f}%)")
        
        # Report coverage
        print(f"\n📋 COVERAGE ANALYSIS")
        base_reports = set(base["report_normalized"].unique())
        search_reports = set(search["report_normalized"].unique())
        common_reports = base_reports & search_reports
        only_in_base = base_reports - search_reports
        only_in_search = search_reports - base_reports
        
        print(f"   Reports in base dataset: {len(base_reports)}")
        print(f"   Reports in search results: {len(search_reports)}")
        print(f"   Common reports: {len(common_reports)}")
        if only_in_base:
            print(f"   Reports only in base: {len(only_in_base)}")
            for r in sorted(only_in_base)[:5]:
                print(f"      - {r}")
        if only_in_search:
            print(f"   Reports only in search: {len(only_in_search)}")
            for r in sorted(only_in_search):
                print(f"      - {r}")
        
        base_questions = set(base["question"].unique())
        search_questions = set(search["question"].unique())
        common_questions = base_questions & search_questions
        only_in_base_q = base_questions - search_questions
        only_in_search_q = search_questions - base_questions
        
        print(f"\n   Questions in base dataset: {len(base_questions)}")
        print(f"   Questions in search results: {len(search_questions)}")
        print(f"   Common questions: {len(common_questions)}")
        if only_in_base_q:
            print(f"   Questions only in base: {len(only_in_base_q)}")
        if only_in_search_q:
            print(f"   Questions only in search: {len(only_in_search_q)}")
        
        # Store results
        file_info = Path(search_file).stem
        if "__" in file_info:
            parts = file_info.split("__")
            embedding = parts[0]
            topk = parts[1] if len(parts) > 1 else "unknown"
        else:
            embedding = "unknown"
            topk = "unknown"
        
        all_results.append({
            "file": Path(search_file).name,
            "embedding": embedding,
            "topk": topk,
            "total_rows": total_rows,
            "matched_rows": matched_rows,
            "unmatched_rows": unmatched_rows,
            "match_rate": match_rate,
            "unique_unmatched_paragraphs": len(unmatched_paras) if len(unmatched) > 0 else 0,
            "paragraphs_not_in_base": len(paras_not_in_base) if len(unmatched) > 0 else 0,
            "reports_not_in_base": len(reports_not_in_base),
            "common_reports": len(common_reports),
            "common_questions": len(common_questions),
        })
        
        print()
    
    # Summary across all files
    if len(all_results) > 1:
        print("=" * 80)
        print("SUMMARY ACROSS ALL FILES")
        print("=" * 80)
        summary_df = pd.DataFrame(all_results)
        print(summary_df.to_string(index=False))
    
    # Save output file if requested (even for single file)
    if output_file and len(all_results) > 0:
        summary_df = pd.DataFrame(all_results)
        summary_df.to_csv(output_file, index=False)
        print(f"\nSummary saved to: {output_file}")
    
    return all_results


def main():
    parser = argparse.ArgumentParser(
        description="Analyze data coverage between base dataset and search results"
    )
    parser.add_argument(
        "--base-data",
        type=str,
        default="../Report-Level Dataset/ClimRetrieve_ReportLevel_V1.csv",
        help="Path to base dataset CSV file"
    )
    parser.add_argument(
        "--search-dir",
        type=str,
        default="./Embedding_Search_Results",
        help="Directory containing search result CSV files"
    )
    parser.add_argument(
        "--search-file",
        type=str,
        default=None,
        help="Single search result CSV file to analyze (overrides --search-dir)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to save summary CSV file"
    )
    
    args = parser.parse_args()
    
    analyze_coverage(
        base_data_path=args.base_data,
        search_results_dir=args.search_dir if not args.search_file else None,
        search_result_file=args.search_file,
        output_file=args.output
    )


if __name__ == "__main__":
    main()


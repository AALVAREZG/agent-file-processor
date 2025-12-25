"""
Table Extraction Experiment Script

This script tests different pdfplumber table extraction strategies
to find the optimal settings for liquidation PDF documents.
"""
import pdfplumber
import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime


# Define different extraction strategies to test
STRATEGIES = {
    "default": {
        "name": "Default (lines strategy)",
        "settings": {}  # pdfplumber defaults
    },
    "lines_strict": {
        "name": "Lines Strict",
        "settings": {
            "vertical_strategy": "lines_strict",
            "horizontal_strategy": "lines_strict",
        }
    },
    "text_based": {
        "name": "Text-based detection",
        "settings": {
            "vertical_strategy": "text",
            "horizontal_strategy": "text",
        }
    },
    "tight_snap": {
        "name": "Tight snap tolerance (prevents merging)",
        "settings": {
            "snap_tolerance": 1,
            "join_tolerance": 1,
        }
    },
    "loose_snap": {
        "name": "Loose snap tolerance (allows merging)",
        "settings": {
            "snap_tolerance": 10,
            "join_tolerance": 10,
        }
    },
    "text_tight": {
        "name": "Text-based + Tight tolerance",
        "settings": {
            "vertical_strategy": "text",
            "horizontal_strategy": "text",
            "text_tolerance": 1,
            "text_x_tolerance": 1,
            "text_y_tolerance": 1,
        }
    },
    "text_loose": {
        "name": "Text-based + Loose tolerance",
        "settings": {
            "vertical_strategy": "text",
            "horizontal_strategy": "text",
            "text_tolerance": 5,
            "text_x_tolerance": 5,
            "text_y_tolerance": 5,
        }
    },
}


def analyze_table_structure(table: List[List]) -> Dict[str, Any]:
    """Analyze the structure of an extracted table."""
    if not table:
        return {
            "num_rows": 0,
            "num_cols": 0,
            "cells_with_newlines": 0,
            "empty_cells": 0,
            "merged_indicators": 0
        }

    num_rows = len(table)
    num_cols = max(len(row) for row in table) if table else 0
    cells_with_newlines = 0
    empty_cells = 0
    merged_indicators = 0

    for row in table:
        for cell in row:
            if cell is None or cell == '':
                empty_cells += 1
            elif isinstance(cell, str) and '\n' in cell:
                cells_with_newlines += 1
                # Count how many newlines (indicates multiple values merged)
                newline_count = cell.count('\n')
                if newline_count > 1:
                    merged_indicators += 1

    return {
        "num_rows": num_rows,
        "num_cols": num_cols,
        "cells_with_newlines": cells_with_newlines,
        "empty_cells": empty_cells,
        "merged_indicators": merged_indicators,
        "avg_cols_per_row": sum(len(row) for row in table) / num_rows if num_rows > 0 else 0
    }


def display_table_preview(table: List[List], max_rows: int = 5) -> str:
    """Create a preview of the table for display."""
    if not table:
        return "  [EMPTY TABLE]"

    lines = []
    for i, row in enumerate(table[:max_rows]):
        # Show first 3 columns with newline indicators
        preview_cols = []
        for j, cell in enumerate(row[:3]):
            if cell is None:
                preview_cols.append("[NULL]")
            elif cell == '':
                preview_cols.append("[EMPTY]")
            else:
                cell_str = str(cell)
                # Truncate and show newline count
                newline_count = cell_str.count('\n')
                if newline_count > 0:
                    truncated = cell_str.replace('\n', '↵')[:40]
                    preview_cols.append(f"{truncated}... [{newline_count}↵]")
                else:
                    preview_cols.append(cell_str[:40])

        lines.append(f"  Row {i}: {' | '.join(preview_cols)}")

    if len(table) > max_rows:
        lines.append(f"  ... ({len(table) - max_rows} more rows)")

    return '\n'.join(lines)


def experiment_on_pdf(pdf_path: Path, page_num: int = 0) -> Dict[str, Any]:
    """Run extraction experiments on a single PDF page."""
    print(f"\n{'='*80}")
    print(f"PDF: {pdf_path.name}")
    print(f"Page: {page_num + 1}")
    print(f"{'='*80}\n")

    results = {}

    with pdfplumber.open(pdf_path) as pdf:
        if page_num >= len(pdf.pages):
            print(f"ERROR: PDF only has {len(pdf.pages)} pages")
            return results

        page = pdf.pages[page_num]

        for strategy_key, strategy_info in STRATEGIES.items():
            print(f"\n{'-'*80}")
            print(f"Strategy: {strategy_info['name']}")
            print(f"Settings: {strategy_info['settings']}")
            print(f"{'-'*80}")

            try:
                # Extract tables with this strategy
                if strategy_info['settings']:
                    tables = page.extract_tables(table_settings=strategy_info['settings'])
                else:
                    tables = page.extract_tables()

                num_tables = len(tables) if tables else 0
                print(f"Number of tables detected: {num_tables}")

                if tables:
                    for idx, table in enumerate(tables):
                        print(f"\nTable {idx + 1}:")
                        analysis = analyze_table_structure(table)
                        print(f"  Rows: {analysis['num_rows']}, Cols: {analysis['num_cols']}")
                        print(f"  Cells with newlines: {analysis['cells_with_newlines']}")
                        print(f"  Empty cells: {analysis['empty_cells']}")
                        print(f"  Merged indicators (>1 newline): {analysis['merged_indicators']}")
                        print(f"  Avg cols/row: {analysis['avg_cols_per_row']:.1f}")

                        print(f"\nPreview:")
                        print(display_table_preview(table))

                        # Store results
                        if strategy_key not in results:
                            results[strategy_key] = {
                                "name": strategy_info['name'],
                                "tables": []
                            }
                        results[strategy_key]["tables"].append({
                            "analysis": analysis,
                            "raw_data": table
                        })
                else:
                    print("  No tables found!")
                    results[strategy_key] = {
                        "name": strategy_info['name'],
                        "tables": []
                    }

            except Exception as e:
                print(f"  ERROR: {e}")
                results[strategy_key] = {
                    "name": strategy_info['name'],
                    "error": str(e)
                }

    return results


def compare_strategies(results: Dict[str, Any]) -> None:
    """Print a comparison table of all strategies."""
    print(f"\n{'='*80}")
    print("STRATEGY COMPARISON SUMMARY")
    print(f"{'='*80}\n")

    print(f"{'Strategy':<30} {'Tables':<8} {'Rows':<8} {'NewLines':<10} {'Merged':<8}")
    print(f"{'-'*70}")

    for strategy_key, result in results.items():
        if "error" in result:
            print(f"{result['name']:<30} ERROR: {result['error']}")
            continue

        num_tables = len(result.get("tables", []))
        if num_tables == 0:
            print(f"{result['name']:<30} {'0':<8} {'-':<8} {'-':<10} {'-':<8}")
            continue

        # Aggregate stats across all tables
        total_rows = sum(t["analysis"]["num_rows"] for t in result["tables"])
        total_newlines = sum(t["analysis"]["cells_with_newlines"] for t in result["tables"])
        total_merged = sum(t["analysis"]["merged_indicators"] for t in result["tables"])

        print(f"{result['name']:<30} {num_tables:<8} {total_rows:<8} {total_newlines:<10} {total_merged:<8}")

    print("\nKEY INSIGHTS:")
    print("- Lower 'NewLines' = better cell separation (fewer merged cells)")
    print("- Lower 'Merged' = fewer cells with multiple values")
    print("- Compare 'Rows' to see if any strategy is missing data")


def save_detailed_results(pdf_path: Path, page_num: int, results: Dict[str, Any]) -> None:
    """Save detailed results to a JSON file for further analysis."""
    output_dir = Path("experiment_results")
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"{pdf_path.stem}_page{page_num + 1}_{timestamp}.json"

    # Convert to JSON-serializable format
    json_results = {}
    for strategy_key, result in results.items():
        json_results[strategy_key] = {
            "name": result["name"],
            "tables": [
                {
                    "analysis": t["analysis"],
                    # Store raw data for manual inspection if needed
                }
                for t in result.get("tables", [])
            ] if "tables" in result else [],
            "error": result.get("error")
        }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(json_results, f, indent=2, ensure_ascii=False)

    print(f"\nDetailed results saved to: {output_file}")


def main():
    """Main experiment runner."""
    print("="*80)
    print("PDF TABLE EXTRACTION EXPERIMENT")
    print("="*80)
    print("\nThis script will test different extraction strategies on your PDFs")
    print("to help identify the best settings for your liquidation documents.\n")

    # Find all PDFs
    pdf_files = list(Path(".").glob("*.PDF"))

    if not pdf_files:
        print("No PDF files found in current directory!")
        return

    print(f"Found {len(pdf_files)} PDF files:")
    for i, pdf in enumerate(pdf_files, 1):
        print(f"  {i}. {pdf.name}")

    # Ask which PDF to test
    print("\nSelect a PDF to experiment with (enter number, or 'all' for all PDFs):")
    selection = input("> ").strip()

    if selection.lower() == 'all':
        selected_pdfs = pdf_files
    else:
        try:
            idx = int(selection) - 1
            if 0 <= idx < len(pdf_files):
                selected_pdfs = [pdf_files[idx]]
            else:
                print("Invalid selection!")
                return
        except ValueError:
            print("Invalid input!")
            return

    # Ask which page to test
    print("\nWhich page to test? (1 for first page, default=1):")
    page_input = input("> ").strip()
    page_num = int(page_input) - 1 if page_input else 0

    # Run experiments
    for pdf_path in selected_pdfs:
        results = experiment_on_pdf(pdf_path, page_num)
        compare_strategies(results)
        save_detailed_results(pdf_path, page_num, results)

    print("\n" + "="*80)
    print("EXPERIMENT COMPLETE")
    print("="*80)
    print("\nNext steps:")
    print("1. Review the comparison table above")
    print("2. Check which strategy has the cleanest extraction")
    print("3. Look for strategies with fewer newlines and merged cells")
    print("4. Test the promising strategies on other pages/PDFs")
    print("5. Integrate the best settings into your extractor")


if __name__ == "__main__":
    main()

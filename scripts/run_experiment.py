"""
Non-interactive table extraction experiment runner.
Tests all PDFs on page 1 automatically.
"""
from experiment_table_extraction import experiment_on_pdf, compare_strategies, save_detailed_results
from pathlib import Path

def main():
    print("="*80)
    print("PDF TABLE EXTRACTION EXPERIMENT - AUTO MODE")
    print("="*80)

    # Find all PDFs
    pdf_files = sorted(Path(".").glob("*.PDF"))

    if not pdf_files:
        print("No PDF files found!")
        return

    print(f"\nTesting {len(pdf_files)} PDFs on page 1:\n")

    for pdf_path in pdf_files:
        results = experiment_on_pdf(pdf_path, page_num=0)  # Test first page
        compare_strategies(results)
        save_detailed_results(pdf_path, 0, results)

    print("\n" + "="*80)
    print("EXPERIMENT COMPLETE!")
    print("="*80)
    print("\nResults saved to experiment_results/ directory")
    print("\nRECOMMENDATIONS:")
    print("1. Look for the strategy with LOWEST 'NewLines' count")
    print("2. Verify that 'Rows' count matches expected records")
    print("3. Test the best strategy on page 2 to confirm consistency")

if __name__ == "__main__":
    main()

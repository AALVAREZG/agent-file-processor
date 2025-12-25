"""
ENSEMBLE EXTRACTION EXPERIMENT

Tests multiple extraction libraries and compares results.
Uses consensus to improve accuracy for critical accounting data.
"""
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json

# Import multiple extraction libraries
try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except:
    HAS_PDFPLUMBER = False

try:
    import camelot
    HAS_CAMELOT = True
except:
    HAS_CAMELOT = False

try:
    import tabula
    HAS_TABULA = True
except:
    HAS_TABULA = False

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except:
    HAS_PYMUPDF = False


@dataclass
class ExtractionResult:
    """Result from one extraction library."""
    library: str
    success: bool
    tables: List[List[List[str]]]
    num_tables: int
    num_rows: int
    error: Optional[str] = None


class EnsembleExtractor:
    """Extracts tables using multiple libraries and finds consensus."""

    def __init__(self, pdf_path: Path):
        self.pdf_path = pdf_path
        self.results = []

    def extract_with_pdfplumber(self) -> ExtractionResult:
        """Extract using pdfplumber."""
        if not HAS_PDFPLUMBER:
            return ExtractionResult("pdfplumber", False, [], 0, 0, "Not installed")

        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                page = pdf.pages[0]
                tables = page.extract_tables()

                if tables:
                    return ExtractionResult(
                        library="pdfplumber",
                        success=True,
                        tables=tables,
                        num_tables=len(tables),
                        num_rows=sum(len(t) for t in tables)
                    )
                else:
                    return ExtractionResult("pdfplumber", False, [], 0, 0, "No tables found")

        except Exception as e:
            return ExtractionResult("pdfplumber", False, [], 0, 0, str(e))

    def extract_with_camelot(self) -> ExtractionResult:
        """Extract using Camelot (best for bordered tables)."""
        if not HAS_CAMELOT:
            return ExtractionResult("camelot", False, [], 0, 0, "Not installed")

        try:
            # Camelot has two flavors: 'lattice' (bordered) and 'stream' (borderless)
            tables = camelot.read_pdf(str(self.pdf_path), pages='1', flavor='lattice')

            if len(tables) == 0:
                # Try stream flavor if lattice fails
                tables = camelot.read_pdf(str(self.pdf_path), pages='1', flavor='stream')

            if len(tables) > 0:
                # Convert Camelot tables to list format
                table_data = [table.df.values.tolist() for table in tables]

                return ExtractionResult(
                    library="camelot",
                    success=True,
                    tables=table_data,
                    num_tables=len(tables),
                    num_rows=sum(len(t) for t in table_data)
                )
            else:
                return ExtractionResult("camelot", False, [], 0, 0, "No tables found")

        except Exception as e:
            return ExtractionResult("camelot", False, [], 0, 0, str(e))

    def extract_with_tabula(self) -> ExtractionResult:
        """Extract using Tabula (Java-based)."""
        if not HAS_TABULA:
            return ExtractionResult("tabula", False, [], 0, 0, "Not installed")

        try:
            # Tabula returns DataFrames
            dfs = tabula.read_pdf(str(self.pdf_path), pages='1', multiple_tables=True)

            if dfs:
                # Convert to list format
                table_data = [df.values.tolist() for df in dfs]

                return ExtractionResult(
                    library="tabula",
                    success=True,
                    tables=table_data,
                    num_tables=len(dfs),
                    num_rows=sum(len(t) for t in table_data)
                )
            else:
                return ExtractionResult("tabula", False, [], 0, 0, "No tables found")

        except Exception as e:
            return ExtractionResult("tabula", False, [], 0, 0, str(e))

    def extract_all(self) -> List[ExtractionResult]:
        """Run all available extractors."""
        print(f"\n{'='*80}")
        print(f"ENSEMBLE EXTRACTION: {self.pdf_path.name}")
        print(f"{'='*80}\n")

        extractors = [
            ("pdfplumber", self.extract_with_pdfplumber),
            ("camelot", self.extract_with_camelot),
            ("tabula", self.extract_with_tabula),
        ]

        results = []

        for name, extractor in extractors:
            print(f"Running {name}...")
            result = extractor()
            results.append(result)

            if result.success:
                print(f"  [OK] Success: {result.num_tables} tables, {result.num_rows} rows")
            else:
                print(f"  [FAIL] Failed: {result.error}")

        self.results = results
        return results

    def analyze_consensus(self):
        """Analyze agreement between extractors."""
        print(f"\n{'='*80}")
        print("CONSENSUS ANALYSIS")
        print(f"{'='*80}\n")

        successful = [r for r in self.results if r.success]

        if not successful:
            print("No successful extractions to compare!")
            return

        print(f"Successful extractors: {len(successful)}/{len(self.results)}")
        print()

        # Compare table counts
        table_counts = {r.library: r.num_tables for r in successful}
        print("Table counts:")
        for lib, count in table_counts.items():
            print(f"  {lib}: {count}")

        # Compare row counts
        row_counts = {r.library: r.num_rows for r in successful}
        print("\nRow counts:")
        for lib, count in row_counts.items():
            print(f"  {lib}: {count}")

        # Check if they agree
        if len(set(row_counts.values())) == 1:
            print("\n[CONSENSUS] All extractors agree on row count!")
        else:
            print("\n[WARNING] DISAGREEMENT: Extractors found different row counts")
            print("  -> Need to investigate which is correct")

        # Compare first data row (if available)
        print(f"\n{'='*80}")
        print("FIRST DATA ROW COMPARISON")
        print(f"{'='*80}\n")

        for result in successful:
            if result.tables and len(result.tables[0]) > 1:
                first_row = result.tables[0][1][:3]  # First 3 cells of first data row
                print(f"{result.library}:")
                print(f"  {first_row}")

    def get_best_result(self) -> Optional[ExtractionResult]:
        """
        Select the best extraction result based on heuristics.

        Strategy:
        1. Prefer results with most rows (likely more complete)
        2. Prefer pdfplumber if counts are close (it's what we know)
        3. Use consensus if 2+ agree
        """
        successful = [r for r in self.results if r.success]

        if not successful:
            return None

        if len(successful) == 1:
            return successful[0]

        # Check for consensus on row count
        row_counts = {}
        for r in successful:
            count = r.num_rows
            if count not in row_counts:
                row_counts[count] = []
            row_counts[count].append(r)

        # If 2+ agree on same count, use consensus
        for count, results in row_counts.items():
            if len(results) >= 2:
                # Among consensus, prefer pdfplumber
                pdfplumber_result = next((r for r in results if r.library == "pdfplumber"), None)
                if pdfplumber_result:
                    return pdfplumber_result
                return results[0]

        # No consensus - return result with most rows
        return max(successful, key=lambda r: r.num_rows)


def main():
    """Run ensemble extraction experiment."""
    pdf_files = sorted(Path(".").glob("*.PDF"))

    if not pdf_files:
        print("No PDFs found!")
        return

    print("Available libraries:")
    print(f"  pdfplumber: {'OK' if HAS_PDFPLUMBER else 'NOT INSTALLED (pip install pdfplumber)'}")
    print(f"  camelot:    {'OK' if HAS_CAMELOT else 'NOT INSTALLED (pip install camelot-py[cv])'}")
    print(f"  tabula:     {'OK' if HAS_TABULA else 'NOT INSTALLED (pip install tabula-py)'}")
    print(f"  PyMuPDF:    {'OK' if HAS_PYMUPDF else 'NOT INSTALLED (pip install PyMuPDF)'}")

    if not any([HAS_PDFPLUMBER, HAS_CAMELOT, HAS_TABULA]):
        print("\nNeed at least 2 libraries to run ensemble!")
        return

    # Test first PDF
    print(f"\nTesting first PDF: {pdf_files[0].name}")

    extractor = EnsembleExtractor(pdf_files[0])
    results = extractor.extract_all()
    extractor.analyze_consensus()

    best = extractor.get_best_result()
    if best:
        print(f"\n{'='*80}")
        print(f"RECOMMENDED RESULT: {best.library}")
        print(f"  Tables: {best.num_tables}, Rows: {best.num_rows}")
        print(f"{'='*80}")


if __name__ == "__main__":
    main()

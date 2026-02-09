from pathlib import Path

import pymupdf
from loguru import logger
from pymupdf import Document


def merge_pdf(files: list[Path], output: str | None = None) -> Path:
    """
    Merge multiple PDF files into one.

    Args:
        files: List of PDF file paths to merge (minimum 2)
        output: Output file path (optional). If None, saves as 'merged.pdf' in CWD

    Returns:
        Path to the merged PDF file

    Raises:
        ValueError: If less than 2 files provided
        FileNotFoundError: If any input file doesn't exist
        RuntimeError: If merging fails

    """
    MIN_PDF_FILES = 2
    if len(files) < MIN_PDF_FILES:
        error_msg: str = "At least two PDF files are required"
        raise ValueError(error_msg)

    for file in files:
        if not file.exists():
            file_not_found_msg: str = f"PDF file not found: {file}"
            raise FileNotFoundError(file_not_found_msg)
        if not file.is_file():
            path_not_file_msg: str = f"Path is not a file: {file}"
            raise ValueError(path_not_file_msg)

    if output is None:
        output_path: Path = Path.cwd() / "merged.pdf"
    else:
        output_path = Path(output)

        if output_path.suffix.lower() != ".pdf":
            output_path = output_path.with_suffix(".pdf")

        if not output_path.is_absolute():
            output_path = Path.cwd() / output_path.name

    if output_path.exists():
        logger.warning(f"Output file already exists and will be overwritten: {output_path}")

    base_pdf: Document | None = None

    try:
        logger.info(f"Merging {len(files)} PDF files...")
        base_pdf = pymupdf.open(str(files[0]))

        for i, file in enumerate(files[1:], start=2):
            logger.debug(f"Merging file {i}/{len(files)}: {file.name}")
            with pymupdf.open(str(file)) as doc:
                base_pdf.insert_pdf(doc)

        logger.info(f"Saving merged PDF to: {output_path}")
        base_pdf.save(str(output_path))

        logger.success(f"Successfully merged {len(files)} files into {output_path}")
    except Exception as e:
        logger.exception(f"Failed to merge PDF files: {e}")
        run_time_error_msg: str = f"PDF merge failed: {e}"
        raise RuntimeError(run_time_error_msg) from e
    else:
        return output_path
    finally:
        if base_pdf is not None:
            base_pdf.close()
            logger.info("Closed base pdf document")

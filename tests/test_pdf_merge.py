from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pymupdf
import pytest
from pymupdf import Document, Page
from typer.testing import CliRunner, Result

from src.commands.merge import app
from src.services.pdf_merge import merge_pdf

runner = CliRunner()


@pytest.fixture
def sample_pdfs(tmp_path) -> list[Path]:
    pdf_paths: list[Path] = []

    for i in range(2):
        pdf_file = tmp_path / f"sample_{i + 1}.pdf"

        doc: Document = pymupdf.open()
        page: Page = doc.new_page()

        page.insert_text((72, 72), f"Sample PDF {i + 1}", fontsize=12)

        doc.save(str(pdf_file))
        doc.close()
        pdf_paths.append(pdf_file)

    return pdf_paths


def get_pdf_page_count(pdf_file: Path) -> int:
    with pymupdf.open(str(pdf_file)) as doc:
        return len(doc)


def creating_valid_pdf_file(tmp_path) -> Path:
    valid_pdf: Path = tmp_path / "valid.pdf"
    doc: Document = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Valid PDF", fontsize=12)
    doc.save(str(valid_pdf))
    doc.close()
    return valid_pdf


def test_merge_cli(sample_pdfs, tmp_path) -> None:
    output_file: Path = tmp_path / "merged.pdf"
    result: Result = runner.invoke(
        app, [str(sample_pdfs[0]), str(sample_pdfs[1]), "--output", str(output_file)]
    )
    assert result.exit_code == 0, f"Expected exit code = 0, got: {result.exit_code}"
    assert output_file.exists()
    assert str(output_file) in result.stdout


def test_merge_less_than_two_files(sample_pdfs) -> None:
    file = sample_pdfs[0:1]
    with pytest.raises(ValueError, match="At least two PDF files are required"):
        merge_pdf(file)


def test_merge_two_valid_pdfs_without_output(sample_pdfs) -> None:
    files: list[Path] = sample_pdfs
    result: Path = merge_pdf(files)

    assert isinstance(result, Path), "Result is not an instance of Path"
    assert result.name == "merged.pdf", "Created file is not called merged.pdf"
    assert result.parent == Path.cwd(), "Parent path is not correct"
    assert result.exists(), "File does not exist"
    assert result.stat().st_size > 0, "Size of a file is equal 0"
    assert get_pdf_page_count(result) == 2, (
        f"Expected 2 pages, get {get_pdf_page_count(result)}"
    )

    with pymupdf.open(result) as doc:
        for i, page in enumerate(doc.pages()):
            expected_text: str = f"Sample PDF {i + 1}"
            actual_text: str = page.get_text().strip()

            assert expected_text in actual_text, (
                f"Expected text: {expected_text}, got {actual_text}"
            )


def test_merge_two_valid_pdfs_with_output(sample_pdfs) -> None:
    files: list[Path] = sample_pdfs
    result_without_pdf_ext: Path = merge_pdf(files, "output")
    assert result_without_pdf_ext.name == "output.pdf", (
        f"Expected output.pdf, got {result_without_pdf_ext.name}"
    )

    result_with_not_pdf_ext: Path = merge_pdf(files, "output.exe")
    assert result_with_not_pdf_ext.name == "output.pdf", (
        f"Expected output.pdf, got {result_with_not_pdf_ext.name}"
    )


def test_file_not_found(tmp_path, sample_pdfs: list[Path]) -> None:
    files: list[Path] = sample_pdfs.copy()
    not_existing_file: Path = tmp_path / "not_exists.pdf"
    files.append(not_existing_file)

    with pytest.raises(
        FileNotFoundError, match=f"PDF file not found: {not_existing_file}"
    ):
        merge_pdf(files)


def test_file_is_not_a_file(tmp_path, sample_pdfs: list[Path]) -> None:
    files: list[Path] = sample_pdfs.copy()
    dir_path: Path = tmp_path / "not_a_file"
    dir_path.mkdir()
    files.append(dir_path)

    with pytest.raises(ValueError, match=f"Path is not a file: {dir_path}"):
        merge_pdf(files)


def test_merge_pdf_invalid_file_raises_runtime_error(tmp_path) -> None:
    files: list[Path] = []
    invalid_pdf: Path = tmp_path / "invalid.pdf"
    invalid_pdf.write_text("This is not a valid PDF file")
    files.append(invalid_pdf)

    valid_pdf: Path = creating_valid_pdf_file(tmp_path)
    files.append(valid_pdf)

    with pytest.raises(RuntimeError, match="PDF merge failed"):
        merge_pdf(files)


def test_merge_pdf_corrupted_file_raises_runtime_error(tmp_path) -> None:
    files: list[Path]
    corrupted_pdf: Path = tmp_path / "corrupted.pdf"
    corrupted_pdf.write_bytes(b"%PDF-1.4\n" + b"garbage_data" * 100)

    valid_pdf: Path = creating_valid_pdf_file(tmp_path)

    files = [corrupted_pdf, valid_pdf]

    with pytest.raises(RuntimeError, match="PDF merge failed"):
        merge_pdf(files)


@patch("src.services.pdf_merge.pymupdf.open")
def test_document_close_called(mock_open: Mock, sample_pdfs) -> None:
    mock_base_pdf = MagicMock()
    mock_doc = MagicMock()

    mock_open.side_effect = [mock_base_pdf, mock_doc]

    merge_pdf(sample_pdfs)
    mock_base_pdf.close.assert_called_once()


@patch("src.services.pdf_merge.pymupdf.open")
def test_document_close_called_with_error(mock_open: Mock, sample_pdfs) -> None:
    mock_base_pdf = MagicMock()

    mock_open.side_effect = [mock_base_pdf, RuntimeError("PDF merge failed")]

    with pytest.raises(RuntimeError, match="PDF merge failed"):
        merge_pdf(sample_pdfs)
    mock_base_pdf.close.assert_called_once()

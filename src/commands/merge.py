from pathlib import Path
from typing import Annotated

import typer
from rich import print

from services.pdf_merge import merge_pdf

app = typer.Typer()


@app.command()
def merge(
    files: Annotated[
        list[Path],
        typer.Argument(readable=True, help="PDF files to merge (order matters)"),
    ],
    output: Annotated[
        str | None,
        typer.Option("-o", "--output", help="Output PDF file (default: ./merged.pdf)"),
    ] = None,
) -> None:
    output_path: Path = merge_pdf(files, output)
    print(output_path)

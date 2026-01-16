import typer

from commands.merge import app as merge_app


app = typer.Typer()

app.add_typer(merge_app)

import typer

from commands.merge import app as merge_app
from commands.split import app as split_app


app = typer.Typer()

app.add_typer(merge_app)
app.add_typer(split_app)

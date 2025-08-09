# Professional CLI with minimal boilerplate
import click


@click.group()
@click.option("--verbose", is_flag=True)
@click.pass_context
def cli(ctx: click.Context, verbose: bool) -> None:
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose


@cli.command()
@click.argument("task")
def hack(task: str) -> None:
    """AI-assisted code modification"""
    pass

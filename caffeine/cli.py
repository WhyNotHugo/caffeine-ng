import ctypes
import logging
import signal

import click
from setproctitle import setproctitle

from caffeine.applicationinstance import ApplicationInstance
from caffeine.main import GUI

logger = logging.getLogger(__name__)


@click.group(invoke_without_command=True)
@click.version_option(prog_name="caffeine")
@click.option("--verbose", "-v", is_flag=True)
@click.pass_context
def cli(ctx, verbose):
    setproctitle("caffeine-ng")
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    # register the process id as 'caffeine'
    libc = ctypes.cdll.LoadLibrary("libc.so.6")
    libc.prctl(15, "caffeine", 0, 0, 0)

    if verbose:
        logging.basicConfig(level=logging.DEBUG)
        logger.debug("Running with --verbose.")

    ctx.obj = ApplicationInstance("caffeine-ng")

    if not ctx.invoked_subcommand:
        ctx.invoke(cli.commands["start"])


@cli.command()
@click.option(
    "--activate",
    "-a",
    is_flag=True,
    help="Immediately disable power management and screen saving.",
)
@click.option(
    "--deactivate",
    "-d",
    is_flag=True,
    help="Immediately re-enable power management and screen saving.",
)
@click.option(
    "--kill",
    "-k",
    is_flag=True,
    help="Kill any running instance of caffeine.",
)
@click.option(
    "--time",
    "-t",
    # XXX: There's a param issing to make this take values.
    help="Use with -a. Activate caffeine for HH:MM.",
    metavar="HH:MM",
)
@click.option(
    "--preferences",
    "-p",
    is_flag=True,
    help="Start with the Preferences dialog open.",
)
@click.option(
    "--pulseaudio/--no-pulseaudio",
    default=True,
    help=(
        "Inhibit when pulseaudio is in use. "
        "Only the screensaver (i.e.: not suspension) is inhibited when audio is playing."
    ),
)
@click.option(
    "--whitelist/--no-whitelist",
    default=True,
    help="Inhibit based on whitelisted applications.",
)
@click.option(
    "--fullscreen/--no-fullscreen",
    default=True,
    help="Inhibit when a fullscreen application is detected.",
)
@click.pass_obj
def start(
    app: ApplicationInstance,
    activate: bool,
    deactivate: bool,
    kill: bool,
    time: str,
    preferences: bool,
    pulseaudio: bool,
    whitelist: bool,
    fullscreen: bool,
):
    """Start caffeine."""
    if kill:
        app.kill()
    elif app.is_running():
        raise click.ClickException("Caffeine is already running.")

    main = GUI(
        show_preferences=preferences,
        pulseaudio=pulseaudio,
        whitelist=whitelist,
        fullscreen=fullscreen,
    )
    if activate:
        main.setActive(True)

    if activate and time:
        parts = time.split(":")
        if len(parts) != 2:
            raise click.ClickException("-t argument must be in the hour:minute format.")

        try:
            hours = int(parts[0])
            minutes = int(parts[1])
        except ValueError:
            raise click.ClickException("Invalid time argument.")

        main.timed_activation((hours * 3600.0) + (minutes * 60.0))

    if preferences:
        main.window.show_all()

    with app.pid_file():
        main.run()


@cli.command()
@click.pass_obj
def kill(app: ApplicationInstance):
    """Kill any running instances of caffeine and exit."""
    if app.is_running():
        app.kill()
    else:
        raise click.ClickException("Caffeine is not running.")


if __name__ == "__main__":
    cli()

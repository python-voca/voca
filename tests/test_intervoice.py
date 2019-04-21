from click.testing import CliRunner

from intervoice import cli


def test_main():
    runner = CliRunner()
    result = runner.invoke(cli.cli, [])

    assert result.output.startswith("Usage")
    assert result.exit_code == 0

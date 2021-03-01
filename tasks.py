import os
import re

import invoke
from invoke import task


def oneline_command(string):
    return re.sub("\\s+", " ", string).strip()


def run_invoke_cmd(context, cmd):
    return context.run(cmd, env=None, hide=False, warn=False, pty=False, echo=True)


@task
def clean(context):
    find_command = oneline_command(
        """
        find
            .
            -type f \\(
                -name '*.script'
            \\)
            -or -type d \\(
                -name '*.dSYM' -or
                -name 'Sandbox' -or
                -name 'Output' -or
                -name 'output'
            \\)
            -not -path "**Expected**"
            -not -path "**Input**"
        """
    )

    find_result = run_invoke_cmd(context, find_command)
    find_result_stdout = find_result.stdout.strip()
    echo_command = oneline_command(
        """echo {find_result} | xargs rm -rfv""".format(find_result=find_result_stdout)
    )

    run_invoke_cmd(context, echo_command)


@task
def sphinx(context):
    cwd = os.getcwd()
    run_invoke_cmd(
        context,
        oneline_command(
            f"""
            cd docs &&
                SPHINXOPTS="-W --keep-going -n" make html latexpdf &&
                cp build/latex/sphinx-latex-reqspec-template.pdf {cwd}/Template.pdf &&
                open build/latex/sphinx-latex-reqspec-template.pdf
            """
        ),
    )


@task
def test_unit(context):
    command = oneline_command(
        """
        pytest --capture=no
        """
    )

    run_invoke_cmd(context, command)


@task
def export_pip_requirements(context):
    run_invoke_cmd(context, "poetry export -f requirements.txt > requirements.txt")


@task
def lint_black_diff(context):
    command = oneline_command(
        """
        black . --color 2>&1
        """
    )
    result = run_invoke_cmd(context, command)

    # black always exits with 0, so we handle the output.
    if "reformatted" in result.stdout:
        print("invoke: black found issues")
        result.exited = 1
        raise invoke.exceptions.UnexpectedExit(result)


@task
def lint_pylint(context):
    command = oneline_command(
        """
        pylint --rcfile=.pylint.ini docs/ tasks.py
        """
    )
    try:
        run_invoke_cmd(context, command)
    except invoke.exceptions.UnexpectedExit as exc:
        # pylink doesn't show an error message when exit code != 0, so we do.
        print("invoke: pylint exited with error code {}".format(exc.result.exited))
        raise exc


@task(lint_pylint, lint_black_diff)
def lint(_):
    pass


@task(lint)
def test(_):
    pass

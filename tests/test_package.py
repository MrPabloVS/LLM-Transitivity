"""Check package boundaries without importing the evaluation framework."""

import subprocess
import sys


def test_domain_imports_have_no_framework_or_network_dependencies():
    subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import llm_transitivity.domain.cases; "
                "import llm_transitivity.domain.config; "
                "import llm_transitivity.domain.selection; "
                "import llm_transitivity.domain.scoring; "
                "assert not {'inspect_ai', 'inspect_flow', 'requests', 'dotenv'} "
                "& sys.modules.keys()"
            ),
        ],
        check=True,
    )

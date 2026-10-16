"""MkDocs hooks."""

import shutil
from pathlib import Path


def on_post_build(config, **kwargs):
    """Publish skills/liminal/SKILL.md at <site>/assets/SKILL.md so it is same-origin
    and the `download` attribute on the docs link triggers a real download."""
    src = Path(config["docs_dir"]).parent / "skills" / "liminal" / "SKILL.md"
    dest = Path(config["site_dir"]) / "assets" / "SKILL.md"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dest)

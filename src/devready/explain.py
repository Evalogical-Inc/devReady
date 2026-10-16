"""Static, beginner-friendly explanations per check id (used by `devready explain`)."""

EXPLANATIONS = {
    "python.version": "The Python interpreter running DevReady; not necessarily your project's virtualenv.",
    "git.version": "Git is needed to clone, branch and commit. Install: https://git-scm.com/downloads",
    "node.version": "Node.js runs JavaScript tooling. Many projects pin a version; see project.node.* checks.",
    "npm.version": "npm installs JavaScript dependencies and ships with Node.js.",
    "project.node.pin": "A .nvmrc/.node-version file says which Node the team uses. A mismatch is a warning; switch with nvm, fnm or mise.",
    "project.node.engines": "package.json engines.node is a hard requirement. A mismatch fails the check and npm may refuse to install.",
    "project.node.tool_versions": ".tool-versions (asdf/mise) pins Node for this project.",
    "project.python.pin": ".python-version (pyenv/uv) pins Python for this project.",
    "project.python.requires": "pyproject.toml requires-python is a hard requirement; pip refuses incompatible versions.",
    "project.python.tool_versions": ".tool-versions (asdf/mise) pins Python for this project.",
    "project.env.keys": "Compares variable NAMES in .env.example with .env. Values are never read or shown.",
    "docker.cli": "Shown only when the project has a Dockerfile or compose file and the docker command is missing.",
    "docker.daemon": "The Docker CLI can exist while the daemon is stopped. Start Docker Desktop or the service.",
    "git.identity": "Commits need user.name and user.email. DevReady checks they exist, never what they are.",
    "disk.space": "Warns below 1 GB free where the project lives; installs and builds can fail when the disk is full.",
}

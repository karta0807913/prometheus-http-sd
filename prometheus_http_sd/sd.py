import os
import json
import logging
import importlib
from typing import List
from .consts import TARGETS_DIR_ENV_NAME
from .targets import TargetList

logger = logging.getLogger(__name__)


def run_python(generator_path) -> TargetList:
    module = importlib.import_module(generator_path)
    return module.generate_targets()


def get_generator_list(path: str = "") -> List[str]:
    """
    generate targets start from ``path``
    if ``path`` is None or empty, then start from the root path
    ``TARGETS_DIR_ENV_NAME ``
    """
    start_path = os.environ[TARGETS_DIR_ENV_NAME]
    if path:
        start_path = os.path.join(start_path, path)

    generators = []

    for root, _, files in os.walk(start_path):
        for file in files:
            full_path = os.path.join(root, file)

            should_ignore = any(
                p.startswith("_") for p in os.path.normpath(full_path).split(os.sep)
            )
            if should_ignore:
                continue

            generators.append(full_path)

    return generators


def generate(path: str = "") -> TargetList:
    generators = get_generator_list(path)
    all_targets = []
    for generator in generators:
        target_list = run_generator(generator)
        all_targets.extend(target_list)

    return all_targets


def run_generator(generator_path: str) -> TargetList:
    if generator_path.endswith(".json"):
        with open(generator_path) as jsonf:
            return json.load(jsonf)
    elif generator_path.endswith(".py"):
        return run_python(generator_path)
    else:
        raise Exception("Unknow Type!")


if __name__ == "__main__":
    generate("")
    generate("spex")

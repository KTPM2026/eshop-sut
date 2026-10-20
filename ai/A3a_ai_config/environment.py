"""Load a selected dotenv file as data; never execute shell instructions."""

from dotenv import load_dotenv


def load_environment(path):
    if not path.is_file():
        raise ValueError("Environment file does not exist")
    # A selected file defines this run, independently of stale shell values.
    load_dotenv(path, override=True, interpolate=False, encoding="utf-8-sig")

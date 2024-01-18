pytest_plugins = "pytester"

def pytest_addoption(parser):
    """Optional user specified data dir paths"""
    parser.addini("datadir", "my custom datadir for pytest-regressions")
    parser.addini("original_datadir", "my custom original_datadir for pytest-regressions")
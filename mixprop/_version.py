__all__ = ['__version__']

# major, minor, patch
version_info = 0, 0, 3

# suffix
suffix = None

# version string
__version__ = '.'.join(map(str, version_info)) + (f'.{suffix}' if suffix else '')

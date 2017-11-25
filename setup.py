import os
import re

import setuptools

here = os.path.abspath(os.path.dirname(__file__))


def get_meta() -> str:
    with open(os.path.join(here, 'miyabi/__init__.py')) as f:
        source = f.read()

    regex = r"^{}\s*=\s*['\"]([^'\"]*)['\"]"
    return lambda name: re.search(regex.format(name), source, re.MULTILINE).group(1)


get_meta = get_meta()
"""
with open(os.path.join(here, 'README.rst')) as f:
    README = f.read()
with open(os.path.join(here, 'CHANGES.rst')) as f:
    CHANGES = f.read()
"""
requires = [
    'pyramid',
    'pyyaml',
]

tests_require = [
    'pytest',
]

setuptools.setup(
    name='miyabi',
    version=get_meta('__version__'),
    description="",
    # long_description=README + "\n\n" + CHANGES,
    classifiers=[
        "Environment :: Web Environment",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3 :: Only",
        "License :: OSI Approved :: MIT License",
    ],
    author=get_meta('__author__'),
    author_email=get_meta('__email__'),
    url="",
    keywords="",
    packages=setuptools.find_packages(),
    extras_require={
        'testing': tests_require,
    },
    install_requires=requires,
    include_package_data=True,
    license="MIT License",
)

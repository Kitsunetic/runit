from setuptools import find_packages, setup

setup(
    name="runit",
    version="0.0.1",
    description="runit: scheduling multiple commands with limited devices",
    author="Kitsunetic",
    author_email="jh.shim.gg@gmail.com",
    packages=find_packages(),
    zip_safe=False,
    entry_points={
        "console_scripts": ["runit=runit.runit:main"],
    },
)

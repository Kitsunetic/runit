from setuptools import find_packages, setup


with open("README.md", encoding="utf-8") as f:
    desc = f.read()


setup(
    name="runit-parallel",
    version="0.0.3",
    description="runit: scheduling multiple commands with limited devices",
    author="Kitsunetic",
    author_email="jh.shim.gg@gmail.com",
    packages=find_packages(),
    zip_safe=False,
    entry_points={
        "console_scripts": ["runit=runit.runit:main"],
    },
    long_description=desc,
    long_description_content_type="text/markdown",
)

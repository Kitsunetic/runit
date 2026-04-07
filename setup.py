from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="runit-parallel",
    version="0.1.0",
    description="A simple command-line tool for scheduling multiple commands with limited resources.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Kitsunetic",
    author_email="jh.shim.gg@gmail.com",
    url="https://github.com/Kitsunetic/runit",
    packages=find_packages(),
    zip_safe=False,
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "runit=runit.runit:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Topic :: Utilities",
    ],
)

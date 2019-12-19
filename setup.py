import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="vcpy",
    version="0.0.1",
    author="Fausto Woelflin",
    author_email="fausto@dock.io",
    description="Issue verifiable credentials with ease.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords='verifiable credentials blockcerts issuing blockchain certificates claims signed open badges',
    url="https://github.com/docknetwork/vcpy",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)

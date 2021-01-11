
import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="sphinxcontrib-pharodomain", # Replace with your own username
    version="0.0.1",
    author="Massimo Nocentini",
    author_email="massimo.nocentini@gmail.com",
    description="A Sphinx domain for Pharo Smalltalk",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/massimo-nocentini/pharodomain",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
          'markdown',
      ],
    python_requires='>=3.9',
)

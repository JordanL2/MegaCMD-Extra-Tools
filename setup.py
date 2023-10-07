import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="megacmdextra",
    version="1.0.1",
    author="Jordan Leppert",
    author_email="jordanleppert@gmail.com",
    description="Extra tools for the Mega.nz megacmd toolset.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/JordanL2/MegaCMD-Extra-Tools",
    packages=setuptools.find_packages() + setuptools.find_namespace_packages(include=['megacmdextra.*']),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GPL-3.0 License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    entry_points = {'console_scripts': [
        'mega-sync-one-way=megacmdextra.megasynconeway:main',
        ], },
)

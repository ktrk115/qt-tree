import setuptools

setuptools.setup(
    name="qt-tree",
    version="0.1.0",
    author="Kotaro Kikuchi",
    author_email="ktrk115@gmail.com",
    description="Graphical user interface for editing and visualizing tree data structure",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/ktrk115/qt-tree",
    packages=setuptools.find_packages(),
    install_requires=['PySide2', 'anytree'],
    extras_require={'pillow': ['pillow']},
    keywords='Qt, tree structure, tree editor',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ]
)

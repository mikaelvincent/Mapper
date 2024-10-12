from setuptools import setup, find_packages

setup(
    name='Mapper',
    version='0.1.0',
    description='A command-line tool to generate a customizable representation of a project\'s directory and file structure.',
    author='mikaelvincent.dev',
    author_email='tumampos@mikaelvincent.dev',
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    install_requires=[
        'click>=8.0',
        'pathspec>=0.9.0'
    ],
    entry_points={
        'console_scripts': [
            'map=mapper.cli:main',
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)

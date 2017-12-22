import sys
from setuptools import setup, find_packages

if sys.version_info < (3, 6):
    sys.exit('Sorry, TECtool requires Python >= 3.6 (Tested with Python 3.6.2)')

requirements = [
    "htseq>=0.9.1",
    "pybedtools>=0.7.10",
    "bzip2",
    "pyfasta>=0.5.2",
    "scikit-learn>=0.19.0",
]

setup(
    name='TECtool',
    version='0.2',
    description="TECtool is a method that uses mRNA and 3’ end sequencing data to identify novel terminal exons.",
    author="Foivos Gypas",
    author_email='foivos.gypas@unibas.ch',
    url='https://git.scicore.unibas.ch/zavolan_public/TECtool.git',
    packages=['gene_structure', 'aln_analysis', 'annotation', 'machine_learning'],
    package_dir={'':'tectool'},
    scripts=['tectool/tectool.py'],
    install_requires=requirements,
    keywords='TECtool',
    classifiers=[
        'Programming Language :: Python :: 3.6',
    ]
)

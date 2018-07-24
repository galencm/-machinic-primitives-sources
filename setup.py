from setuptools import find_packages, setup
setup(
name="sourceprimitives",
    version="0.1",
    description="",
    author="Galen Curwen-McAdams",
    author_email='',
    platforms=["any"],
    license="Mozilla Public License 2.0 (MPL 2.0)",
    include_package_data=True,
    data_files = [("", ["LICENSE.txt"])],
    url="",
    packages=find_packages(),
    install_requires=['redis','logzero','zerorpc','python-consul','Pillow','lorem','roman'],
    entry_points = {'console_scripts': ['primitives-source-indexable = sourceprimitives.source_indexable:main',
                                        'primitives-source-simple = sourceprimitives.source:main',
                                        'primitives-generate-boook = sourceprimitives.boook_cli:main'
                                        ],
                            },
)

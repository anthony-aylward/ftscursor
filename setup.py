import setuptools

with open('README.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name='ftscursor',
    version='0.5.0',
    author='Anthony Aylward',
    author_email='aaylward@eng.ucsd.edu',
    description='A sqlite3 cursor with extra methods to support FTS3/4/5',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/anthony-aylward/ftscursor',
    packages=setuptools.find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    entry_points = {
        'console_scripts': ['ftscursor-example=ftscursor.example_script:main']
    }
)
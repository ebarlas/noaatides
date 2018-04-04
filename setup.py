from setuptools import setup

setup(
    name='noaatides',
    version='0.1',
    author='Elliot Barlas',
    author_email='elliotbarlas@gmail.com',
    description=('Python module to query NOAA tide predictions.'),
    license='MIT',
    url='https://github.com/ebarlas/noaatides',
    packages=['noaatides'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6'
    ],
    install_requires=['requests']
)

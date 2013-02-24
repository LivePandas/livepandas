from setuptools import setup

setup(
    name='livepandas',
    version="0.1.7",
    packages=['livepandas'],
    install_requires=[
        'requests',
        'decorator',
        'tornado',
    ],
    entry_points={
        'console_scripts': [
            'livepandas = livepandas.cli:main'
        ]
    },
    author="Jorge E. Cardona",
    author_email="jorge@cardona.co",
    description="Give a little life to your data.",
    license="PSF",
    url="http://www.livepandas.com/package",    
)

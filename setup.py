from setuptools import setup, find_packages


with open('README.md') as f:
    description = ''.join(l for l in f if not l.startswith('#')).strip()


setup(
    name='json2seq',
    version='0.0.1',
    author='trapwalker',
    author_email='svpmailbox@gmail.com',
    license='MIT',
    url='https://github.com/trapwalker/json2seq',
    install_requires=[
        "ijson",
    ],
    entry_points = {
        'console_scripts': 'json2seq = json2seq:main'
    },
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: MIT License",
        "Environment :: Console",
        "Topic :: Software Development :: Libraries",
        "Topic :: Text Processing :: Markup",
        "Topic :: Utilities",
    ],
    python_requires='>=3.6',
    packages=find_packages(),
    description=description,
    keywords=['converter', 'JSON', 'JSON-seq', 'RFC7464', 'tool'],
)

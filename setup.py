import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="io_shared",
    version="0.0.1",
    author="Ilya Belkin",
    author_email="ilya.belkin-trade@yandex.ru",
    description="Read/write safe IPC via shared memory",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ivbelkin/io_shared",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires='>=2.7',
    install_requires=["numpy", "posix_ipc"],
)

from setuptools import setup, find_packages


def readme():
    with open('README.md') as f:
        return f.read()


setup(
    name='uniflex_module_wifi_gnuradio',
    version='0.1.0',
    packages=find_packages(),
    url='https://github.com/uniflex',
    license='',
    author='Piotr Gawlowicz',
    author_email='gawlowicz@tu-berlin.de',
    description='UniFlex Module - GNU Radio',
    long_description='UniFlex Module - GNU Radio',
    keywords='wireless control',
    install_requires=[]
)

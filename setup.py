from glob import glob
from setuptools import find_packages, setup

package_name = 'insurance_survey_robot'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.launch.py')),
        ('share/' + package_name + '/worlds', glob('worlds/*.sdf')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    description='AI-assisted disaster survey robot for insurance loss inspection',
    entry_points={
        'console_scripts': ['patrol = insurance_survey_robot.patrol:main'],
    },
)

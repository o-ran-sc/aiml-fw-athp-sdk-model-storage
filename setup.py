# ==================================================================================
#
#       Copyright (c) 2022 Samsung Electronics Co., Ltd. All Rights Reserved.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#          http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ==================================================================================

from setuptools import setup, find_packages
import setuptools as setuptools
setup(
    name='modelmetricsdk',
    version='0.2',
    description='model store SDK for Training Host',
    url='',
    author='O-RAN Software Community',
    author_email='discuss@lists.o-ran-sc.org',
    license='Apache 2.0',
    packages=['modelmetricsdk'],
    package_data={"modelmetricsdk": ['config/config.json']},
    zip_safe=False,
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown'
)

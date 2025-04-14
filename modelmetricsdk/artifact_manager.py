# ==================================================================================
#
#       Copyright (c) 2025 Samsung Electronics Co., Ltd. All Rights Reserved.
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
from modelmetricsdk.storage_factory import StorageFactory
import logging

class ArtifactManager:
    """
    ArtifactManager class is responsible for managing datasets by uploading and downloading them
    from a specified storage service. Note: It will expand further to support different type of
    Artifacts.

    The class takes a storage configuration and a storage type (defaulting to 's3') to initialize
    the appropriate storage adapter.

    Attributes:
        storage (StorageAdapter): An instance of a storage adapter initialized based on the provided
                                  storage type and configuration.
    """

    def __init__(self, storage_config, storage_type='s3', logger=None):
        """
        Initialize the ArtifactManager with the given storage configuration and type.

        Args:
            storage_config (dict): A dictionary containing the configuration for the storage service.
            storage_type (str): The type of storage service to use (default is 's3').
            logger (logging.Logger): The logger instance to use.
        """
        self._logger = logger
        self._logger.info(f"init invoked with storage_type:{storage_type} config:{storage_config}")
        self.storage = StorageFactory.get_storage(storage_type, storage_config)

    @property
    def _logger(self):
        """
        Get the private logger instance.

        Returns:
            logging.Logger: The private logger instance.
        """
        return self.__logger

    @_logger.setter
    def _logger(self, value):
        """
        Set the private logger instance.

        Args:
            value (logging.Logger): The logger instance to set as the private logger.
        """
        if not isinstance(value, logging.Logger):
            raise ValueError("Logger instance must be of logging.Logger")
        self.__logger = value

    ## === Dataset API ===

    def upload_dataset(self, dataset_path: str, dataset_name: str):
        """
        Upload a dataset to the storage service.

        This method is currently not implemented and will raise a NotImplementedError if called.

        Args:
            dataset_path (str): The local file path of the dataset to upload.
            dataset_name (str): The name of the dataset in the storage service.
        """
        self._logger.debug(f'Upload request for {dataset_path} with dataset_name:{dataset_name}')
        try:
            self.storage.upload_artifact(dataset_path, 'mlpipeline', dataset_name)
            self._logger.debug(f'Uploaded dataset')
        except Exception as e:
            self._logger.debug(f'upload failed with error : {e}')
            raise

    def download_dataset(self, dataset_name, dest_path: str):
        """
        Download a dataset from the storage service to the specified destination path.

        Args:
            dataset_name (str): The name of the dataset in the storage service.
            dest_path (str): The local file path where the dataset should be downloaded.
        """
        self.storage.download_artifact('mlpipeline', dataset_name, dest_path)
        self._logger.debug(f"invoked download dataset")

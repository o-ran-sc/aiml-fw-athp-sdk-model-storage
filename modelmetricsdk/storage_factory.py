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
from modelmetricsdk.adapters.s3_adapter import S3Storage

class StorageFactory:
    """
    StorageFactory class is responsible for creating instances of storage adapters based on the provided
    storage type and configuration.

    This factory class currently supports creating instances of the S3Storage adapter for Amazon S3 storage.
    Additional storage types can be added by extending this class and implementing the appropriate logic.

    Attributes:
        None
    """

    @staticmethod
    def get_storage(storage_type: str, storage_config):
        """
        Get an instance of a storage adapter based on the provided storage type and configuration.

        Currently, this method only supports creating instances of the S3Storage adapter for Amazon S3 storage.
        Additional storage types can be supported by extending this method.

        Args:
            storage_type (str): The type of storage service to use. Currently, only 's3' is supported.
            storage_config (dict): A dictionary containing the configuration for the storage service.

        Returns:
            StorageAdapter: An instance of a storage adapter.

        Raises:
            ValueError: If an unsupported storage type is provided.
        """
        if storage_type == 's3':
            return S3Storage(storage_config)
        else:
            raise ValueError(f"Unsupported storage type: {storage_type}")
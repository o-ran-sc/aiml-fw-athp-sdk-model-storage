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
from abc import ABC, abstractmethod

class StorageAdapter(ABC):
    """
    Abstract class for storage operations.

    This class defines an interface for storage adapters to implement. It provides
    methods for downloading, uploading, and deleting artifacts from a storage
    service. Concrete implementations of this class should provide the specific
    logic for interacting with the storage service they are designed for.

    Attributes:
        None
    """

    @abstractmethod
    def download_artifact(self, bucket_name, key, download_path):
        """
        Download an artifact from the storage service.

        This method should be implemented by subclasses to download an artifact
        from the specified bucket and key to the local file system at the given
        download path.

        Args:
            bucket_name (str): The name of the bucket where the artifact is stored.
            key (str): The key (path) of the artifact within the bucket.
            download_path (str): The local file path where the artifact should be downloaded.

        Returns:
            None

        Raises:
            NotImplementedError: If the subclass does not implement this method.
        """
        pass

    @abstractmethod
    def upload_artifact(self, artifact_path, bucket_name, key):
        """
        Upload an artifact to the storage service.

        This method should be implemented by subclasses to upload a local file
        as an artifact to the specified bucket and key in the storage service.

        Args:
            artifact_path (str): The local file path of the artifact to upload.
            bucket_name (str): The name of the bucket where the artifact should be uploaded.
            key (str): The key (path) where the artifact should be stored within the bucket.

        Returns:
            None

        Raises:
            NotImplementedError: If the subclass does not implement this method.
        """
        pass

    @abstractmethod
    def delete_artifact(self, bucket_name, key):
        """
        Delete an artifact from the storage service.

        This method should be implemented by subclasses to delete an artifact
        from the specified bucket and key in the storage service.

        Args:
            bucket_name (str): The name of the bucket where the artifact is stored.
            key (str): The key (path) of the artifact within the bucket.

        Returns:
            None

        Raises:
            NotImplementedError: If the subclass does not implement this method.
        """
        pass

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
import boto3
import base64
from botocore.client import Config
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from kubernetes import client, config
from kubernetes.config.config_exception import ConfigException
from modelmetricsdk.adapters.base_adapter import StorageAdapter
from botocore.exceptions import ClientError
import logging
from modelmetricsdk.singleton_manager import SingletonManager
class S3Storage(StorageAdapter):
    """
    S3Storage class is a concrete implementation of the StorageAdapter interface for S3 storage.

    This class uses the boto3 library to interact with S3. It takes a configuration dictionary and an
    optional logger instance during initialization. If no logger is provided, it defaults to the logger from the
    SingletonManager.

    Attributes:
        _logger (logging.Logger): The private logger instance used for logging.
        client (boto3.client): The boto3 client instance used to interact with  S3.
    """

    def __init__(self, config, logger=None):
        """
        Initialize the S3Storage with the given configuration and an optional logger instance.

        Args:
            config (dict): A dictionary containing the configuration for S3.
            logger (logging.Logger, optional): The logger instance to use for logging. Defaults to None.
        """
        self._logger = logger
        self.client = boto3.client(
            "s3",
            endpoint_url=config["endpoint_url"],
            aws_access_key_id=config["aws_access_key_id"],
            aws_secret_access_key=self.__get_aws_key(config),
        )

    def __get_aws_key_from_secret(self):
        """
        Retrieve the AWS secret access key from Kubernetes secrets.

        Returns:
            str: The AWS secret access key.
        """
        config.load_incluster_config()
        v1 = client.CoreV1Api()
        sec = v1.read_namespaced_secret("leofs-secret", 'kubeflow').data
        aws_key = base64.b64decode(sec.get("password")).decode('utf-8')
        return aws_key

    def __get_aws_key_from_config(self, config):
        """
        Retrieve the AWS secret access key from the provided configuration.

        Args:
            config (dict): The configuration dictionary.

        Returns:
            str: The AWS secret access key.
        """
        self._logger.debug(f'config: {config}')
        return config["aws_secret_access_key"]

    def __get_aws_key(self, config):
        """
        Retrieve the AWS secret access key from either Kubernetes secrets or the provided configuration.

        Args:
            config (dict): The configuration dictionary.

        Returns:
            str: The AWS secret access key, or None if it could not be retrieved.
        """
        try:
            awskey = self.__get_aws_key_from_secret()
        except ConfigException as e:
            self._logger.error(f"not able to retrieve aws_secret key: {e}")
            try:
                awskey = self.__get_aws_key_from_config(config)
            except Exception as e:
                self._logger.error(f'not able to retrieve aws_secret_key using config: {e}')
                return None
        return awskey

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
        value = value or SingletonManager.get_instance().logger
        if not isinstance(value, logging.Logger):
            raise ValueError("Logger instance must be of logging.Logger")

        self.__logger = value

    def upload_artifact(self, artifact_path, bucket_name, key):
        """
        Upload an artifact to  S3.

        Args:
            artifact_path (str): The local file path of the artifact to upload.
            bucket_name (str): The name of the bucket where the artifact should be uploaded.
            key (str): The key (path) where the artifact should be stored within the bucket.
        """
        try:
            self._logger.debug(f'Uploading {artifact_path} to bucket:{bucket_name} with key:{key}')
            self.client.upload_file(artifact_path, bucket_name, key)
            self._logger.info(f'Successfully uploaded artifact: {artifact_path} to s3://{bucket_name}/{key}')
        except Exception as e:
            self._logger.error(f'Failed to upload {artifact_path} to s3://{bucket_name}/{key}')
            raise

    def delete_artifact(self, bucket_name, key):
        """
        Delete an artifact from  S3.

        Args:
            bucket_name (str): The name of the bucket where the artifact is stored.
            key (str): The key (path) of the artifact within the bucket.
        """
        # self.client.delete_object(Bucket=bucket_name, Key=key)
        raise NotImplementedError("delete_artifact is currently not supported by S3 adapter")

    def download_artifact(self, bucket_name, key, download_path):
        """
        Download an artifact from  S3 to the specified download path.

        Args:
            bucket_name (str): The name of the bucket where the artifact is stored.
            key (str): The key (path) of the artifact within the bucket.
            download_path (str): The local file path where the artifact should be downloaded.
        """
        self._logger.debug(f'download_artifact from bucket:{bucket_name} key:{key} to download path:{download_path}')
        try:
            self.client.download_file(bucket_name, key, download_path)
            self._logger.debug(f'Artifact is downloaded successfully at {download_path}')
        except Exception as error:
            self._logger.error(f'Artifact download error: {error}')
            raise
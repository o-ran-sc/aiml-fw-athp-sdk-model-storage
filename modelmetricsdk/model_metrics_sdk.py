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

"""
This module is used for working with object database.
"""
import json
import traceback
import os
import tempfile
import shutil
from io import BytesIO
import boto3
from botocore.client import Config
from modelmetricsdk.sdk_exception import SdkException
from modelmetricsdk.singleton_manager import SingletonManager
from kubernetes import client, config
import base64



class ModelMetricsSdk:
    """
    This class is used for working with object database.
    """
    def __init__(self):
        sm_object = SingletonManager.get_instance()
        self.logger = sm_object.logger
        self.config = sm_object.config["model_db_config"]
        self.client = boto3.client(
            "s3",
            endpoint_url = self.config["endpoint_url"],
            aws_access_key_id = self.config["aws_access_key_id"],
            aws_secret_access_key = self.get_aws_key(),
            config=Config(signature_version="s3v4"),
        )

    def get_aws_key(self):
        """
            This function would retrieve aws_secret_access_key from kubernetes secrets
        """
        config.load_incluster_config()
        v1 = client.CoreV1Api()
        sec = v1.read_namespaced_secret("leofs-secret", 'kubeflow').data
        aws_key = base64.b64decode(sec.get("password")).decode('utf-8')
        return aws_key


    def upload_model(self, model_path, trainingjob_name, version, model_under_version_folder=True):
        """
        This function upload folder/file which is at model_path in bucket with version prefix
        as zip file. if model_under_version_folder is True then folder/file which is at model_path
        is put under version folder as zip file otherwise is put directly as zip file.
        args:
            model_path: location of file which will be uploaded
            trainingjob_name: bucket name
            version: version
            model_under_version_folder: boolean flag indicating where folder/file which is at
                                        model_path is put under version folder or not as zip file
        return value:
            None
        """
        try:
            # Create a temporary Directory for copying model from model_path
            with tempfile.TemporaryDirectory() as model_copy_dir:
                model_copy_dir = model_copy_dir + '/copy/'
                if model_under_version_folder:
                    # Copy the model in another directory named with "version number"
                    version_path = os.path.join(model_copy_dir, str(version))
                    shutil.copytree(model_path, version_path)
                else:
                    shutil.copytree(model_path, model_copy_dir)

                export_bucket = trainingjob_name

                # Create export bucket if it does not yet exist
                response = self.client.list_buckets()
                export_bucket_exists = False
                for bucket in response["Buckets"]:
                    if bucket["Name"] == export_bucket:
                        export_bucket_exists = True
                if not export_bucket_exists:
                    self.logger.debug("{} bucket is creating".format(export_bucket))
                    self.client.create_bucket(Bucket=export_bucket)
                    self.logger.debug("{} bucket is created".format(export_bucket))

                json_object = { "model_under_version_folder" : model_under_version_folder}
                self.client.put_object(
                    Body=json.dumps(json_object),
                    Bucket=trainingjob_name,
                    Key= str(version) + "/" + "metadata.json"
                )

                # Creating another temporary directory to Archive Model.zip that would get uploaded
                with tempfile.TemporaryDirectory() as upload_dir:
                    model_file_name = "Model"
                    model_object = model_file_name + '.zip'
                    zip_file_full_path = upload_dir +  '/' + model_file_name + '.zip'
                    zip_file_full_path_without_extention = upload_dir +  '/' + model_file_name
                    shutil.make_archive(zip_file_full_path_without_extention, 'zip', model_copy_dir)

                    self.logger.debug("putting object inside bucket!!")
                    self.client.upload_file(
                            zip_file_full_path,
                            export_bucket,
                            str(version) +"/" + model_object
                    )
                    self.logger.debug("object is put inside bucket")
                    # After Uploading, Temporary directories would get deleted automatically when upload_dir and model_copy_dir goes out of scope
            response = self.client.list_objects(Bucket=export_bucket, Prefix="")
            self.logger.debug("All objects in %s:",export_bucket)
            for file in response["Contents"]:
                self.logger.debug("%s/%s",export_bucket,file['Key'])

        except Exception as err:
            self.logger.error(traceback.format_exc())
            raise SdkException(str(err)) from None

    def upload_metrics(self, metrics, trainingjob_name, version):
        """
        This function upload dictionary represting metrics in bucket with version prefix.
        args:
            metrics: dictionary represting metrics
            trainingjob_name: bucket name
            version: version
        return value:
            None
        """
        try:
            export_bucket = trainingjob_name

            # Create export bucket if it does not yet exist
            response = self.client.list_buckets()
            export_bucket_exists = False
            for bucket in response["Buckets"]:
                if bucket["Name"] == export_bucket:
                    export_bucket_exists = True
            if not export_bucket_exists:
                self.logger.debug("{} bucket is creating".format(export_bucket))
                self.client.create_bucket(Bucket=export_bucket)
                self.logger.debug("{} bucket is created".format(export_bucket))

            json_object = metrics
            metrics_file_name = "metrics.json"
            metrics_object = str(version) + "/" + metrics_file_name

            self.logger.debug("putting object inside bucket")
            self.client.put_object(
                    Body=json.dumps(json_object),
                    Bucket=export_bucket,
                    Key=metrics_object
            )
            self.logger.debug("object is put inside bucket")

            response = self.client.list_objects(Bucket=export_bucket, Prefix="")
            self.logger.debug("All objects in %s:",export_bucket)
            for file in response["Contents"]:
                self.logger.debug("%s/%s",export_bucket,file['Key'])
        except Exception as err:
            self.logger.error(traceback.format_exc())
            raise SdkException(str(err)) from None

    def get_metrics(self, trainingjob_name, version):
        """
        This function returns dictionary represting metrics in bucket with version prefix.
        args:
            trainingjob_name: bucket name
            version: version
        return value:
            dictionary represting metrics
        """
        try:
            metrics_file_name = "metrics.json"
            metrics_object = str(version) + "/" + metrics_file_name
            self.logger.debug("fetching json object")
            response = self.client.get_object(
                    Bucket = trainingjob_name,
                    Key = metrics_object
                    )
            json_bytes = response['Body'].read()
            self.logger.debug("stored json: {}".format(str(json_bytes)))
            return json.loads(json_bytes)
        except Exception as err:
            self.logger.error(traceback.format_exc())
            raise SdkException(str(err)) from None

    def get_model_zip(self, trainingjob_name, version):
        """
        This function returns model zip file in memory from bucket whose prefix is version
        args:
            trainingjob_name: bucket name
            version: version
        return value:
            zip file in memory
        """
        try:
            with tempfile.TemporaryDirectory() as model_download_folder:     
                model_file_name = "Model.zip"
                model_object = str(version) + "/" + model_file_name
                path = os.path.join(model_download_folder, trainingjob_name + "_" + version, model_file_name)
                path_without_model_file = os.path.join(model_download_folder, trainingjob_name + "_" + version)
                if not os.path.exists(path_without_model_file):
                    self.logger.debug("create folder in tmp")
                    os.makedirs(path_without_model_file)
                self.logger.debug("start downloading")
                self.client.download_file(
                        Bucket = trainingjob_name,
                        Key = model_object,
                        Filename = path
                        )
                self.logger.debug("finish downloading")
                return_data = BytesIO()
                with open(path, 'rb') as file_open:
                    return_data.write(file_open.read())
                return_data.seek(0)
                return return_data
        except Exception as err:
            self.logger.error(traceback.format_exc())
            raise SdkException(str(err)) from None

    def get_model(self, trainingjob_name, version, download_path):
        """
        This function download model from bucket whose prefix is version at download_path
        args:
            trainingjob_name: bucket name
            version: version
            download_path: download path
        return value:
            None
        """
        try:
            with tempfile.TemporaryDirectory() as download_folder:
                model_file_name = "Model.zip"
                model_object = str(version) + "/" + model_file_name
                path = os.path.join(download_folder, trainingjob_name + "_" + version, model_file_name)
                path_without_model_file = os.path.join(download_folder, trainingjob_name + "_" + version)
                if not os.path.exists(path_without_model_file):
                    self.logger.debug("create folder in tmp")
                    os.makedirs(path_without_model_file)
                self.logger.debug("start downloading")
                self.client.download_file(
                        Bucket = trainingjob_name,
                        Key = model_object,
                        Filename = path
                        )
                self.logger.debug("finish downloading")
                shutil.unpack_archive(path, extract_dir=path_without_model_file)
                response = self.client.get_object(
                        Bucket = trainingjob_name,
                        Key = str(version) + "/" + "metadata.json"
                        )
                json_bytes = response['Body'].read()
                model_under_version_folder = json.loads(json_bytes)['model_under_version_folder']
                if model_under_version_folder:
                    shutil.copytree(os.path.join(path_without_model_file, version),
                                    download_path, dirs_exist_ok=True)
                else:
                    shutil.copytree(path_without_model_file, download_path, dirs_exist_ok=True)
        except Exception as err:
            self.logger.error(traceback.format_exc())
            raise SdkException(str(err)) from None

    def delete_model_metric(self, trainingjob_name, version):
        """
        This functions return True if all objects with version prefix are deleted otherwise
        it returns False
        args:
            trainingjob_name: bucket_name
            version: version
        return value:
            True: if all objectss with version prefix are deleted
            False: if all object with version prefix are not deleted
        """
        try:
            should_be_deleted = []
            if self.check_object(trainingjob_name, version, 'Model.zip'):
                should_be_deleted.append({'Key' : f'{version}/Model.zip'})
            if self.check_object(trainingjob_name, version, 'metrics.json'):
                should_be_deleted.append({'Key' : f'{version}/metrics.json'})
            if self.check_object(trainingjob_name, version, 'metadata.json'):
                should_be_deleted.append({'Key' : '{}/metadata.json'.format(version)})
            for _ in range(3):
                self.logger.debug("should be deleted files: {}".format(str(should_be_deleted)))
                response = self.client.delete_objects(
                        Bucket = trainingjob_name,
                        Delete = {
                            'Objects' : should_be_deleted
                            }
                        )
                self.logger.debug("response: {}".format(str(response)))
                if 'Errors' in response:
                    should_be_deleted = []
                    for error_dict in response['Errors']:
                        should_be_deleted.append({'Key' : error_dict['Key']})
                else:
                    return True
            self.logger.error(should_be_deleted)
            return False
        except Exception as err:
            self.logger.error(traceback.format_exc())
            raise SdkException(str(err)) from None

    def check_object(self, trainingjob_name, version, file_name):
        """
        This function checks object is present in bucket with versions prefix.
        args:
            trainingjob_name: bucket name
            version: version
            file_name: object which we want to check
        return value:
            True: if object is present in bucket with version prefix.
            False: if object is not present in bucket with version prefix.
        """
        try:
            response = self.client.list_objects(
                    Bucket = trainingjob_name,
                    Prefix = str(version) + "/"
                    )
 
        except Exception as err:# pylint: disable=broad-except
            self.logger.debug(str(err))
            return False

        if 'Contents' not in response:
            self.logger.debug("{} bucket's response has no Contents".format(trainingjob_name))
            return False

        for obj in response['Contents']:
            if obj['Key'] == str(version) + "/" + file_name:
                return True
        self.logger.debug("%s not found in bucket:%s ,version:%s",file_name,trainingjob_name,version)
        return False

    def is_bucket_present(self, trainingjob_name):
        """
        This function checks given bucket is present or not.
        args:
            trainingjob_name: bucket name
        return value:
            True: if bucket is present
            False: if bucket is not present
        """
        try:
            response = self.client.list_buckets()
            for bucket in response["Buckets"]:
                if bucket["Name"] == trainingjob_name:
                    return True
            return False
        except Exception as err:
            self.logger.error(traceback.format_exc())
            raise SdkException(str(err)) from None

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
from modelmetricsdk.model_metrics_sdk import ModelMetricsSdk
from mock import patch, MagicMock
import base64
import pytest
import json
import io
import shutil
import logging
import logging.handlers
import os
import tempfile
import zipfile

class pwd_helper():
    def __init__(self):
        self.data = self
    
    def read_namespaced_secret(self, secret_name, namespace):
        return self
    
    def get(self, pwd):
        return  base64.b64encode(bytes("dummy_password", 'utf-8'))

class bucket_helper():
    def __init__(self):
        self.buckets = {
            "Buckets" : [
                {"Name" : "dummy_bucket1"}, 
                {"Name" : "dummy_bucket2"},
                {"Name" : "mymodel", "files": [{"filepath": "/test", "key": "v1.0.0/1/Model.zip"}]}
                ]
            }

    def list_buckets(self):
        return self.buckets
    
    def create_bucket(self, Bucket):
        if Bucket == "Throw_Error":
            # Preventing this bucket to get created, to mimic a bucket error
            raise Exception("Bucket Helper Error")
        self.buckets["Buckets"].append({"Name" : Bucket})
    
    def get_bucket_index(self, Bucket):
        for i in range(len(self.buckets["Buckets"])):
            if (self.buckets["Buckets"][i]["Name"] == Bucket):
                return i
        raise Exception("Bucket Doesn't Exists!!")

    def put_object(self, Bucket, Body, Key):
        bucket_index = self.get_bucket_index(Bucket)
        self.buckets["Buckets"][bucket_index]['Key'] = Key
        self.buckets["Buckets"][bucket_index]['Body'] = io.StringIO(Body) # Storing the Body String as File Pointer

    def upload_file(self, file_path, Bucket, file_name):
        bucket_index = self.get_bucket_index(Bucket)
        if "files" in self.buckets["Buckets"][bucket_index].keys():
            self.buckets["Buckets"][bucket_index]["files"].append({"file_path" : file_path, "key" : file_name})
        else:
            self.buckets["Buckets"][bucket_index]["files"] = [{"file_path" : file_path, "key" : file_name}]

    def list_objects(self, Bucket, Prefix = None):
        if Bucket == "Throw_Error":
            return []
        bucket_index = self.get_bucket_index(Bucket)
        object_key = self.buckets["Buckets"][bucket_index]["files"][0]["key"]
        out = {'ResponseMetadata': {'HTTPStatusCode': 200, 'HTTPHeaders': {'transfer-encoding': 'identity', 'date': 'Thu, 29 Sep 2022 06:03:34 GMT', 'connection': 'close', 'server': 'LeoFS', 'content-type': 'application/xml'}, 'RetryAttempts': 0}, 'IsTruncated': False, 'Marker': '', 'NextMarker': '', 
                'Contents': [
                                {'Key': object_key,'ETag': 'fab9057d19119e147c760727ff4c4b79', 'Size': 1466474946, 'StorageClass': 'STANDARD', 'Owner': {'DisplayName': 'leofs', 'ID': 'leofs'}}, 
                                {'Key': '1/metrics.json','ETag': 'fab9057d19119e147c760727ff4c4b79', 'Size': 1466474946, 'StorageClass': 'STANDARD', 'Owner': {'DisplayName': 'leofs', 'ID': 'leofs'}}, 
                                {'Key': '1/metadata.json','ETag': 'fab9057d19119e147c760727ff4c4b79', 'Size': 1466474946, 'StorageClass': 'STANDARD', 'Owner': {'DisplayName': 'leofs', 'ID': 'leofs'}}, 
                                
                             ], 'Name': Bucket, 'Prefix': '', 'Delimiter': '/', 'MaxKeys': 1000}
        return out
    
    def get_object(self, Bucket, Key):
        bucket_index = self.get_bucket_index(Bucket)
        return self.buckets["Buckets"][bucket_index]

    def download_file(self, Bucket, Key, Filename):
        bucket_index = self.get_bucket_index(Bucket)
        for file in self.buckets["Buckets"][bucket_index]['files']:
            if file['key'] == Key:
                # Saving Locally Since requires Additional permission to write in /tmp/download/
                with open('test/downloaded_model_file.txt', 'w', encoding='utf-8') as file_open:
                    file_open.write("Your Model: Hello World")
                return 

        raise Exception(" Requested File wasn't uploaded")
    
    def delete_objects(self, Bucket, Delete):
        if Bucket == "Throw_Delete_Object_Error":
            return {"Errors" : [{"Key" : "Default Intended Error"}]}

        bucket_index = self.get_bucket_index(Bucket) # To Check If bucket exists or not
        for key in Delete['Objects']:
            return []


mock_resource_filename = 'test/config/config.json'
class Test_model_metrics_sdk():
    @patch('modelmetricsdk.model_metrics_sdk.config.load_incluster_config')
    @patch('modelmetricsdk.model_metrics_sdk.client.CoreV1Api', return_value= pwd_helper())
    @patch('modelmetricsdk.model_metrics_sdk.boto3.client', return_value = bucket_helper())
    @patch('pkg_resources.resource_filename', return_value=mock_resource_filename)
    @patch('modelmetricsdk.singleton_manager.logging.handlers.RotatingFileHandler', return_value = logging.handlers.RotatingFileHandler('test_modelmetricsdk.log',
                    maxBytes=10485760, backupCount=20, encoding='utf-8'))
    def setup_method(self, mock1, mock2, mock3, mock4, mock5, mock6):
        self.obj = ModelMetricsSdk()
        self.modelname = "mymodel"
        self.modelversion = "v1.0.0"
        self.artifactversion = "1"
        self.trainingjob_id = 1
    
    def test_init(self):
        assert self.obj != None, 'Model Metrics Sdk Object Creation Failed'
    
    @patch('modelmetricsdk.model_metrics_sdk.shutil.copytree')
    @patch('modelmetricsdk.model_metrics_sdk.shutil.make_archive')
    def test_upload_model(self, mock1, mock2):
        self.obj.upload_model('test/dummy_model/', self.modelname, self.modelversion, self.artifactversion)
        # In order to check if the test fail or pass, need to check if bucket is created and object is put succesfully
        assert self.obj.client.get_bucket_index(self.modelname) is not None, "Bucket Fails to create during uploading model"
        assert self.obj.client.list_objects(Bucket=self.modelname) is not None, "Object Fails to put in the created Bucket during model upload"

    @patch('modelmetricsdk.model_metrics_sdk.shutil.copytree')
    @patch('modelmetricsdk.model_metrics_sdk.shutil.make_archive')
    @patch('modelmetricsdk.model_metrics_sdk.os.path.exists', return_value = True)
    @patch('modelmetricsdk.model_metrics_sdk.shutil.rmtree')
    def test_upload_model_case2(self, mock1, mock2, mock3, mock4):
        '''
            Case 2: covers the cases when model_under_version_folder = False, 
            and when /tmp/copy/ path exists, (Since, /tmp/ folder can only be ascessed/written with sudo privelleges, Therefore, we need to mock it using patch)
        '''
        self.obj.upload_model('test/dummy_model/', self.modelname, self.modelversion, self.artifactversion, model_under_version_folder=False)
        assert self.obj.client.get_bucket_index(self.modelname) is not None, "Bucket Fails to create during uploading model"
        assert self.obj.client.list_objects(Bucket=self.modelname) is not None, "Object Fails to put in the created Bucket during model upload"

    @patch('modelmetricsdk.model_metrics_sdk.shutil.copytree')
    @patch('modelmetricsdk.model_metrics_sdk.shutil.make_archive')
    def test_negative_upload_model(self, mock1, mock2):
        with pytest.raises(Exception) as exc:
            self.obj.upload_model('test/dummy_model/', "Throw_Error", self.modelversion, self.artifactversion)
        assert "Bucket Helper Error" in str(exc.value)
    
    @patch('modelmetricsdk.model_metrics_sdk.requests.post')
    def test_upload_metrics(self, mock_post):
        try:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response
            metrics = {"accuracy": 97}
            self.obj.upload_metrics( metrics, self.trainingjob_id)
        except Exception as err:
            assert False, "Test_upload_metircs is supposed to pass, but got an error: " + str(err)
        

    def test_negative_upload_metrics_tm_connection_error(self):
        with pytest.raises(Exception) as exc:
            metrics = {"accuracy": 97}
            self.obj.upload_metrics( metrics, self.trainingjob_id)
        assert "Error communicating with TM" in str(exc.value)

    @patch('modelmetricsdk.model_metrics_sdk.requests.get')
    def test_get_metrics(self, mock_get):
        expected_metrics = {"accuracy": 97}
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = expected_metrics
        mock_get.return_value = mock_response
        
        out = self.obj.get_metrics(self.trainingjob_id)
        assert out == expected_metrics, "Uploaded and Fetched Metrics Doesn't Match"

    def test_negative_get_metrics_tm_connection_error(self):
        with pytest.raises(Exception) as exc:
            self.obj.get_metrics(self.trainingjob_id)
        assert "Error communicating with TM" in str(exc.value)

    @patch('modelmetricsdk.model_metrics_sdk.os.makedirs')
    @patch('modelmetricsdk.model_metrics_sdk.open', return_value = open('test/downloaded_model_file.txt', 'rb'))
    def test_get_model_zip(self, mock1, mock2):
        expected_model_content = "Your Model: Hello World"
        downloaded_model = self.obj.get_model_zip(self.modelname, self.modelversion, self.artifactversion)
        model_content = str(downloaded_model.read(), 'utf-8')
        assert model_content == expected_model_content, "Uploaded and Download Model doesn't Match"

    @patch('modelmetricsdk.model_metrics_sdk.os.makedirs')
    @patch('modelmetricsdk.model_metrics_sdk.open', return_value = open('test/downloaded_model_file.txt', 'rb'))
    @patch('modelmetricsdk.model_metrics_sdk.os.path.exists', return_value = True)
    @patch('modelmetricsdk.model_metrics_sdk.shutil.rmtree')
    def test_get_model_zip_case2(self, mock1, mock2, mock3, mock4):
        '''
            Case 2: When /tmp/download path exists
        '''
        expected_model_content = "Your Model: Hello World"
        downloaded_model = self.obj.get_model_zip(self.modelname, self.modelversion, self.artifactversion)
        model_content = str(downloaded_model.read(), 'utf-8')
        assert model_content == expected_model_content, "Uploaded and Download Model doesn't Match"

    @patch('modelmetricsdk.model_metrics_sdk.os.makedirs')
    def test_negative_get_model_zip(self, mock1):
        with pytest.raises(Exception) as exc:
            self.obj.get_model_zip("Throw_Error", self.modelversion, self.artifactversion)
        assert "Bucket Doesn't Exists!!" in str(exc.value)


    def test_delete_model_metric(self):
        assert self.obj.delete_model_metric(self.modelname, self.modelversion, self.artifactversion), 'Delete Model Metric Failed'

    def test_delete_model_metric_case2(self):
        '''
            When Delete_Objects would throw error
        '''
        # Create a Bucket with name : Throw_Delete_Object_Error
        assert not self.obj.delete_model_metric("Throw_Delete_Object_Error", self.modelversion, self.artifactversion), 'Delete Model Metric Passed, whereas It should throw error'

    def test_negative_delete_model_metric(self):
        with pytest.raises(Exception) as exc:
            self.obj.delete_model_metric("Throw_Error", self.modelversion, self.artifactversion)
        assert "Bucket Doesn't Exists!!" in str(exc.value)

    def test_check_object(self):
        assert self.obj.check_object(self.modelname, self.modelversion, self.artifactversion, 'Model.zip'), 'Check Object Failed'
    
    def test_check_object_when_not_present(self):
        assert not self.obj.check_object(self.modelname, self.modelversion, self.artifactversion, 'blah.zip'), 'Check Object Failed, when object not present'

    def test_negative_check_object(self):
        assert not self.obj.check_object('Throw_Error', self.modelversion, self.artifactversion, 'Model.zip')

    def test_is_bucket_present(self):
        assert self.obj.is_bucket_present(self.modelname), 'Bucket {} is not present'.format(self.modelname)
    
    def test_is_bucket_present_when_bucket_is_not_present(self):
        trainingjob_name = "blah"
        assert not self.obj.is_bucket_present(trainingjob_name), 'Bucket {} is present, whereas it should not be present'.format(trainingjob_name)

class Test_export_model:
    # Use the same patching helpers as other tests in the file:
    @patch('modelmetricsdk.model_metrics_sdk.config.load_incluster_config')
    @patch('modelmetricsdk.model_metrics_sdk.client.CoreV1Api', return_value=pwd_helper())
    @patch('modelmetricsdk.model_metrics_sdk.boto3.client', return_value=bucket_helper())
    @patch('pkg_resources.resource_filename', return_value="dummy_resource")
    @patch(
        'modelmetricsdk.singleton_manager.logging.handlers.RotatingFileHandler',
        return_value=logging.handlers.RotatingFileHandler(
            'test_modelmetricsdk.log', maxBytes=10485760, backupCount=20, encoding='utf-8'
        )
    )
    def setup_method(self, mock1, mock2, mock3, mock4, mock5, mock6):
        # Import here so the test module-level patches above are in effect
        from modelmetricsdk.model_metrics_sdk import ModelMetricsSdk
        self.obj = ModelMetricsSdk()
        self.tmpdir = tempfile.mkdtemp()
    def teardown_method(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)
    def _create_dummy_model(self, base_dir):
        model_dir = os.path.join(base_dir, "dummy_model")
        os.makedirs(model_dir, exist_ok=True)
        with open(os.path.join(model_dir, "file1.txt"), "w") as f:
            f.write("hello")
        with open(os.path.join(model_dir, "file2.txt"), "w") as f:
            f.write("world")
        sub = os.path.join(model_dir, "subdir")
        os.makedirs(sub, exist_ok=True)
        with open(os.path.join(sub, "subfile.txt"), "w") as f:
            f.write("sub")
        return model_dir
    def test_export_model_creates_zip_in_cwd(self):
        model_dir = self._create_dummy_model(self.tmpdir)
        old_cwd = os.getcwd()
        os.chdir(self.tmpdir)
        try:
            out_path = self.obj.export_model(model_dir, "myname", "v1", "a1", model_under_version_folder=True)
            assert os.path.exists(out_path), "Zip file was not created"
            assert out_path.endswith("myname_v1_a1.zip")
            with zipfile.ZipFile(out_path, 'r') as z:
                names = z.namelist()
                assert any(name.startswith("v1/") for name in names), "Version folder v1 missing in zip"
                assert any(name.endswith("file1.txt") for name in names)
        finally:
            os.chdir(old_cwd)
            try:
                os.remove(out_path)
            except Exception:
                pass
    def test_export_model_without_version_folder(self):
        model_dir = self._create_dummy_model(self.tmpdir)
        old_cwd = os.getcwd()
        os.chdir(self.tmpdir)
        try:
            out_path = self.obj.export_model(model_dir, "another", "ver2", "art2", model_under_version_folder=False)
            assert os.path.exists(out_path)
            with zipfile.ZipFile(out_path, 'r') as z:
                names = z.namelist()
                assert any(name.endswith("file1.txt") for name in names)
                assert any("subdir/subfile.txt" in name for name in names)
        finally:
            os.chdir(old_cwd)
            try:
                os.remove(out_path)
            except Exception:
                pass
    def test_export_model_overwrites_existing_zip(self):
        model_dir = self._create_dummy_model(self.tmpdir)
        old_cwd = os.getcwd()
        os.chdir(self.tmpdir)
        zip_name = "dup_v_v.zip"
        try:
            # create a dummy existing file at expected path (in cwd)
            with open(zip_name, "w") as f:
                f.write("old")
            out_path = self.obj.export_model(model_dir, "dup", "v", "v", model_under_version_folder=False)
            assert os.path.exists(out_path)
            # ensure it's a valid zip
            with zipfile.ZipFile(out_path, 'r') as z:
                assert z.namelist(), "Zip is empty"
        finally:
            os.chdir(old_cwd)
            try:
                os.remove(os.path.join(self.tmpdir, zip_name))
            except Exception:
                pass
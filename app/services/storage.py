from __future__ import annotations

import os
import uuid
from pathlib import Path

from werkzeug.utils import secure_filename


class LocalReportStorage:
    def __init__(self, upload_folder):
        self.upload_folder = Path(upload_folder)

    def save(self, uploaded_file):
        clean_name = secure_filename(uploaded_file.filename)
        key = f"{uuid.uuid4().hex}_{clean_name}"
        uploaded_file.save(self.upload_folder / key)
        return key

    def path(self, key):
        candidate = (self.upload_folder / key).resolve()
        if self.upload_folder.resolve() not in candidate.parents:
            return None
        return candidate


class S3ReportStorage:
    def __init__(self, bucket, region):
        import boto3
        self.bucket = bucket
        self.client = boto3.client("s3", region_name=region)

    def save(self, uploaded_file):
        clean_name = secure_filename(uploaded_file.filename)
        key = f"reports/{uuid.uuid4().hex}/{clean_name}"
        self.client.upload_fileobj(uploaded_file, self.bucket, key, ExtraArgs={"ServerSideEncryption": "AES256"})
        return key

    def path(self, key):
        return None


def build_storage(config):
    if config.get("S3_REPORTS_BUCKET"):
        return S3ReportStorage(config["S3_REPORTS_BUCKET"], config["AWS_REGION"])
    return LocalReportStorage(config["UPLOAD_FOLDER"])

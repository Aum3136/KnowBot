import boto3
import os
from dotenv import load_dotenv

load_dotenv()

s3_client = boto3.client(
    "s3",
    aws_access_key_id     = os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name           = os.getenv("AWS_REGION", "eu-north-1")
)

BUCKET = os.getenv("S3_BUCKET_NAME", "knowbot-documents")

def upload_file_to_s3(local_path: str, project_id: str, filename: str) -> str:
    s3_key = f"projects/{project_id}/docs/{filename}"
    s3_client.upload_file(local_path, BUCKET, s3_key)
    print(f"[S3] Uploaded: {s3_key}")
    return s3_key

def download_file_from_s3(project_id: str, filename: str, local_path: str):
    s3_key = f"projects/{project_id}/docs/{filename}"
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    s3_client.download_file(BUCKET, s3_key, local_path)
    print(f"[S3] Downloaded: {s3_key} → {local_path}")

def delete_file_from_s3(project_id: str, filename: str):
    s3_key = f"projects/{project_id}/docs/{filename}"
    s3_client.delete_object(Bucket=BUCKET, Key=s3_key)
    print(f"[S3] Deleted: {s3_key}")

def delete_project_from_s3(project_id: str):
    prefix = f"projects/{project_id}/"
    response = s3_client.list_objects_v2(Bucket=BUCKET, Prefix=prefix)
    objects = response.get("Contents", [])
    if objects:
        s3_client.delete_objects(
            Bucket=BUCKET,
            Delete={"Objects": [{"Key": obj["Key"]} for obj in objects]}
        )
    print(f"[S3] Deleted all files for project: {project_id}")

def list_project_files(project_id: str) -> list:
    prefix = f"projects/{project_id}/docs/"
    response = s3_client.list_objects_v2(Bucket=BUCKET, Prefix=prefix)
    files = [
        obj["Key"].split("/")[-1]
        for obj in response.get("Contents", [])
        if not obj["Key"].endswith("/")
    ]
    return files

def test_connection():
    try:
        s3_client.head_bucket(Bucket=BUCKET)
        print(f"[S3] Connected to bucket: {BUCKET}")
        return True
    except Exception as e:
        print(f"[S3] Connection failed: {e}")
        return False

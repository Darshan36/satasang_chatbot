"""Upload the app's data files to an S3-compatible private bucket (e.g. Backblaze B2).

Reads credentials from environment variables (never hard-code them):
  S3_ENDPOINT_URL, S3_BUCKET, S3_ACCESS_KEY_ID, S3_SECRET_ACCESS_KEY, S3_REGION

Run after rebuilding data (build_embeddings.py / recategorize_groq.py) to refresh
what the deployed app downloads at startup.

  python upload_data.py
"""
import os

import boto3
from botocore.config import Config

DATA_FILES = [
    "recategorized_stories.json",
    "embeddings.npy",
    "topic_embeddings.npy",
    "embeddings_meta.json",
    "topics.json",
    "glossary.json",
]


def client():
    return boto3.client(
        "s3",
        endpoint_url=os.environ["S3_ENDPOINT_URL"],
        aws_access_key_id=os.environ["S3_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["S3_SECRET_ACCESS_KEY"],
        region_name=os.environ.get("S3_REGION") or None,
        config=Config(signature_version="s3v4"),
    )


def main():
    s3 = client()
    bucket = os.environ["S3_BUCKET"]
    for f in DATA_FILES:
        s3.upload_file(f, bucket, f)
        print("uploaded", f)
    objs = s3.list_objects_v2(Bucket=bucket).get("Contents", [])
    print("\nbucket contents:")
    for o in sorted(objs, key=lambda x: x["Key"]):
        print(f"  {o['Key']:32} {o['Size']:>10} bytes")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Demo script showing GCS integration usage.

This script demonstrates how to:
1. Load GCS configuration from existing pipeline config
2. Initialize GCS client
3. Upload video artifacts
4. Generate signed URLs for download
5. Clean up artifacts

Usage:
    python examples/gcs_demo.py
"""

import os
import sys
import tempfile
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_demo_video_file() -> str:
    """Create a temporary demo video file for testing"""
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
        # Write some dummy video content
        temp_file.write(b"DEMO VIDEO CONTENT - This would be actual video data in a real scenario")
        temp_path = temp_file.name

    logger.info(f"Created demo video file: {temp_path}")
    return temp_path


def demo_gcs_integration():
    """Demonstrate GCS integration functionality"""
    try:
        # Import GCS modules
        from api.config import load_api_config
        from api.gcs_client import create_gcs_client
        from workers.gcs_uploader import create_worker_uploader

        logger.info("=== GCS Integration Demo ===")

        # 1. Load configuration
        logger.info("1. Loading configuration...")
        try:
            config = load_api_config()
            logger.info(f"   Bucket: {config.gcs.bucket}")
            logger.info(f"   Prefix: {config.gcs.prefix}")
            logger.info(f"   Credentials: {config.gcs.credentials_path or 'Default credentials'}")
        except Exception as e:
            logger.error(f"   Failed to load config: {e}")
            logger.info("   This is expected if pipeline_config.yaml doesn't exist")

            # Create a demo configuration
            from api.config import GCSConfig
            gcs_config = GCSConfig(
                bucket="demo-bucket",
                prefix="demo-prefix",
                signed_url_expiration=3600
            )
            logger.info("   Using demo configuration instead")
        else:
            gcs_config = config.gcs

        # 2. Create GCS client (this will fail without real credentials, which is expected)
        logger.info("2. Creating GCS client...")
        try:
            gcs_client = create_gcs_client(gcs_config)
            logger.info("   ✓ GCS client created successfully")

            # 3. Create worker uploader
            logger.info("3. Creating worker uploader...")
            uploader = create_worker_uploader(gcs_config)
            if uploader:
                logger.info("   ✓ Worker uploader created successfully")
            else:
                logger.error("   ✗ Failed to create worker uploader")
                return

            # 4. Demonstrate artifact path generation
            logger.info("4. Generating artifact paths...")
            job_id = "demo-job-12345"
            artifact_path = gcs_client.generate_artifact_path(job_id)
            logger.info(f"   Generated path: {artifact_path}")

            # 5. Create demo video file
            logger.info("5. Creating demo video file...")
            demo_video_path = create_demo_video_file()

            # 6. Upload artifact (this will fail without real GCS access, which is expected)
            logger.info("6. Uploading artifact...")
            try:
                gcs_uri = uploader.upload_video_artifact(demo_video_path, job_id)
                if gcs_uri:
                    logger.info(f"   ✓ Uploaded to: {gcs_uri}")

                    # 7. Generate signed URL
                    logger.info("7. Generating signed URL...")
                    signed_url = gcs_client.generate_signed_url(gcs_uri)
                    logger.info(f"   ✓ Signed URL: {signed_url[:50]}...")

                    # 8. Verify upload
                    logger.info("8. Verifying upload...")
                    if uploader.verify_upload(gcs_uri):
                        logger.info("   ✓ Upload verified successfully")
                    else:
                        logger.warning("   ⚠ Upload verification failed")

                    # 9. List artifacts
                    logger.info("9. Listing artifacts...")
                    artifacts = gcs_client.list_artifacts(job_id=job_id)
                    logger.info(f"   Found {len(artifacts)} artifacts for job {job_id}")

                else:
                    logger.error("   ✗ Upload failed")

            except Exception as e:
                logger.error(f"   ✗ Upload failed (expected without real GCS credentials): {e}")

            # Clean up demo file
            try:
                os.unlink(demo_video_path)
                logger.info("   Cleaned up demo video file")
            except Exception as e:
                logger.warning(f"   Failed to clean up demo file: {e}")

        except Exception as e:
            logger.error(f"   ✗ GCS client creation failed (expected without real credentials): {e}")
            logger.info("   This is normal when running without proper GCS credentials")

            # Still demonstrate path generation without actual GCS access
            logger.info("   Demonstrating path generation without GCS access...")
            from api.gcs_client import GCSClient
            from datetime import datetime

            # Mock the client initialization to show path generation
            class MockGCSClient:
                def __init__(self, config):
                    self.config = config

                def generate_artifact_path(self, job_id, filename="final_video.mp4"):
                    now = datetime.utcnow()
                    date_prefix = now.strftime("%Y-%m")
                    path_parts = [self.config.prefix, date_prefix, job_id, filename]
                    blob_path = "/".join(path_parts)
                    return f"gs://{self.config.bucket}/{blob_path}"

            mock_client = MockGCSClient(gcs_config)
            demo_path = mock_client.generate_artifact_path("demo-job-12345")
            logger.info(f"   Demo artifact path: {demo_path}")

        logger.info("=== Demo completed ===")

    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.error("Make sure you're running from the project root directory")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")


def demo_configuration_loading():
    """Demonstrate configuration loading from different sources"""
    logger.info("=== Configuration Loading Demo ===")

    try:
        from api.config import load_api_config, GCSConfig

        # Try loading from existing files
        logger.info("1. Attempting to load from existing configuration files...")
        try:
            config = load_api_config()
            logger.info("   ✓ Configuration loaded successfully")
            logger.info(f"   Pipeline config keys: {list(config.pipeline_config.keys())}")

            if 'google_veo' in config.pipeline_config:
                veo_config = config.pipeline_config['google_veo']
                logger.info(f"   Google Veo project: {veo_config.get('project_id', 'Not set')}")
                logger.info(f"   Credentials path: {veo_config.get('credentials_path', 'Not set')}")

        except Exception as e:
            logger.info(f"   Configuration loading failed: {e}")
            logger.info("   This is expected if config files don't exist")

        # Demonstrate manual configuration
        logger.info("2. Creating manual GCS configuration...")
        manual_config = GCSConfig(
            bucket="my-video-bucket",
            prefix="video-api",
            credentials_path="path/to/credentials.json",
            signed_url_expiration=7200  # 2 hours
        )
        logger.info(f"   Bucket: {manual_config.bucket}")
        logger.info(f"   Prefix: {manual_config.prefix}")
        logger.info(f"   Expiration: {manual_config.signed_url_expiration} seconds")

        # Show environment variable override capability
        logger.info("3. Environment variable overrides...")
        logger.info("   You can override config with these environment variables:")
        logger.info("   - GCS_BUCKET: Override bucket name")
        logger.info("   - GCS_CREDENTIALS_PATH: Override credentials path")
        logger.info("   - API_CONFIG_PATH: Path to API config file")
        logger.info("   - PIPELINE_CONFIG_PATH: Path to pipeline config file")

    except ImportError as e:
        logger.error(f"Import error: {e}")


if __name__ == "__main__":
    print("GCS Integration Demo")
    print("===================")
    print()

    demo_configuration_loading()
    print()
    demo_gcs_integration()

    print()
    print("Note: This demo will show errors when trying to access GCS without proper credentials.")
    print("This is expected behavior. The demo shows how the integration would work with real credentials.")

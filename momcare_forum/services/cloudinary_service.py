"""
Cloudinary Image Upload Service
Handles image uploads and storage for posts and products
"""
import requests
import hashlib
import time
import json
import logging
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class CloudinaryService:
    """Service for handling Cloudinary image uploads"""
    
    # Cloudinary configuration
    CLOUD_NAME = 'dy5vntutj'
    API_KEY = '156727476264568'
    API_SECRET = 'oHhCzliSvEq4HuQiJTwvyWbbuvA'
    UPLOAD_URL = f'https://api.cloudinary.com/v1_1/{CLOUD_NAME}/image/upload'
    
    @classmethod
    def generate_signature(cls, params):
        """
        Generate Cloudinary API signature
        Params must be in alphabetical order
        """
        # Sort parameters alphabetically
        sorted_params = sorted(params.items())
        
        # Build query string
        query_string = '&'.join([f'{k}={v}' for k, v in sorted_params])
        
        # Append API secret
        string_to_sign = query_string + cls.API_SECRET
        
        # Generate SHA-1 hash
        signature = hashlib.sha1(string_to_sign.encode()).hexdigest()
        
        logger.debug(f"Generated signature for upload")
        return signature
    
    @classmethod
    def upload_image(cls, image_file, folder='momcare/posts', **kwargs):
        """
        Upload image to Cloudinary
        
        Args:
            image_file: Django UploadedFile object
            folder: Cloudinary folder path
            **kwargs: Additional parameters (public_id, tags, etc.)
        
        Returns:
            dict: Response with 'secure_url' and 'public_id' on success
            None: On failure
        """
        try:
            # Verify API credentials
            if not cls.CLOUD_NAME or not cls.API_KEY or not cls.API_SECRET:
                logger.error("Cloudinary credentials not configured")
                return None
            
            # Prepare upload parameters
            timestamp = int(time.time())
            
            params = {
                'timestamp': timestamp,
                'folder': folder,
                'api_key': cls.API_KEY,
            }
            
            # Add optional parameters
            if 'public_id' in kwargs:
                params['public_id'] = kwargs['public_id']
            
            # Handle tags - convert list to comma-separated string
            if 'tags' in kwargs:
                tags = kwargs['tags']
                if isinstance(tags, list):
                    tags = ','.join(str(t) for t in tags)
                params['tags'] = tags
            
            if 'resource_type' in kwargs:
                params['resource_type'] = kwargs['resource_type']
            
            # Generate signature
            signature_params = {k: v for k, v in params.items() if k != 'api_key'}
            signature = cls.generate_signature(signature_params)
            params['signature'] = signature
            
            # Prepare file for upload
            files = {'file': image_file}
            
            logger.info(f"Uploading image to Cloudinary folder: {folder}, file: {image_file.name}")
            
            # Send request to Cloudinary
            try:
                response = requests.post(cls.UPLOAD_URL, files=files, data=params, timeout=60)
            except requests.Timeout:
                logger.error("Upload timeout after 60 seconds")
                return None
            except requests.ConnectionError as e:
                logger.error(f"Connection error: {str(e)}")
                return None
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✓ Image uploaded successfully: {data.get('secure_url')}")
                return {
                    'secure_url': data.get('secure_url'),
                    'public_id': data.get('public_id'),
                    'width': data.get('width'),
                    'height': data.get('height'),
                    'format': data.get('format'),
                }
            else:
                error_msg = response.text
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', {}).get('message', error_msg)
                except:
                    pass
                logger.error(f"Upload failed with status {response.status_code}: {error_msg}")
                return None
                
        except Exception as e:
            import traceback
            logger.error(f"Error uploading image: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None
    
    @classmethod
    def delete_image(cls, public_id):
        """
        Delete image from Cloudinary
        
        Args:
            public_id: Cloudinary public_id of image to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            timestamp = int(time.time())
            
            params = {
                'public_id': public_id,
                'timestamp': timestamp,
                'api_key': cls.API_KEY,
            }
            
            # Generate signature
            signature_params = {k: v for k, v in params.items() if k != 'api_key'}
            signature = cls.generate_signature(signature_params)
            params['signature'] = signature
            
            destroy_url = f'https://api.cloudinary.com/v1_1/{cls.CLOUD_NAME}/image/destroy'
            response = requests.post(destroy_url, data=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                success = data.get('result') == 'ok'
                logger.info(f"Image deletion {'successful' if success else 'failed'}: {public_id}")
                return success
            else:
                logger.error(f"Delete failed: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting image: {str(e)}")
            return False
    
    @classmethod
    def get_optimized_url(cls, url, width=None, height=None, quality='auto', format='auto'):
        """
        Get optimized image URL with transformations
        
        Args:
            url: Cloudinary image URL
            width: Desired width in pixels
            height: Desired height in pixels
            quality: Quality setting (auto, 80, etc.)
            format: Format setting (auto, webp, jpg, etc.)
            
        Returns:
            str: Optimized image URL
        """
        if 'cloudinary.com' not in url:
            return url
        
        transformations = []
        if width:
            transformations.append(f'w_{width}')
        if height:
            transformations.append(f'h_{height}')
        transformations.append(f'q_{quality}')
        transformations.append(f'f_{format}')
        
        transformation = ','.join(transformations)
        
        # Insert transformation into URL
        return url.replace('/upload/', f'/upload/{transformation}/')

"""
NFT Metadata Management Service

Handles:
- Metadata JSON generation
- IPFS upload (optional)
- On-chain metadata references
- Metadata schema validation
"""

import json
import logging
from typing import Optional, Dict, Any
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class NFTMetadataService:
    """Handle NFT metadata generation and storage"""
    
    # Standard NFT metadata schema
    METADATA_SCHEMA_VERSION = "1.0"
    
    @staticmethod
    def generate_metadata(
        name: str,
        description: str,
        image_url: str,
        attributes: Optional[list] = None,
        external_url: Optional[str] = None,
        animation_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate standard NFT metadata following TON specification
        
        Args:
            name: NFT name/title
            description: NFT description
            image_url: URL to image/artwork
            attributes: List of trait objects
            external_url: URL to view NFT on platform
            animation_url: URL to animation (video, etc)
            
        Returns:
            Metadata dict ready for JSON encoding and IPFS upload
        """
        
        metadata = {
            "name": name.strip(),
            "description": description.strip(),
            "image": image_url.strip(),
        }
        
        # Add optional fields
        if external_url:
            metadata["external_url"] = external_url.strip()
        
        if animation_url:
            metadata["animation_url"] = animation_url.strip()
        
        if attributes:
            metadata["attributes"] = attributes
        
        # Add platform metadata
        metadata["metadata"] = {
            "schema_version": NFTMetadataService.METADATA_SCHEMA_VERSION,
            "platform": "nft-platform",
            "created_at": __import__("datetime").datetime.utcnow().isoformat(),
        }
        
        logger.info(f"[NFTMetadataService] Generated metadata for: {name}")
        return metadata
    
    @staticmethod
    def generate_metadata_json(metadata: Dict[str, Any]) -> str:
        """Serialize metadata to JSON string"""
        return json.dumps(metadata, indent=2)
    
    @staticmethod
    def validate_metadata(metadata: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate metadata structure
        
        Returns:
            (is_valid, error_message)
        """
        
        required_fields = {"name", "description", "image"}
        
        for field in required_fields:
            if field not in metadata:
                return False, f"Missing required field: {field}"
            
            if not isinstance(metadata[field], str) or not metadata[field].strip():
                return False, f"Field '{field}' must be non-empty string"
        
        # Validate attribute structure if present
        if "attributes" in metadata:
            if not isinstance(metadata["attributes"], list):
                return False, "Attributes must be a list"
            
            for attr in metadata["attributes"]:
                if not isinstance(attr, dict):
                    return False, "Each attribute must be an object"
                
                if "trait_type" not in attr or "value" not in attr:
                    return False, "Each attribute must have 'trait_type' and 'value'"
        
        return True, None
    
    @staticmethod
    async def upload_to_ipfs(
        metadata_json: str,
        ipfs_client: Any = None,  # Pinata or similar client
    ) -> Optional[str]:
        """
        Upload metadata to IPFS
        
        Args:
            metadata_json: JSON string of metadata
            ipfs_client: IPFS client (Pinata, Infura, etc)
            
        Returns:
            IPFS hash (ipfs://Qm...) or None if upload failed
        """
        
        try:
            if not ipfs_client:
                logger.warning("[NFTMetadataService] No IPFS client provided, skipping upload")
                return None
            
            # Upload metadata JSON to IPFS
            # Result will be: "ipfs://Qm..."
            response = await ipfs_client.upload_json(metadata_json)
            
            if response and "ipfs_hash" in response:
                ipfs_uri = f"ipfs://{response['ipfs_hash']}"
                logger.info(f"[NFTMetadataService] Metadata uploaded to IPFS: {ipfs_uri}")
                return ipfs_uri
            
            return None
            
        except Exception as e:
            logger.error(f"[NFTMetadataService] IPFS upload failed: {e}")
            return None
    
    @staticmethod
    def generate_backend_metadata_uri(
        nft_id: str,
        base_url: str = "https://api.platform.com",
    ) -> str:
        """
        Generate backend-hosted metadata URI
        
        For when IPFS is not available, metadata can be stored on backend.
        Format: https://api.platform.com/api/v1/nft/{nft_id}/metadata
        
        Args:
            nft_id: ID of the NFT
            base_url: Base URL of the API
            
        Returns:
            Full metadata URI
        """
        
        uri = urljoin(base_url, f"/api/v1/nft/{nft_id}/metadata")
        logger.info(f"[NFTMetadataService] Generated backend metadata URI: {uri}")
        return uri

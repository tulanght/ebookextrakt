# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: src/extract_app/core/wordpress_api_client.py
# Version: 1.0.0
# Author: Antigravity
# Description: WordPress REST API Client for publishing content.
# --------------------------------------------------------------------------------

import requests
from typing import Dict, Any, Optional

class WordPressAPIClient:
    """
    Client for interacting with WordPress REST API.
    Expects site_config dictionary injected from the outside (SettingsManager).
    """

    def __init__(self, site_config: Dict[str, Any]):
        self.site_config = site_config
        self.url = site_config.get("url", "").rstrip("/")
        self.username = site_config.get("username", "")
        self.app_password = site_config.get("app_password", "")
        self.api_base = f"{self.url}/wp-json/wp/v2"

    def _get_auth(self):
        """Returns the Basic Auth tuple for requests."""
        if not self.username or not self.app_password:
            return None
        return (self.username, self.app_password)

    def test_connection(self) -> bool:
        """
        Tests the connection by hitting the /users/me endpoint.
        Returns True if successful, raises an Exception otherwise.
        """
        if not self.url:
            raise ValueError("WordPress URL is not configured.")
        
        auth = self._get_auth()
        if not auth:
            raise ValueError("WordPress Username or App Password is not configured.")

        try:
            response = requests.get(f"{self.api_base}/users/me", auth=auth, timeout=10)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Failed to connect to WordPress: {e}")

    def create_draft(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates a new draft post.
        payload = {title, content, categories, tags, meta}
        Returns a dictionary containing 'wp_post_id' and 'wp_post_url'.
        """
        # Build the WP REST API payload
        wp_payload = {
            "title": payload.get("title", ""),
            "content": payload.get("content", ""),
            "status": "draft"
        }

        # Handle categories (expects array of category IDs)
        if "categories" in payload and isinstance(payload["categories"], list):
            wp_payload["categories"] = payload["categories"]

        # Handle tags (expects array of tag IDs)
        if "tags" in payload and isinstance(payload["tags"], list):
            wp_payload["tags"] = payload["tags"]

        # Optionally handle meta (Custom Fields) if supported by the destination API natively
        if "meta" in payload and isinstance(payload["meta"], dict):
             wp_payload["meta"] = payload["meta"]

        try:
            response = requests.post(
                f"{self.api_base}/posts",
                json=wp_payload,
                auth=self._get_auth(),
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "wp_post_id": data.get("id"),
                "wp_post_url": data.get("link")
            }
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_json = e.response.json()
                    error_msg += f" - {error_json.get('message', '')}"
                except ValueError:
                    pass
            raise Exception(f"Failed to create draft: {error_msg}")

    def publish_post(self, wp_post_id: int) -> bool:
        """
        Updates an existing draft post's status to 'publish'.
        Returns True if successful.
        """
        wp_payload = {
            "status": "publish"
        }

        try:
            # While PATCH is RESTful, POST is standard and widely supported in WP API for updates
            response = requests.post(
                f"{self.api_base}/posts/{wp_post_id}",
                json=wp_payload,
                auth=self._get_auth(),
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            return data.get("status") == "publish"
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_json = e.response.json()
                    error_msg += f" - {error_json.get('message', '')}"
                except ValueError:
                    pass
            raise Exception(f"Failed to publish post: {error_msg}")

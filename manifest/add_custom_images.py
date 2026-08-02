#!/usr/bin/env python3
import json
import hashlib
from datetime import datetime
import os
from pathlib import Path
import shutil
import sys
import urllib.parse
import urllib.request

DEFAULT_REPO_URL = "https://downloads.raspberrypi.com/os_list_imagingutility_v4.json"
CHUNK_SIZE = 1024 * 1024 # read files in 1MB chunks
CACHE_DIR = os.path.join(sys.path[0], "cache")
DEPLOY_DIR = './deploy'
MANIFEST_FILE = os.path.join(DEPLOY_DIR, "os_list_local.rpi-imager-manifest")

CUSTOM_IMAGE_DEFINITIONS = [
    {
        "name": "Custom Raspberry Pi OS (64-bit)",
        "description": "A custom build of Debian for Raspberry Pi",
        "image_pattern": "*-raspi-os-custom-arm64-nominal.img",
        "icon_url": "https://downloads.raspberrypi.com/raspios_arm64/Raspberry_Pi_OS_(64-bit).png",
        "url": None,
        "devices": [
           "pi5-64bit",
           "pi4-64bit",
           "pi3-64bit"
        ],
        "init_format": "cloudinit-rpi",
        "capabilities": []
    },
    {
        "name": "Custom Raspberry Pi OS (64-bit, minimal)",
        "description": "A custom build of Debian for Raspberry Pi",
        "image_pattern": "*-raspi-os-custom-arm64-minimal.img",
        "icon_url": "https://downloads.raspberrypi.com/raspios_arm64/Raspberry_Pi_OS_(64-bit).png",
        "url": None,
        "devices": [
           "pi5-64bit",
           "pi4-64bit",
           "pi3-64bit"
        ],
        "init_format": "cloudinit-rpi",
        "capabilities": []
    },
    {
        "name": "Custom Raspberry Pi OS (32-bit)",
        "description": "A custom build of Debian for Raspberry Pi",
        "image_pattern": "*-raspi-os-custom-nominal.img",
        "icon_url": "https://downloads.raspberrypi.com/raspios_armhf/Raspberry_Pi_OS_(32-bit).png",
        "url": None,
        "devices": [
           "pi5-32bit",
           "pi4-32bit",
           "pi3-32bit",
           "pi2-32bit",
           "pi1-32bit"
        ],
        "init_format": "cloudinit-rpi",
        "capabilities": []
    },
    {
        "name": "Custom Raspberry Pi OS (32-bit, minimal)",
        "description": "A custom build of Debian for Raspberry Pi with minimal packages",
        "image_pattern": "*-raspi-os-custom-minimal.img",
        "icon_url": "https://downloads.raspberrypi.com/raspios_armhf/Raspberry_Pi_OS_(32-bit).png",
        "url": None,
        "devices": [
            "pi5-32bit",
            "pi4-32bit",
            "pi3-32bit",
            "pi2-32bit",
            "pi1-32bit"
        ],
        "init_format": "cloudinit-rpi",
        "capabilities": []
    }
]

class OSListBuilder:
    def __init__(self):
        self.data = {"os_list": []}

    def find_custom_images(self, directory):
        """Find image files in a directory matching a pattern."""

        for definition in CUSTOM_IMAGE_DEFINITIONS:
            pattern = definition["image_pattern"]
            images = sorted(Path(directory).glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
            print(f"Found {len(images)} images for pattern '{pattern}': {[str(img) for img in images]}")

            if len(images) > 0:
                self.add_os(
                    image_path=str(images[0]),
                    **definition
                )

    def add_os(self, name, description, image_path, icon_url, url, devices, **kwargs):
        """Add an OS entry with automatic hash calculation."""
        
        # Calculate SHA256 of the image
        sha256_hash = hashlib.sha256()
        with open(image_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        extract_size = Path(image_path).stat().st_size
        basename = Path(image_path).name
        file_url = f"file:{basename}"
        
        entry = {
            "name": name,
            "description": description,
            "icon": icon_url,
            "url": url if url else file_url,
            "extract_size": extract_size,
            "extract_sha256": sha256_hash.hexdigest(),
            "image_download_size": kwargs.get('download_size', extract_size),
            "release_date": kwargs.get('release_date', 
                                      datetime.now().strftime('%Y-%m-%d')),
            "devices": devices
        }
        
        # Optional fields
        if 'init_format' in kwargs:
            entry['init_format'] = kwargs['init_format']
        if 'website' in kwargs:
            entry['website'] = kwargs['website']
        if 'architecture' in kwargs:
            entry['architecture'] = kwargs['architecture']
        if 'capabilities' in kwargs:
            entry['capabilities'] = kwargs['capabilities']
        
        self.data['os_list'].append(entry)
        return self
    
    def set_imager_metadata(self, latest_version, url, **kwargs):
        """Set top-level imager metadata."""
        self.data['imager'] = {
            "latest_version": latest_version,
            "url": url
        }
        for key in ['default_os', 'embedded_default_os', 
                    'embedded_default_destination']:
            if key in kwargs:
                self.data['imager'][key] = kwargs[key]
        return self
    
    def save(self, output_path):
        """Save to JSON file."""
        with open(output_path, 'w') as f:
            json.dump(self.data, f, indent=2)
        print(f"✓ Saved to {output_path}")

    def download_file(self, url, filename):
        try:
            print(f"Downloading {url} to {filename}")
            with urllib.request.urlopen(url) as response:
                with open(filename, "wb") as fh:
                    shutil.copyfileobj(response, fh, CHUNK_SIZE)
                    return True
        except Exception:
            return False

    def fatal_error(self, reason):
        print(f"Error: {reason}")
        sys.exit(1)

    def fetch_repo_manifest(self, url=DEFAULT_REPO_URL):
        """Fetch the OS list manifest from the repository."""

        repo_urlparts = urllib.parse.urlparse(url)
        if not repo_urlparts.netloc or repo_urlparts.scheme not in ("http", "https"):
            self.fatal_error("Expected repo to be a http:// or https:// URL")

        repo_filename = os.path.basename(repo_urlparts.path)
        if Path(repo_filename).exists():
            online_json_file = repo_filename
        else:
            os.makedirs(CACHE_DIR, exist_ok=True)
            online_json_file = os.path.join(CACHE_DIR, repo_filename)

        if Path(online_json_file).exists():
            print(f"Info: {online_json_file} already exists, so using local file")
        else:
            if not self.download_file(url, online_json_file):
                self.fatal_error(f"Couldn't download {url}")

        return online_json_file

    def create_manifest_from_online(self):
        """Copy the online manifest to the local output file."""
        online_json_file = self.fetch_repo_manifest()
        with open(online_json_file) as online_fh:
            online_data = json.load(online_fh)

        self.data
        if "imager" in online_data and "devices" in online_data["imager"]:
            self.data["imager"] = dict()
            self.data["imager"]["devices"] = list()
            for device in online_data["imager"]["devices"]:
                self.data["imager"]["devices"].append(device)

if __name__ == "__main__":
    builder = OSListBuilder()
    builder.create_manifest_from_online()
    builder.find_custom_images(DEPLOY_DIR)
    builder.save(MANIFEST_FILE)

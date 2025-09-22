"""
Facebook Ads Domain Search - Streamlit App
Fixed version with working save functionality and real-time table creation
"""

import streamlit as st
import json
import sqlite3
import os
from datetime import datetime, timedelta, timezone, date
from apify_client import ApifyClient
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import quote_plus
import time
import hashlib
from io import BytesIO
import zipfile
import requests
import re
from bs4 import BeautifulSoup
# =============================================================================
# COUNTRY LIST (ISO 3166-1 alpha-2)
# =============================================================================

COUNTRIES: list[tuple[str, str]] = [
    ("AF", "Afghanistan"), ("AL", "Albania"), ("DZ", "Algeria"), ("AS", "American Samoa"), ("AD", "Andorra"),
    ("AO", "Angola"), ("AI", "Anguilla"), ("AQ", "Antarctica"), ("AG", "Antigua and Barbuda"), ("AR", "Argentina"),
    ("AM", "Armenia"), ("AW", "Aruba"), ("AU", "Australia"), ("AT", "Austria"), ("AZ", "Azerbaijan"),
    ("BS", "Bahamas"), ("BH", "Bahrain"), ("BD", "Bangladesh"), ("BB", "Barbados"), ("BY", "Belarus"),
    ("BE", "Belgium"), ("BZ", "Belize"), ("BJ", "Benin"), ("BM", "Bermuda"), ("BT", "Bhutan"),
    ("BO", "Bolivia"), ("BQ", "Bonaire, Sint Eustatius and Saba"), ("BA", "Bosnia and Herzegovina"), ("BW", "Botswana"),
    ("BV", "Bouvet Island"), ("BR", "Brazil"), ("IO", "British Indian Ocean Territory"), ("BN", "Brunei Darussalam"),
    ("BG", "Bulgaria"), ("BF", "Burkina Faso"), ("BI", "Burundi"), ("CV", "Cabo Verde"), ("KH", "Cambodia"),
    ("CM", "Cameroon"), ("CA", "Canada"), ("KY", "Cayman Islands"), ("CF", "Central African Republic"), ("TD", "Chad"),
    ("CL", "Chile"), ("CN", "China"), ("CX", "Christmas Island"), ("CC", "Cocos (Keeling) Islands"), ("CO", "Colombia"),
    ("KM", "Comoros"), ("CG", "Congo"), ("CD", "Congo, Democratic Republic of the"), ("CK", "Cook Islands"), ("CR", "Costa Rica"),
    ("CI", "Côte d'Ivoire"), ("HR", "Croatia"), ("CU", "Cuba"), ("CW", "Curaçao"), ("CY", "Cyprus"), ("CZ", "Czechia"),
    ("DK", "Denmark"), ("DJ", "Djibouti"), ("DM", "Dominica"), ("DO", "Dominican Republic"), ("EC", "Ecuador"),
    ("EG", "Egypt"), ("SV", "El Salvador"), ("GQ", "Equatorial Guinea"), ("ER", "Eritrea"), ("EE", "Estonia"),
    ("SZ", "Eswatini"), ("ET", "Ethiopia"), ("FK", "Falkland Islands"), ("FO", "Faroe Islands"), ("FJ", "Fiji"),
    ("FI", "Finland"), ("FR", "France"), ("GF", "French Guiana"), ("PF", "French Polynesia"), ("TF", "French Southern Territories"),
    ("GA", "Gabon"), ("GM", "Gambia"), ("GE", "Georgia"), ("DE", "Germany"), ("GH", "Ghana"), ("GI", "Gibraltar"),
    ("GR", "Greece"), ("GL", "Greenland"), ("GD", "Grenada"), ("GP", "Guadeloupe"), ("GU", "Guam"), ("GT", "Guatemala"),
    ("GG", "Guernsey"), ("GN", "Guinea"), ("GW", "Guinea-Bissau"), ("GY", "Guyana"), ("HT", "Haiti"), ("HM", "Heard Island and McDonald Islands"),
    ("VA", "Holy See"), ("HN", "Honduras"), ("HK", "Hong Kong"), ("HU", "Hungary"), ("IS", "Iceland"), ("IN", "India"),
    ("ID", "Indonesia"), ("IR", "Iran"), ("IQ", "Iraq"), ("IE", "Ireland"), ("IM", "Isle of Man"), ("IL", "Israel"),
    ("IT", "Italy"), ("JM", "Jamaica"), ("JP", "Japan"), ("JE", "Jersey"), ("JO", "Jordan"), ("KZ", "Kazakhstan"),
    ("KE", "Kenya"), ("KI", "Kiribati"), ("KP", "Korea, North"), ("KR", "Korea, South"), ("KW", "Kuwait"), ("KG", "Kyrgyzstan"),
    ("LA", "Lao People's Democratic Republic"), ("LV", "Latvia"), ("LB", "Lebanon"), ("LS", "Lesotho"), ("LR", "Liberia"),
    ("LY", "Libya"), ("LI", "Liechtenstein"), ("LT", "Lithuania"), ("LU", "Luxembourg"), ("MO", "Macao"), ("MG", "Madagascar"),
    ("MW", "Malawi"), ("MY", "Malaysia"), ("MV", "Maldives"), ("ML", "Mali"), ("MT", "Malta"), ("MH", "Marshall Islands"),
    ("MQ", "Martinique"), ("MR", "Mauritania"), ("MU", "Mauritius"), ("YT", "Mayotte"), ("MX", "Mexico"), ("FM", "Micronesia"),
    ("MD", "Moldova"), ("MC", "Monaco"), ("MN", "Mongolia"), ("ME", "Montenegro"), ("MS", "Montserrat"), ("MA", "Morocco"),
    ("MZ", "Mozambique"), ("MM", "Myanmar"), ("NA", "Namibia"), ("NR", "Nauru"), ("NP", "Nepal"), ("NL", "Netherlands"),
    ("NC", "New Caledonia"), ("NZ", "New Zealand"), ("NI", "Nicaragua"), ("NE", "Niger"), ("NG", "Nigeria"), ("NU", "Niue"),
    ("NF", "Norfolk Island"), ("MK", "North Macedonia"), ("MP", "Northern Mariana Islands"), ("NO", "Norway"), ("OM", "Oman"),
    ("PK", "Pakistan"), ("PW", "Palau"), ("PS", "Palestine, State of"), ("PA", "Panama"), ("PG", "Papua New Guinea"), ("PY", "Paraguay"),
    ("PE", "Peru"), ("PH", "Philippines"), ("PN", "Pitcairn"), ("PL", "Poland"), ("PT", "Portugal"), ("PR", "Puerto Rico"),
    ("QA", "Qatar"), ("RE", "Réunion"), ("RO", "Romania"), ("RU", "Russian Federation"), ("RW", "Rwanda"), ("BL", "Saint Barthélemy"),
    ("SH", "Saint Helena, Ascension and Tristan da Cunha"), ("KN", "Saint Kitts and Nevis"), ("LC", "Saint Lucia"), ("MF", "Saint Martin (French part)"),
    ("PM", "Saint Pierre and Miquelon"), ("VC", "Saint Vincent and the Grenadines"), ("WS", "Samoa"), ("SM", "San Marino"),
    ("ST", "Sao Tome and Principe"), ("SA", "Saudi Arabia"), ("SN", "Senegal"), ("RS", "Serbia"), ("SC", "Seychelles"),
    ("SL", "Sierra Leone"), ("SG", "Singapore"), ("SX", "Sint Maarten (Dutch part)"), ("SK", "Slovakia"), ("SI", "Slovenia"),
    ("SB", "Solomon Islands"), ("SO", "Somalia"), ("ZA", "South Africa"), ("GS", "South Georgia and the South Sandwich Islands"),
    ("SS", "South Sudan"), ("ES", "Spain"), ("LK", "Sri Lanka"), ("SD", "Sudan"), ("SR", "Suriname"), ("SJ", "Svalbard and Jan Mayen"),
    ("SE", "Sweden"), ("CH", "Switzerland"), ("SY", "Syrian Arab Republic"), ("TW", "Taiwan"), ("TJ", "Tajikistan"), ("TZ", "Tanzania"),
    ("TH", "Thailand"), ("TL", "Timor-Leste"), ("TG", "Togo"), ("TK", "Tokelau"), ("TO", "Tonga"), ("TT", "Trinidad and Tobago"),
    ("TN", "Tunisia"), ("TR", "Türkiye"), ("TM", "Turkmenistan"), ("TC", "Turks and Caicos Islands"), ("TV", "Tuvalu"),
    ("UG", "Uganda"), ("UA", "Ukraine"), ("AE", "United Arab Emirates"), ("GB", "United Kingdom"), ("US", "United States"),
    ("UM", "United States Minor Outlying Islands"), ("UY", "Uruguay"), ("UZ", "Uzbekistan"), ("VU", "Vanuatu"), ("VE", "Venezuela"),
    ("VN", "Viet Nam"), ("VG", "Virgin Islands (British)"), ("VI", "Virgin Islands (U.S.)"), ("WF", "Wallis and Futuna"), ("EH", "Western Sahara"),
    ("YE", "Yemen"), ("ZM", "Zambia"), ("ZW", "Zimbabwe")
]

COUNTRY_NAME_BY_CODE: dict[str, str] = {code: name for code, name in COUNTRIES}
# =============================================================================
# IMAGE FETCH HELPER (robust against CDN timeouts)
# =============================================================================

def _fetch_image_bytes(url: str, *, timeout: float = 10.0, retries: int = 3, save_path: str | None = None) -> bytes | None:
    """Download image bytes with robust retry and comprehensive headers.

    Returns None on failure.
    """
    if not url or not isinstance(url, str):
        return None

    # Clean and validate URL
    url = url.strip()
    if not url.startswith(('http://', 'https://')):
        return None

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        ),
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.facebook.com/ads/library/",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Sec-Fetch-Dest": "image",
        "Sec-Fetch-Mode": "no-cors",
        "Sec-Fetch-Site": "cross-site",
    }

    last_err: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
            resp.raise_for_status()

            # Check content type
            ct = resp.headers.get("Content-Type", "").lower()
            content_length = len(resp.content)

            # Accept various image types
            valid_types = ["image/", "application/octet-stream"]
            is_valid_type = any(ct.startswith(vt) for vt in valid_types)

            # Also check file extensions
            url_lower = url.lower()
            has_image_ext = any(url_lower.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".bmp"])

            if not (is_valid_type or has_image_ext):
                last_err = RuntimeError(f"Unexpected content-type: {ct}, size: {content_length}")
                continue

            if content_length < 5000:  # Creatives should be much larger than profile pics (5KB+)
                last_err = RuntimeError(f"Content too small for creative: {content_length} bytes")
                continue

            # Save to file if path provided
            if save_path:
                try:
                    with open(save_path, 'wb') as f:
                        f.write(resp.content)
                    print(f"💾 Saved creative to: {save_path}")
                except Exception as e:
                    print(f"❌ Failed to save to {save_path}: {e}")
                    return None

            return resp.content

        except Exception as e:  # noqa: BLE001
            last_err = e
            if attempt < retries:
                import time
                time.sleep(1)  # Brief pause between retries
            continue

    # Don't show warnings for validation attempts (save_path=None)
    # Only show warnings if we're actually trying to save/display an image
    if save_path is not None:
        try:
            import streamlit as _st  # local import to avoid circulars
            _st.warning(f"Image fetch failed: {url[:50]}... ({str(last_err)[:50]})")
        except Exception:
            pass
    return None

# =============================================================================
# CREATIVE EXTRACTION FUNCTIONS
# =============================================================================

def is_likely_creative_url(url: str) -> bool:
    """Check if URL is likely to be an ad creative (not logo/profile pic)"""
    if not ('fbcdn.net' in url or 'facebook.com' in url or 'fbsbx.com' in url):
        return False

    # Exclude obvious non-creative URLs
    exclude_patterns = [
        'icon', 'avatar', 'emoji', 'badge', '1x1', 'pixel', 'spinner',
        '/photos/', '/profile/', '/pages/', '/groups/', '/events/',
        'logo', 'brand', 'company', 'profile_picture', 'page_profile',
        'thumbnail', 'small', 'tiny',
        'video', '.mp4', 'video_hd_url', 'video_preview_image_url'  # Skip video URLs
    ]

    if any(pattern in url.lower() for pattern in exclude_patterns):
        return False

    # Include patterns that suggest creatives
    include_patterns = [
        'scontent',  # Static content CDN
        '/t39.', '/t31.',  # Facebook image size indicators
        'creative', 'ad', 'campaign'
    ]

    return any(pattern in url.lower() for pattern in include_patterns)


def download_ad_creative(apify_item: Dict[str, Any], ad_archive_id: str) -> bool:
    """Download the best creative for an ad using multi-attempt logic"""
    if not apify_item:
        return False

    # Extract creatives using our enhanced logic
    creatives = extract_ad_creatives_from_snapshot(apify_item, ad_archive_id)

    if not creatives:
        return False

    # Sort creatives by priority (best first)
    priority_order = {
        'creative_thumbnail': 1,
        'link_data_image': 2,
        'video_data_image': 3,
        'direct_field': 4,
        'deep_search': 5
    }

    sorted_creatives = sorted(creatives, key=lambda c: (
        priority_order.get(c.get('type'), 999),
        -c.get('size_hint', 0)  # Higher size_hint first (likely higher quality)
    ))

    # Try to download creatives in priority order until one succeeds
    safe_id = re.sub(r'[^\w\-_]', '_', ad_archive_id)
    save_path = f"creative_{safe_id}.png"

    for i, creative in enumerate(sorted_creatives, 1):
        url = creative['url']

        # Try to download
        image_data = _fetch_image_bytes(url, save_path=save_path)

        if image_data:
            print(f"🏆 Got creative for ad {ad_archive_id} on attempt {i}")
            return True
        else:
            print(f"❌ Creative attempt {i} failed for ad {ad_archive_id}")

    print(f"💥 All {len(sorted_creatives)} creatives failed for ad {ad_archive_id}")
    return False

def scrape_facebook_ad_creative_with_apify(ad_archive_id: str, apify_token: str) -> List[str]:
    """Fallback: Use Apify to scrape individual Facebook Ads Library page for creative image"""
    try:
        print(f"🔄 FALLBACK: Using Apify to scrape Facebook page for ad {ad_archive_id}...")

        # Construct Facebook Ads Library URL for this specific ad
        fb_url = f"https://www.facebook.com/ads/library/?id={ad_archive_id}"

        # Use Apify's Facebook Ads Library scraper to get detailed ad data
        client = ApifyClient(apify_token)

        run_input = {
            "urls": [{"url": fb_url, "method": "GET"}],
            "count": 1,  # We only want this specific ad
            "scrapeAdDetails": True,
            "scrapePageAds.activeStatus": "all",
            "period": ""
        }

        run = client.actor("curious_coder/facebook-ads-library-scraper").call(run_input=run_input)
        dataset_id = run.get("defaultDatasetId")
        if not dataset_id:
            print(f"❌ No dataset ID returned from Apify fallback for ad {ad_archive_id}")
            return []

        items = list(client.dataset(dataset_id).iterate_items())

        print(f"📊 Fallback returned {len(items)} items:")
        for i, item in enumerate(items):
            item_id = item.get('ad_archive_id', 'NO_ID')
            print(f"   {i+1}. Ad ID: {item_id}")

        if not items:
            print(f"❌ No items returned from Apify fallback for ad {ad_archive_id}")
            return []

        # Find the item with the correct ad_archive_id
        fallback_item = None
        for item in items:
            if item.get('ad_archive_id') == ad_archive_id:
                fallback_item = item
                break

        # If we didn't find the exact ad, try the first item as fallback
        if not fallback_item:
            print(f"⚠️  Exact ad {ad_archive_id} not found in fallback results, using first item")
            fallback_item = items[0]

        # Double-check we have the right item
        found_id = fallback_item.get('ad_archive_id')
        if found_id != ad_archive_id:
            print(f"⚠️  Fallback returned different ad ID: {found_id} instead of {ad_archive_id}")
        else:
            print(f"✅ Found correct ad ID: {found_id}")

        # Extract creative URLs from the fallback data
        creative_urls = []

        def add_creative_fallback(url: str):
            if url and is_likely_creative_url(url):
                creative_urls.append(url)

        # Direct fields
        if fallback_item.get('original_image_url'):
            add_creative_fallback(fallback_item['original_image_url'])

        if fallback_item.get('image_url'):
            add_creative_fallback(fallback_item['image_url'])

        # Snapshot-based extraction (same as main logic)
        snapshot = fallback_item.get('snapshot', {})
        if isinstance(snapshot, dict):
            # Check various nested locations
            if snapshot.get('creatives'):
                for creative in snapshot['creatives']:
                    if creative.get('thumbnail'):
                        add_creative_fallback(creative['thumbnail'])
                    if creative.get('object_story_spec', {}).get('link_data', {}).get('image', {}).get('url'):
                        add_creative_fallback(creative['object_story_spec']['link_data']['image']['url'])
                    if creative.get('object_story_spec', {}).get('video_data', {}).get('image', {}).get('url'):
                        add_creative_fallback(creative['object_story_spec']['video_data']['image']['url'])

            # Deep search in snapshot (same as main logic)
            def find_images_recursive_fallback(obj, path=""):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        if key in ['image', 'images', 'thumbnail', 'thumbnails', 'picture', 'pictures', 'photo', 'photos']:
                            if isinstance(value, str) and value.startswith('http'):
                                add_creative_fallback(value)
                            elif isinstance(value, dict) and value.get('url'):
                                add_creative_fallback(value['url'])
                            elif isinstance(value, list):
                                for i, item in enumerate(value):
                                    if isinstance(item, str) and item.startswith('http'):
                                        add_creative_fallback(item)
                                    elif isinstance(item, dict) and item.get('url'):
                                        add_creative_fallback(item['url'])
                        elif isinstance(value, (dict, list)):
                            find_images_recursive_fallback(value, f"{path}.{key}" if path else key)
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        find_images_recursive_fallback(item, f"{path}[{i}]" if path else f"[{i}]")

            find_images_recursive_fallback(snapshot)

        # Remove duplicates
        creative_urls = list(set(creative_urls))

        print(f"📸 Found {len(creative_urls)} potential creative URLs via Apify fallback")

        if not creative_urls:
            print(f"❌ No creative images found via Apify fallback for ad {ad_archive_id}")
            return []

        # Return the URLs in priority order (same logic as main extraction)
        priority_order = {
            'creative_thumbnail': 1,
            'link_data_image': 2,
            'video_data_image': 3,
            'direct_field': 4,
            'deep_search': 5
        }

        # Classify URLs by priority
        classified_creatives = []
        for url in creative_urls:
            # Simple classification based on URL patterns
            if 'thumbnail' in url:
                creative_type = 'creative_thumbnail'
            elif 'link_data' in url or 'object_story_spec' in url:
                creative_type = 'link_data_image'
            elif 'video_data' in url:
                creative_type = 'video_data_image'
            else:
                creative_type = 'direct_field'

            classified_creatives.append({
                'url': url,
                'type': creative_type,
                'size_hint': 100000  # Default size hint
            })

        # Sort by priority and return just the URLs
        sorted_creatives = sorted(classified_creatives, key=lambda c: (
            priority_order.get(c.get('type'), 999),
            -c.get('size_hint', 0)
        ))

        sorted_urls = [creative['url'] for creative in sorted_creatives]
        print(f"🏆 SUCCESS! Apify fallback extracted {len(sorted_urls)} creative URLs for ad {ad_archive_id}")
        return sorted_urls

    except Exception as e:
        print(f"❌ Apify fallback failed for ad {ad_archive_id}: {e}")
        return []

def _get_snapshot_dict(item: dict) -> dict:
    """Extract snapshot JSON from API response"""
    snap = item.get("snapshot")
    if isinstance(snap, str):
        try:
            import json
            snap = json.loads(snap)
        except Exception:
            snap = {}
    if not isinstance(snap, dict):
        snap = {}
    return snap

def extract_ad_creatives_from_snapshot(item: dict, ad_id: str) -> List[Dict[str, Any]]:
    """Extract ACTUAL ad creatives (not logos/profile pics) from Facebook ad data"""
    snap = _get_snapshot_dict(item)
    creatives = []

    # Method 1: Look for creatives in the snapshot
    if snap.get("creatives"):
        creative_data = snap["creatives"]
        if isinstance(creative_data, list):
            for creative in creative_data:
                if isinstance(creative, dict):
                    # Look for image URLs in creative objects
                    creative_urls = find_creative_urls_in_object(creative, f"creatives[{creative_data.index(creative)}]")
                    creatives.extend(creative_urls)

    # Method 2: Look for specific ad creative fields
    if snap.get("creative"):
        creative_obj = snap["creative"]
        if isinstance(creative_obj, dict):
            # Check for thumbnail
            if creative_obj.get("thumbnail"):
                thumb = creative_obj["thumbnail"]
                if isinstance(thumb, str) and is_likely_creative_url(thumb):
                    creatives.append({
                        'url': thumb,
                        'source': 'creative.thumbnail',
                        'type': 'creative_thumbnail',
                        'size_hint': estimate_image_size_from_url(thumb)
                    })

            # Check for object_story_spec (common in Facebook ads)
            if creative_obj.get("object_story_spec"):
                story_spec = creative_obj["object_story_spec"]
                if isinstance(story_spec, dict):
                    # Link data images
                    if story_spec.get("link_data"):
                        link_data = story_spec["link_data"]
                        if isinstance(link_data, dict) and link_data.get("image"):
                            img_url = link_data["image"]
                            if isinstance(img_url, dict) and img_url.get("url"):
                                url = img_url["url"]
                                if is_likely_creative_url(url):
                                    creatives.append({
                                        'url': url,
                                        'source': 'creative.object_story_spec.link_data.image.url',
                                        'type': 'link_data_image',
                                        'size_hint': estimate_image_size_from_url(url)
                                    })

                    # Video data images (thumbnail)
                    if story_spec.get("video_data"):
                        video_data = story_spec["video_data"]
                        if isinstance(video_data, dict) and video_data.get("image"):
                            img_url = video_data["image"]
                            if isinstance(img_url, dict) and img_url.get("url"):
                                url = img_url["url"]
                                if is_likely_creative_url(url):
                                    creatives.append({
                                        'url': url,
                                        'source': 'creative.object_story_spec.video_data.image.url',
                                        'type': 'video_data_image',
                                        'size_hint': estimate_image_size_from_url(url)
                                    })

    # Method 3: Deep search for creative-like URLs in the entire snapshot
    all_nested_urls = find_creative_urls_deep(snap)

    # Filter and prioritize actual creatives over logos/profile pics
    for url_info in all_nested_urls:
        url = url_info['url']

        # Skip obvious non-creative URLs
        if any(skip in url.lower() for skip in [
            'icon', 'avatar', 'emoji', 'badge', '1x1', 'pixel', 'spinner',
            '/photos/', '/profile/', '/pages/', '/groups/', '/events/',
            'logo', 'brand', 'company', 'profile_picture', 'page_profile',
            'video', 'video_hd_url', 'video_preview_image_url'  # Skip video URLs
        ]):
            continue

        # Only include if it's likely a creative and not already found
        if is_likely_creative_url(url):
            creatives.append(url_info)

    # Remove duplicates and prioritize higher quality sources
    seen_urls = set()
    unique_creatives = []
    priority_order = ['creative_thumbnail', 'link_data_image', 'video_data_image', 'direct_field', 'deep_search']

    # Sort by priority
    creatives.sort(key=lambda x: priority_order.index(x.get('type', 'deep_search')) if x.get('type') in priority_order else 999)

    for creative in creatives:
        if creative['url'] not in seen_urls:
            seen_urls.add(creative['url'])
            unique_creatives.append(creative)

    return unique_creatives

def select_best_creative(creatives: List[Dict[str, Any]], ad_archive_id: str) -> Dict[str, Any] | None:
    """Select the best single creative for an ad (highest quality, largest file)"""
    if not creatives:
        return None

    # If only one creative, return it
    if len(creatives) == 1:
        return creatives[0]

    # Sort by priority: prefer original images over resized, then by file size hint
    priority_order = {
        'creative_thumbnail': 1,
        'link_data_image': 2,
        'video_data_image': 3,
        'direct_field': 4,
        'deep_search': 5
    }

    sorted_creatives = sorted(creatives, key=lambda c: (
        priority_order.get(c.get('type'), 999),
        -c.get('size_hint', 0)  # Higher size_hint first (likely higher quality)
    ))

    best_creative = sorted_creatives[0]
    print(f"     🎯 Selected best creative for ad {ad_archive_id}: {best_creative['url'][:50]}... (type: {best_creative.get('type')}, size: {best_creative.get('size_hint')})")
    if len(creatives) > 1:
        print(f"     🗑️  Skipped {len(creatives) - 1} duplicate/resized versions")

    return best_creative

def find_creative_urls_in_object(obj: dict, path: str = "") -> List[Dict[str, Any]]:
    """Find creative URLs in a specific object"""
    urls = []

    # Common creative-related keys
    creative_keys = [
        'image_url', 'image', 'picture', 'thumbnail', 'creative_url',
        'media_url', 'asset_url', 'file_url', 'source_url'
    ]

    for key in creative_keys:
        if key in obj:
            value = obj[key]
            if isinstance(value, str) and ('fbcdn.net' in value or 'facebook.com' in value):
                urls.append({
                    'url': value,
                    'source': f"{path}.{key}",
                    'type': 'direct_field',
                    'size_hint': estimate_image_size_from_url(value)
                })
            elif isinstance(value, dict) and 'url' in value:
                url_val = value.get('url')
                if url_val and ('fbcdn.net' in url_val or 'facebook.com' in url_val):
                    urls.append({
                        'url': url_val,
                        'source': f"{path}.{key}.url",
                        'type': 'nested_object',
                        'size_hint': estimate_image_size_from_url(url_val)
                    })

    return urls

def find_creative_urls_deep(obj: dict, path: str = "") -> List[Dict[str, Any]]:
    """Deep search for creative URLs in nested Facebook data"""
    urls = []

    def _search_recursive(current_obj, current_path):
        if isinstance(current_obj, dict):
            for k, v in current_obj.items():
                new_path = f"{current_path}.{k}" if current_path else k

                if isinstance(v, str) and is_likely_creative_url(v):
                    urls.append({
                        'url': v,
                        'source': new_path,
                        'type': 'deep_search',
                        'size_hint': estimate_image_size_from_url(v)
                    })
                else:
                    _search_recursive(v, new_path)
        elif isinstance(current_obj, list):
            for i, item in enumerate(current_obj):
                new_path = f"{current_path}[{i}]"
                _search_recursive(item, new_path)

    _search_recursive(obj, path)
    return urls

def estimate_image_size_from_url(url: str) -> int:
    """Estimate image size from URL patterns (rough heuristic)"""
    # Larger images often have different path patterns
    if '/t39.' in url:  # Large images
        return 100000  # ~100KB
    elif '/t31.' in url:  # Medium images
        return 50000   # ~50KB
    elif 'scontent' in url:
        return 25000   # ~25KB
    else:
        return 10000   # ~10KB (smaller, possibly logos)

def test_and_validate_creative(apify_item: Dict[str, Any], ad_archive_id: str) -> Tuple[bool, str]:
    """Test and validate creative URLs to ensure they're not profile pics/logos - using the test script logic"""

    # Extract creatives using our enhanced logic
    creatives = extract_ad_creatives_from_snapshot(apify_item, ad_archive_id)

    if not creatives:
        return False, ""

    # Sort creatives by priority (best first) - same logic as test script
    priority_order = {
        'creative_thumbnail': 1,
        'link_data_image': 2,
        'video_data_image': 3,
        'direct_field': 4,
        'deep_search': 5
    }

    sorted_creatives = sorted(creatives, key=lambda c: (
        priority_order.get(c.get('type'), 999),
        -c.get('size_hint', 0)  # Higher size_hint first (likely higher quality)
    ))

    # Show progress bar for validation
    progress_text = f"🔍 Validating creatives for ad {ad_archive_id[:10]}..."
    progress_bar = st.progress(0, text=progress_text)

    total_creatives = len(sorted_creatives)

    # Try to validate creatives in priority order until we find a real creative (not profile pic)
    for i, creative in enumerate(sorted_creatives):
        url = creative['url']

        # Update progress
        progress = int((i + 1) / total_creatives * 100)
        progress_bar.progress(progress, text=f"{progress_text} ({i+1}/{total_creatives})")

        # Test the URL by trying to fetch it (same logic as test script)
        image_data = _fetch_image_bytes(url, save_path=None)  # Don't save, just validate

        if image_data:
            progress_bar.progress(100, text=f"✅ Found creative! ({len(image_data)} bytes)")
            progress_bar.empty()  # Remove the progress bar
            return True, url  # This is a real creative, not a profile pic!

    # No valid creative found
    progress_bar.progress(100, text="❌ No valid creatives found")
    progress_bar.empty()  # Remove the progress bar
    return False, ""

def get_ad_creative_urls_with_fallback(apify_item: Dict[str, Any], ad_archive_id: str, apify_token: str, domain: str = "") -> Tuple[bool, List[str]]:
    """Get creative URLs using the WORKING extraction logic from the test script with validation"""

    # Test and validate creatives to ensure they're not profile pics/logos
    found_valid_creative, valid_url = test_and_validate_creative(apify_item, ad_archive_id)

    if found_valid_creative and valid_url:
        return True, [valid_url]

    # If no valid creatives found, check if this is one of the problematic domains
    fallback_domains = {"CAREERSEEKING.CO", "HEALTHANDWEALTHGUIDE.COM", "INFORMATIONSPHERE.CO"}
    if domain.upper() in fallback_domains:
        print(f"🔄 No valid images found in primary data for ad {ad_archive_id} ({domain}), trying fallback...")
        # For now, disable the broken fallback
        print(f"⚠️  Fallback temporarily disabled - primary extraction should work better")
        # fallback_urls = scrape_facebook_ad_creative_with_apify(ad_archive_id, apify_token)
        # if fallback_urls:
        #     return True, fallback_urls

    print(f"💥 No valid creatives found for ad {ad_archive_id} ({domain})")
    return False, []


# Assistant / image generation engine
try:
    from . import assistant_engine as ae  # when packaged
except Exception:
    import assistant_engine as ae  # when run directly

# =============================================================================
# DATABASE FUNCTIONS
# =============================================================================

def init_database():
    """Initialize SQLite database"""
    conn = sqlite3.connect('saved_ads.db')
    cursor = conn.cursor()
    
    # Create tables table to track different collections
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ad_tables (
            table_name TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            description TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def init_generation_tables():
    """Create tables for uploads and generated images if they don't exist"""
    conn = sqlite3.connect('saved_ads.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            content_type TEXT,
            sha256 TEXT UNIQUE,
            data BLOB,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS generated_ads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            upload_id INTEGER,
            session_id INTEGER,
            variant_id TEXT,
            prompt_json TEXT,
            variant_json TEXT,
            image_data BLOB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(upload_id) REFERENCES uploads(id)
        )
    ''')

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_generated_upload ON generated_ads(upload_id)")

    # Sessions table to group a batch generation
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS session_uploads (
            session_id INTEGER,
            upload_id INTEGER,
            PRIMARY KEY (session_id, upload_id),
            FOREIGN KEY(session_id) REFERENCES sessions(id),
            FOREIGN KEY(upload_id) REFERENCES uploads(id)
        )
    ''')

    # Ensure session_id column exists on generated_ads (for upgrade path)
    try:
        cursor.execute("PRAGMA table_info(generated_ads)")
        cols = [r[1] for r in cursor.fetchall()]
        if 'session_id' not in cols:
            cursor.execute("ALTER TABLE generated_ads ADD COLUMN session_id INTEGER")
    except Exception:
        pass

    # Create index on session_id after the column is guaranteed to exist
    try:
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_generated_session ON generated_ads(session_id)")
    except Exception:
        pass
    
    conn.commit()
    conn.close()

def create_ads_table(table_name: str, description: str = ""):
    """Create a new table for saving ads"""
    conn = sqlite3.connect('saved_ads.db')
    cursor = conn.cursor()
    
    # Sanitize table name - make it unique with timestamp if needed
    base_name = "ads_" + "".join(c for c in table_name if c.isalnum() or c in ('_',)).lower()
    safe_table_name = base_name
    
    # Check if table already exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (safe_table_name,))
    if cursor.fetchone():
        # Add timestamp to make unique
        safe_table_name = f"{base_name}_{int(time.time())}"
    
    # Create the ads table with all fields
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {safe_table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad_archive_id TEXT UNIQUE,
            page_name TEXT,
            page_id TEXT,
            categories TEXT,
            start_date TEXT,
            end_date TEXT,
            is_active BOOLEAN,
            cta_text TEXT,
            cta_type TEXT,
            link_url TEXT,
            display_url TEXT,
            website_url TEXT,
            original_image_url TEXT,
            video_url TEXT,
            collation_count INTEGER,
            collation_id TEXT,
            entity_type TEXT,
            page_entity_type TEXT,
            page_profile_picture_url TEXT,
            page_profile_uri TEXT,
            state_media_run_label TEXT,
            total_active_time TEXT,
            upload_id INTEGER,
            saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT
        )
    ''')
    
    # Add to tables registry
    cursor.execute('''
        INSERT OR REPLACE INTO ad_tables (table_name, description, created_at)
        VALUES (?, ?, datetime('now'))
    ''', (safe_table_name, description))
    
    conn.commit()
    conn.close()
    
    return safe_table_name

def get_available_tables():
    """Get list of available tables"""
    conn = sqlite3.connect('saved_ads.db')
    cursor = conn.cursor()
    
    # First check if ad_tables exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ad_tables'")
    if not cursor.fetchone():
        conn.close()
        return []
    
    cursor.execute('SELECT table_name, description, created_at FROM ad_tables ORDER BY created_at DESC')
    tables = cursor.fetchall()
    
    conn.close()
    return tables

def save_ad_to_table(table_name: str, ad_data: dict, notes: str = ""):
    """Save an ad to specified table"""
    conn = sqlite3.connect('saved_ads.db')
    cursor = conn.cursor()

    try:
        # Check if ad already exists
        cursor.execute(f'''
            SELECT id FROM {table_name} WHERE ad_archive_id = ?
        ''', (ad_data.get("ad_archive_id"),))

        if cursor.fetchone():
            conn.close()
            return False, "Ad already exists in this collection"

        # Save image data to uploads table if we have an image URL
        upload_id = None
        image_url = ad_data.get("original_image_url") or ad_data.get("creative_url")
        if image_url:
            # Try to fetch and save the image
            image_bytes = _fetch_image_bytes(image_url)
            if image_bytes:
                # Generate a filename based on ad_archive_id
                filename = f"ad_{ad_data.get('ad_archive_id', 'unknown')}.png"
                upload_id = save_uploaded_image(filename, "image/png", image_bytes)
                print(f"💾 Saved image for ad {ad_data.get('ad_archive_id')} as upload_id {upload_id}")

        # Insert the ad
        cursor.execute(f'''
            INSERT INTO {table_name} (
                ad_archive_id, page_name, page_id, categories, start_date, end_date,
                is_active, cta_text, cta_type, link_url, display_url, website_url,
                original_image_url, video_url, collation_count, collation_id,
                entity_type, page_entity_type, page_profile_picture_url,
                page_profile_uri, state_media_run_label, total_active_time, upload_id, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            ad_data.get("ad_archive_id"),
            ad_data.get("page_name"),
            ad_data.get("page_id"),
            ad_data.get("categories"),
            ad_data.get("start_date"),
            ad_data.get("end_date"),
            ad_data.get("is_active"),
            ad_data.get("cta_text"),
            ad_data.get("cta_type"),
            ad_data.get("link_url"),
            ad_data.get("display_url"),
            ad_data.get("website_url"),
            ad_data.get("original_image_url"),
            ad_data.get("video_url"),
            ad_data.get("collation_count"),
            ad_data.get("collation_id"),
            ad_data.get("entity_type"),
            ad_data.get("page_entity_type"),
            ad_data.get("page_profile_picture_url"),
            ad_data.get("page_profile_uri"),
            ad_data.get("state_media_run_label"),
            ad_data.get("total_active_time"),
            upload_id,
            notes
        ))

        conn.commit()
        conn.close()
        return True, "Ad saved successfully!"
    except Exception as e:
        conn.close()
        return False, f"Error saving ad: {str(e)}"

def get_saved_ads(table_name: str):
    """Get all saved ads from a table"""
    conn = sqlite3.connect('saved_ads.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute(f'''
            SELECT * FROM {table_name} ORDER BY saved_at DESC
        ''')
        
        columns = [description[0] for description in cursor.description]
        ads = []
        
        for row in cursor.fetchall():
            ad_dict = dict(zip(columns, row))
            ads.append(ad_dict)
        
        conn.close()
        return ads
    except Exception as e:
        conn.close()
        print(f"Error getting saved ads: {e}")
        return []

def delete_saved_ad(table_name: str, ad_id: int):
    """Delete a saved ad"""
    conn = sqlite3.connect('saved_ads.db')
    cursor = conn.cursor()

    cursor.execute(f'DELETE FROM {table_name} WHERE id = ?', (ad_id,))

    conn.commit()
    conn.close()

def delete_generated_images(gen_ids: List[int]):
    """Delete generated images by their IDs"""
    if not gen_ids:
        return

    conn = sqlite3.connect('saved_ads.db')
    cursor = conn.cursor()

    # Delete from generated_ads table
    placeholders = ','.join('?' for _ in gen_ids)
    cursor.execute(f'DELETE FROM generated_ads WHERE id IN ({placeholders})', gen_ids)

    conn.commit()
    conn.close()

def delete_table(table_name: str):
    """Delete an entire table and its registry entry"""
    conn = sqlite3.connect('saved_ads.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute(f'DROP TABLE IF EXISTS {table_name}')
        cursor.execute('DELETE FROM ad_tables WHERE table_name = ?', (table_name,))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.close()
        print(f"Error deleting table: {e}")
        return False

# =============================================================================
# GENERATION STORAGE HELPERS
# =============================================================================

def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def save_uploaded_image(filename: str, content_type: str, data: bytes) -> int:
    """Save an uploaded image and return its row id. Dedup by sha256."""
    conn = sqlite3.connect('saved_ads.db')
    cursor = conn.cursor()
    hash_hex = _sha256_bytes(data)
    try:
        cursor.execute('''
            INSERT INTO uploads (filename, content_type, sha256, data)
            VALUES (?, ?, ?, ?)
        ''', (filename, content_type, hash_hex, sqlite3.Binary(data)))
        upload_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return upload_id
    except sqlite3.IntegrityError:
        cursor.execute('SELECT id FROM uploads WHERE sha256 = ?', (hash_hex,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else -1

def list_uploaded_images() -> List[Dict[str, Any]]:
    conn = sqlite3.connect('saved_ads.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, filename, content_type, uploaded_at FROM uploads ORDER BY uploaded_at DESC')
    rows = cursor.fetchall()
    conn.close()
    return [
        {"id": r[0], "filename": r[1], "content_type": r[2], "uploaded_at": r[3]}
        for r in rows
    ]

def get_upload_bytes(upload_id: int) -> Optional[bytes]:
    conn = sqlite3.connect('saved_ads.db')
    cursor = conn.cursor()
    cursor.execute('SELECT data FROM uploads WHERE id = ?', (upload_id,))
    row = cursor.fetchone()
    conn.close()
    return bytes(row[0]) if row else None

def save_generated_image(upload_id: int, variant_id: str, prompt_json: dict, variant_json: dict, image_bytes: bytes) -> int:
    conn = sqlite3.connect('saved_ads.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO generated_ads (upload_id, session_id, variant_id, prompt_json, variant_json, image_data)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        upload_id,
        st.session_state.get('current_session_id'),
        str(variant_id) if variant_id is not None else None,
        json.dumps(prompt_json, ensure_ascii=False),
        json.dumps(variant_json, ensure_ascii=False),
        sqlite3.Binary(image_bytes)
    ))
    rowid = cursor.lastrowid
    conn.commit()
    conn.close()
    return rowid

def list_generated_for_upload(upload_id: int) -> List[Dict[str, Any]]:
    conn = sqlite3.connect('saved_ads.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, variant_id, created_at FROM generated_ads
        WHERE upload_id = ? ORDER BY created_at DESC
    ''', (upload_id,))
    rows = cursor.fetchall()
    conn.close()
    return [
        {"id": r[0], "variant_id": r[1], "created_at": r[2]}
        for r in rows
    ]

def get_generated_image_bytes(gen_id: int) -> Optional[bytes]:
    conn = sqlite3.connect('saved_ads.db')
    cursor = conn.cursor()
    cursor.execute('SELECT image_data FROM generated_ads WHERE id = ?', (gen_id,))
    row = cursor.fetchone()
    conn.close()
    return bytes(row[0]) if row else None

def create_session(source: str, note: str = "") -> int:
    conn = sqlite3.connect('saved_ads.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO sessions (source, note) VALUES (?, ?)', (source, note))
    sid = cursor.lastrowid
    conn.commit()
    conn.close()
    return sid

def link_session_uploads(session_id: int, upload_ids: List[int]):
    conn = sqlite3.connect('saved_ads.db')
    cursor = conn.cursor()
    for uid in upload_ids:
        cursor.execute('INSERT OR IGNORE INTO session_uploads (session_id, upload_id) VALUES (?, ?)', (session_id, uid))
    conn.commit()
    conn.close()

def list_session_uploads(session_id: int) -> List[int]:
    conn = sqlite3.connect('saved_ads.db')
    cursor = conn.cursor()
    cursor.execute('SELECT upload_id FROM session_uploads WHERE session_id = ?', (session_id,))
    rows = [r[0] for r in cursor.fetchall()]
    conn.close()
    return rows

def list_sessions() -> List[Dict[str, Any]]:
    conn = sqlite3.connect('saved_ads.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, source, note, created_at FROM sessions ORDER BY created_at DESC, id DESC')
    rows = cursor.fetchall()
    conn.close()
    return [
        {"id": r[0], "source": r[1], "note": r[2], "created_at": r[3]}
        for r in rows
    ]

def list_generated_for_session(session_id: int) -> List[Dict[str, Any]]:
    conn = sqlite3.connect('saved_ads.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, upload_id, variant_id, created_at FROM generated_ads WHERE session_id = ? ORDER BY created_at DESC, id DESC', (session_id,))
    rows = cursor.fetchall()
    conn.close()
    return [
        {"id": r[0], "upload_id": r[1], "variant_id": r[2], "created_at": r[3]}
        for r in rows
    ]

def list_generated_for_collection(table_name: str) -> List[Dict[str, Any]]:
    """Get all generated images for a collection by finding sessions with matching source"""
    conn = sqlite3.connect('saved_ads.db')
    cursor = conn.cursor()

    # Find sessions that were created from this collection
    cursor.execute("SELECT id FROM sessions WHERE source = ?", (f"collection:{table_name}",))
    session_ids = [r[0] for r in cursor.fetchall()]

    if not session_ids:
        conn.close()
        return []

    # Get all generated images from these sessions
    placeholders = ','.join('?' for _ in session_ids)
    cursor.execute(f'SELECT id, session_id, upload_id, variant_id, created_at FROM generated_ads WHERE session_id IN ({placeholders}) ORDER BY created_at DESC, id DESC', session_ids)
    rows = cursor.fetchall()
    conn.close()

    return [
        {"id": r[0], "session_id": r[1], "upload_id": r[2], "variant_id": r[3], "created_at": r[4]}
        for r in rows
    ]

def get_upload_meta(upload_id: int) -> Optional[Dict[str, Any]]:
    conn = sqlite3.connect('saved_ads.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, filename, content_type, uploaded_at FROM uploads WHERE id = ?', (upload_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {"id": row[0], "filename": row[1], "content_type": row[2], "uploaded_at": row[3]}

# =============================================================================
# DATE FILTERING HELPER
# =============================================================================

def is_date_in_range(date_str: str, start_date: date, end_date: date) -> bool:
    """Check if date falls within selected date range"""
    if not date_str:
        return True
    
    try:
        if 'T' in date_str:
            ad_date = datetime.fromisoformat(date_str.replace('Z', '+00:00')).date()
        else:
            ad_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        return start_date <= ad_date <= end_date
    except Exception:
        return True

# =============================================================================
# IMAGE EXTRACTION LOGIC
# =============================================================================

def _get_snapshot_dict(item: dict) -> dict:
    """Extract snapshot JSON from API response"""
    snap = item.get("snapshot")
    if isinstance(snap, str):
        try:
            snap = json.loads(snap)
        except Exception:
            snap = {}
    if not isinstance(snap, dict):
        snap = {}
    return snap

def get_original_image_url(item: dict) -> str | None:
    """Extract image URL using comprehensive logic"""
    snap = _get_snapshot_dict(item)

    # Try multiple sources for images
    imgs = snap.get("images")
    if isinstance(imgs, dict):
        imgs = [imgs]
    elif not isinstance(imgs, (list, tuple)):
        imgs = []

    # Look through image objects
    for im in imgs:
        if not isinstance(im, dict):
            continue
        # Try multiple keys in order of preference
        for k in ("original_image_url", "original_picture_url", "original_picture", "resized_image_url",
                  "resized_picture_url", "url", "src", "uri", "secure_url"):
            v = im.get(k)
            if v and isinstance(v, str) and v.strip():
                return v.strip()

    # Fallback: look in other places in the snapshot
    fallback_keys = ["image_url", "picture_url", "picture", "thumbnail_url", "thumbnail",
                    "photo_url", "media_url", "creative_url"]

    for key in fallback_keys:
        v = snap.get(key)
        if v and isinstance(v, str) and v.strip():
            return v.strip()

    # Last resort: look at top level of item
    top_level_keys = ["original_image_url", "image_url", "imageUrl", "picture", "thumbnailUrl", "creative_url"]
    for key in top_level_keys:
        v = item.get(key)
        if v and isinstance(v, str) and v.strip():
            return v.strip()

    return None

def extract_selected_fields(item: dict) -> dict:
    """Extract fields using original code logic"""
    snap = _get_snapshot_dict(item)
    
    card0 = None
    cards = snap.get("cards")
    if isinstance(cards, list) and cards:
        if isinstance(cards[0], dict):
            card0 = cards[0]
    elif isinstance(cards, dict):
        card0 = cards
    
    pgcat0 = None
    page_categories = snap.get("page_categories")
    if isinstance(page_categories, list) and page_categories:
        if isinstance(page_categories[0], dict):
            pgcat0 = page_categories[0]
    elif isinstance(page_categories, dict):
        pgcat0 = page_categories
    
    link_url = snap.get("link_url")
    if not link_url and isinstance(card0, dict):
        link_url = card0.get("link_url")
    
    display_url = snap.get("caption")
    website_url = snap.get("link_url") or snap.get("website") or snap.get("url")
    
    categories = item.get("categories")
    if isinstance(categories, (list, tuple)):
        categories_disp = ", ".join(str(c) for c in categories)
    else:
        categories_disp = categories
    
    image_url = get_original_image_url(item)
    if not image_url:
        img_keys = ["imageUrl", "image_url", "thumbnailUrl", "thumbnail_url", "image"]
        for k in img_keys:
            if item.get(k):
                image_url = item[k]
                break
    
    video_url = None
    videos = snap.get("videos")
    if isinstance(videos, dict):
        videos = [videos]
    elif not isinstance(videos, (list, tuple)):
        videos = []
    
    for vid in videos:
        if not isinstance(vid, dict):
            continue
        for k in ("video_hd_url", "video_sd_url", "video_preview_url", "url", "src"):
            v = vid.get(k)
            if v:
                video_url = v
                break
        if video_url:
            break
    
    if not video_url:
        vid_keys = ["videoUrl", "video_url", "video", "video_hd_url", "video_sd_url"]
        for k in vid_keys:
            if item.get(k):
                video_url = item[k]
                break
            if snap.get(k):
                video_url = snap[k]
                break
    
    return {
        "ad_archive_id": item.get("ad_archive_id") or item.get("adId"),
        "categories": categories_disp,
        "collation_count": item.get("collation_count"),
        "collation_id": item.get("collation_id"),
        "start_date": item.get("start_date") or item.get("startDate"),
        "end_date": item.get("end_date") or item.get("endDate"),
        "entity_type": item.get("entity_type"),
        "is_active": item.get("is_active"),
        "page_id": item.get("page_id") or item.get("pageId"),
        "page_name": item.get("page_name") or item.get("pageName"),
        "cta_text": (card0.get("cta_text") if isinstance(card0, dict) else None) or snap.get("cta_text"),
        "cta_type": (card0.get("cta_type") if isinstance(card0, dict) else None) or snap.get("cta_type"),
        "link_url": link_url,
        "display_url": display_url,
        "website_url": website_url,
        "page_entity_type": (pgcat0.get("page_entity_type") if isinstance(pgcat0, dict) else None) or item.get("page_entity_type"),
        "page_profile_picture_url": item.get("page_profile_picture_url") or snap.get("page_profile_picture_url"),
        "page_profile_uri": item.get("page_profile_uri") or snap.get("page_profile_uri"),
        "state_media_run_label": item.get("state_media_run_label"),
        "total_active_time": item.get("total_active_time"),
        "original_image_url": image_url,
        "video_url": video_url,
    }

# =============================================================================
# SCRAPING FUNCTION
# =============================================================================

def run_facebook_ads_scrape(
    apify_token: str,
    domain: str,
    count: int = 10,
    country: str = "US",
    exact_phrase: bool = False,
    active_status: str = "active",
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[Dict[str, Any]]:
    """Run domain search via Apify"""
    
    if exact_phrase:
        domain_query = f'"{domain.strip()}"'
        search_type = "keyword_exact_phrase"
    else:
        domain_query = domain.strip()
        search_type = "keyword_unordered"
    
    domain_encoded = quote_plus(domain_query)
    
    url = (
        f"https://www.facebook.com/ads/library/?"
        f"active_status={active_status}&"
        f"ad_type=all&"
        f"country={country.upper()}&"
        f"is_targeted_country=false&"
        f"media_type=all&"
        f"q={domain_encoded}&"
        f"search_type={search_type}"
    )
    
    if start_date and end_date:
        url += f"&start_date[min]={start_date.strftime('%Y-%m-%d')}"
        url += f"&start_date[max]={end_date.strftime('%Y-%m-%d')}"
    
    client = ApifyClient(apify_token)
    
    run_input = {
        "urls": [{"url": url, "method": "GET"}],
        "count": int(count),
        "scrapeAdDetails": True,
        "scrapePageAds.activeStatus": active_status,
        "period": ""
    }
    
    try:
        run = client.actor("curious_coder/facebook-ads-library-scraper").call(run_input=run_input)
        dataset_id = run.get("defaultDatasetId")
        if not dataset_id:
            raise Exception("No dataset ID returned from Apify")
        
        items = list(client.dataset(dataset_id).iterate_items())
        
        processed_items = []
        for item in items:
            processed_item = extract_selected_fields(item)

            if start_date and end_date:
                start_date_str = processed_item.get("start_date")
                if start_date_str and not is_date_in_range(start_date_str, start_date, end_date):
                    continue

            # Get creative URLs for this ad (using full Apify item data + fallback scraping)
            ad_archive_id = processed_item.get("ad_archive_id")
            if ad_archive_id:
                creative_found, creative_urls = get_ad_creative_urls_with_fallback(item, ad_archive_id, apify_token, domain)
                processed_item["creative_found"] = creative_found
                processed_item["creative_urls"] = creative_urls
                processed_item["creative_url"] = creative_urls[0] if creative_urls else None

                # Debug logging
                if creative_found and creative_urls:
                    print(f"🎨 Ad {ad_archive_id} ({domain}): Found {len(creative_urls)} creative URLs")
                    print(f"   Display URL set to: {creative_urls[0][:100]}...")
                elif creative_found is False:
                    print(f"❌ Ad {ad_archive_id} ({domain}): No creative URLs found")
                else:
                    print(f"⚠️ Ad {ad_archive_id} ({domain}): creative_found is None")

            processed_items.append(processed_item)
        
        return processed_items
        
    except Exception as e:
        st.error(f"Error running scrape: {e}")
        return []

# =============================================================================
# DISPLAY FUNCTIONS
# =============================================================================

def display_ad_card(ad, index, show_save_button=True):
    """Display ad card in modern grid layout"""
    page_name = ad.get("page_name") or "Unknown Page"
    ad_id = ad.get("ad_archive_id") or f"ad_{index}"
    is_active = ad.get("is_active")
    cta_text = ad.get("cta_text")
    start_date = ad.get("start_date")
    image_url = ad.get("original_image_url") or ad.get("creative_url")
    video_url = ad.get("video_url")
    display_url = ad.get("display_url")

    with st.container():
        # Save button
        if show_save_button:
            if st.button(f"💾 Save", key=f"save_btn_{ad_id}_{index}", help="Save this ad"):
                st.session_state.save_modal_ad = ad
                st.rerun()

        # Display media
        if video_url:
            try:
                st.video(video_url)
            except:
                if image_url:
                    try:
                        st.image(image_url, width='stretch')
                    except Exception as e:
                        st.info(f"📹 Video failed, image also failed: {str(e)[:50]}...")
                else:
                    st.info("📹 Media not available")
        elif image_url:
            try:
                # Debug: Show what URL we're trying to display
                print(f"🎯 Displaying image for ad {ad_id}: {image_url[:100]}...")
                st.image(image_url, width='stretch')
                print(f"✅ Image displayed successfully for ad {ad_id}")
            except Exception as e:
                print(f"❌ Image display failed for ad {ad_id}: {str(e)}")
                st.info(f"🖼️ Image not available: {str(e)[:50]}...")
                # Debug: Show additional info
                if ad.get("creative_found"):
                    st.write(f"Found {len(ad.get('creative_urls', []))} creative URLs")
                    if ad.get("creative_urls"):
                        st.write(f"Best URL: {ad['creative_urls'][0][:100]}...")
        else:
            st.info("No media available")
            # Debug: Show extraction status
            if ad.get("creative_found") is False:
                st.write("No creative images found")
            elif ad.get("creative_found"):
                st.write(f"Creative found but no display URL set")

        # Card info
        st.markdown(f"**{page_name}**")
        if start_date:
            st.caption(f"📅 {start_date}")
        if is_active is not None:
            st.caption(f"{'🟢 Active' if is_active else '🔴 Inactive'}")
        if display_url:
            st.caption(f"🔗 {display_url}")
        if cta_text:
            st.info(f"CTA: {cta_text}")

        # Details expander
        with st.expander("View Details"):
            if ad.get('ad_archive_id'):
                fb_url = f"https://www.facebook.com/ads/library/?id={ad['ad_archive_id']}"
                st.markdown(f"[View on Facebook]({fb_url})")

            col1, col2 = st.columns(2)
            with col1:
                if ad.get('page_id'):
                    st.write(f"**Page ID:** {ad['page_id']}")
                if ad.get('categories'):
                    st.write(f"**Categories:** {ad['categories']}")
                if ad.get('cta_type'):
                    st.write(f"**CTA Type:** {ad['cta_type']}")
                if ad.get('website_url'):
                    st.write(f"**Website:** {ad['website_url']}")

            with col2:
                if ad.get('end_date'):
                    st.write(f"**End Date:** {ad['end_date']}")
                if ad.get('total_active_time'):
                    st.write(f"**Active Time:** {ad['total_active_time']}")
                if ad.get('collation_count'):
                    st.write(f"**Similar Ads:** {ad['collation_count']}")
                if ad.get('entity_type'):
                    st.write(f"**Entity Type:** {ad['entity_type']}")

                # Creative availability status
                creative_found = ad.get('creative_found', False)
                creative_urls = ad.get('creative_urls', [])
                if creative_found and creative_urls:
                    st.success(f"✅ Creative available: {len(creative_urls)} image(s) found")
                    if len(creative_urls) > 1:
                        st.info(f"📸 Multiple creatives available ({len(creative_urls)} total)")
                elif creative_found is False:
                    st.warning("❌ No creative images found")


def display_saved_ad_card(ad, index, show_save_button=True):
    """Display saved ad card with stored image data"""
    page_name = ad.get("page_name") or "Unknown Page"
    ad_id = ad.get("ad_archive_id") or f"ad_{index}"
    is_active = ad.get("is_active")
    cta_text = ad.get("cta_text")
    start_date = ad.get("start_date")
    display_url = ad.get("display_url")
    upload_id = ad.get("upload_id")

    with st.container():
        # Display saved image from uploads table
        if upload_id:
            try:
                img_bytes = get_upload_bytes(upload_id)
                if img_bytes:
                    st.image(img_bytes, width='stretch')
                else:
                    st.info("🖼️ Saved image not found")
            except Exception as e:
                st.info(f"🖼️ Error loading saved image: {str(e)[:50]}...")
        else:
            # Fallback to URL if no saved image
            image_url = ad.get("original_image_url") or ad.get("creative_url")
            if image_url:
                try:
                    st.image(image_url, width='stretch')
                except Exception as e:
                    st.info(f"🖼️ Image not available: {str(e)[:50]}...")
            else:
                st.info("🖼️ No image available")

        # Card info
        st.markdown(f"**{page_name}**")
        if start_date:
            st.caption(f"📅 {start_date}")
        if is_active is not None:
            st.caption(f"{'🟢 Active' if is_active else '🔴 Inactive'}")
        if display_url:
            st.caption(f"🔗 {display_url}")
        if cta_text:
            st.info(f"CTA: {cta_text}")

        # Details expander
        with st.expander("View Details"):
            if ad.get('ad_archive_id'):
                fb_url = f"https://www.facebook.com/ads/library/?id={ad['ad_archive_id']}"
                st.markdown(f"[View on Facebook]({fb_url})")

            col1, col2 = st.columns(2)
            with col1:
                if ad.get('page_id'):
                    st.write(f"**Page ID:** {ad['page_id']}")
                if ad.get('categories'):
                    st.write(f"**Categories:** {ad['categories']}")
                if ad.get('cta_type'):
                    st.write(f"**CTA Type:** {ad['cta_type']}")
                if ad.get('website_url'):
                    st.write(f"**Website:** {ad['website_url']}")

            with col2:
                if ad.get('end_date'):
                    st.write(f"**End Date:** {ad['end_date']}")
                if ad.get('total_active_time'):
                    st.write(f"**Active Time:** {ad['total_active_time']}")
                if ad.get('collation_count'):
                    st.write(f"**Similar Ads:** {ad['collation_count']}")
                if ad.get('entity_type'):
                    st.write(f"**Entity Type:** {ad['entity_type']}")

# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="Facebook Ads Domain Search", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main { padding: 0rem 1rem; }
    .stButton > button {
        width: 100%;
        background: #1877f2;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        font-weight: 500;
    }
    .stButton > button:hover { background: #166fe5; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .generate-sticky { position: sticky; top: 8px; z-index: 100; display: flex; justify-content: flex-end; background: var(--background-color, rgba(255,255,255,0.6)); padding: 4px 0; }
    .generate-sticky .stButton>button { width: auto; padding: 0.6rem 1.2rem; box-shadow: 0 6px 16px rgba(24,119,242,0.35); }
    .danger-zone {border:1px solid #e55353; padding:12px; border-radius:8px; background: #fff5f5;}
    </style>
""", unsafe_allow_html=True)

# Initialize database
init_database()
init_generation_tables()

# Initialize session state
if 'current_ads' not in st.session_state:
    st.session_state.current_ads = []
if 'save_modal_ad' not in st.session_state:
    st.session_state.save_modal_ad = None
if 'selected_table' not in st.session_state:
    st.session_state.selected_table = None

# =============================================================================
# MAIN APP
# =============================================================================

def main():
    """Main Streamlit app"""
    
    # Handle save modal
    if st.session_state.save_modal_ad:
        with st.sidebar:
            st.markdown("### 💾 Save Ad to Collection")
            st.markdown("---")
            
            ad_to_save = st.session_state.save_modal_ad
            st.info(f"Saving: {ad_to_save.get('page_name', 'Unknown')}")
            
            available_tables = get_available_tables()
            
            save_option = st.radio(
                "Choose option:",
                ["Create New Collection", "Add to Existing"] if available_tables else ["Create New Collection"]
            )
            
            selected_table = None
            
            if save_option == "Create New Collection":
                new_name = st.text_input("Collection Name:", placeholder="e.g., Competitor Ads")
                new_desc = st.text_input("Description:", placeholder="Optional description")
                notes = st.text_area("Notes (optional):", placeholder="Add notes about this ad...")
                
                if st.button("Create & Save", type="primary", width='stretch'):
                    if new_name:
                        selected_table = create_ads_table(new_name, new_desc)
                        success, msg = save_ad_to_table(selected_table, ad_to_save, notes)
                        if success:
                            st.success(msg)
                            st.session_state.save_modal_ad = None
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(msg)
                    else:
                        st.error("Please enter a collection name")
            
            else:  # Add to Existing
                table_options = [f"{desc if desc else name.replace('ads_', '').title()}" 
                                for name, desc, _ in available_tables]
                selected_idx = st.selectbox("Select Collection:", range(len(table_options)), 
                                           format_func=lambda x: table_options[x])
                selected_table = available_tables[selected_idx][0]
                
                notes = st.text_area("Notes (optional):", placeholder="Add notes about this ad...")
                
                if st.button("Save to Collection", type="primary", width='stretch'):
                    success, msg = save_ad_to_table(selected_table, ad_to_save, notes)
                    if success:
                        st.success(msg)
                        st.session_state.save_modal_ad = None
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(msg)
            
            if st.button("Cancel", width='stretch'):
                st.session_state.save_modal_ad = None
                st.rerun()
            
            st.markdown("---")
            return  # Don't show navigation when save modal is open
    
    # Handle bulk save modal
    if st.session_state.get('pending_save_ads'):
        with st.sidebar:
            st.markdown("### 💾 Bulk Save Selected")
            st.markdown("---")
            num_sel = len(st.session_state.pending_save_ads)
            st.info(f"You are saving {num_sel} ad(s)")

            available_tables = get_available_tables()
            bulk_option = st.radio(
                "Save to:",
                ["Create New Collection", "Add to Existing"] if available_tables else ["Create New Collection"],
                key="bulk_save_option"
            )

            if bulk_option == "Create New Collection":
                bname = st.text_input("Collection Name", key="bulk_new_name", placeholder="e.g., Competitors Set A")
                bdesc = st.text_input("Description (optional)", key="bulk_new_desc")
                if st.button("Create & Save All", type="primary", width='stretch', key="bulk_create_and_save"):
                    if bname:
                        tbl = create_ads_table(bname, bdesc)
                        ok = 0
                        failed = 0
                        for ad in st.session_state.pending_save_ads:
                            success, _ = save_ad_to_table(tbl, ad)
                            if success:
                                ok += 1
                            else:
                                failed += 1
                        st.success(f"Saved {ok} of {num_sel} ad(s) to {tbl}")
                        if failed:
                            st.warning(f"{failed} ad(s) were duplicates or failed to save.")
                        st.session_state.pending_save_ads = None
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Please provide a collection name")
            else:
                options = available_tables
                idx = st.selectbox(
                    "Choose Collection",
                    list(range(len(options))),
                    format_func=lambda i: options[i][0],
                    key="bulk_existing_idx"
                )
                tbl = options[idx][0]
                if st.button("Save All to Selected Collection", type="primary", width='stretch', key="bulk_save_to_existing"):
                    ok = 0
                    failed = 0
                    for ad in st.session_state.pending_save_ads:
                        success, _ = save_ad_to_table(tbl, ad)
                        if success:
                            ok += 1
                        else:
                            failed += 1
                    st.success(f"Saved {ok} of {num_sel} ad(s) to {tbl}")
                    if failed:
                        st.warning(f"{failed} ad(s) were duplicates or failed to save.")
                    st.session_state.pending_save_ads = None
                    time.sleep(1)
                    st.rerun()

            if st.button("Cancel", width='stretch', key="bulk_cancel"):
                st.session_state.pending_save_ads = None
                st.rerun()

        return  # Stop normal rendering while bulk modal is open
    
    # Sidebar navigation
    with st.sidebar:
        st.title("🧰 Pixel Pay Ad Toolkit")
        st.markdown("---")
        # Gemini API key is now loaded from environment variable
        
        tab = st.radio("Navigation", ["Search", "External Ads Generator", "Saved Collections", "Generated Ads"])
        
        if tab == "Search":
            st.markdown("### Search Parameters")
            
            apify_token = st.text_input(
                "Apify API Token", 
                type="password",
                placeholder="Enter your Apify API token",
                help="Get your token from https://apify.com"
            )
            
            domain = st.text_input(
                "Domain URL", 
                placeholder="example.com",
                help="Enter domain without http:// or https://"
            )
            
            exact_phrase = st.checkbox(
                "Exact Phrase Match",
                value=False,
                help='Search for exact domain phrase'
            )
            
            country = st.selectbox(
                "Target Country",
                options=[c[0] for c in COUNTRIES],
                index=[c[0] for c in COUNTRIES].index("US") if any(c[0] == "US" for c in COUNTRIES) else 0,
                format_func=lambda code: f"{code} - {COUNTRY_NAME_BY_CODE.get(code, code)}"
            )
            
            active_status = st.selectbox(
                "Ad Status",
                options=["active", "inactive", "all"],
                format_func=lambda x: x.capitalize()
            )
            
            count = st.slider(
                "Number of Ads", 
                min_value=1, 
                max_value=100, 
                value=10
            )
            
            st.markdown("### Date Filter (Optional)")
            
            use_date_filter = st.checkbox("Enable Date Filtering", value=False)
            
            if use_date_filter:
                today = date.today()
                six_months_ago = today - timedelta(days=180)
                
                col1, col2 = st.columns(2)
                with col1:
                    start_date = st.date_input(
                        "From",
                        value=six_months_ago,
                        min_value=six_months_ago,
                        max_value=today
                    )
                
                with col2:
                    end_date = st.date_input(
                        "To", 
                        value=today,
                        min_value=six_months_ago,
                        max_value=today
                    )
            else:
                start_date = None
                end_date = None
            
            st.markdown("---")
            search_button = st.button("🚀 Search Ads", type="primary", width='stretch')
        
        elif tab == "Saved Collections":  # Saved Collections navigation
            st.markdown("### 📁 Your Collections")
            available_tables = get_available_tables()
            
            if not available_tables:
                st.info("No saved collections yet")
            else:
                for table_name, desc, created in available_tables:
                    if st.button(
                        f"📁 {desc if desc else table_name.replace('ads_', '').title()}",
                        key=f"nav_{table_name}",
                        width='stretch'
                    ):
                        st.session_state.selected_table = table_name
                    st.caption(f"Created: {created[:10] if created else 'Unknown'}")
            
            search_button = False
        elif tab == "Generated Ads":
            st.markdown("### Generate with OpenAI Assistant")
            st.info("Using your Ad Creative Assistant for prompts and Gemini for image generation.")
            size = st.selectbox("Image Size", ["512x512", "768x768", "1024x1024"], index=2)
            st.caption("Upload images in the main panel, select them, then click Generate ADS.")
            st.markdown("---")
            with st.expander("Danger Zone: Clear Database"):
                st.markdown('<div class="danger-zone">', unsafe_allow_html=True)
                st.write("This will permanently remove all uploads, sessions, and generated images.")
                col1, col2 = st.columns([1,1])
                with col1:
                    confirm = st.toggle("I understand the risk", key="clear_db_confirm_toggle")
                with col2:
                    pass
                phrase = st.text_input("Type CLEAR THE DATABASE to confirm", key="clear_db_phrase", placeholder="CLEAR THE DATABASE")
                disabled = not (confirm and phrase.strip().upper() == "CLEAR THE DATABASE")
                if st.button("Clear Database", key="clear_db_btn", disabled=disabled):
                    try:
                        import sqlite3 as _sql
                        conn = _sql.connect('saved_ads.db')
                        cur = conn.cursor()
                        cur.execute('DELETE FROM generated_ads')
                        cur.execute('DELETE FROM session_uploads')
                        cur.execute('DELETE FROM sessions')
                        cur.execute('DELETE FROM uploads')
                        conn.commit()
                        conn.close()
                        st.success("Database cleared.")
                    except Exception as e:
                        st.error(f"Failed to clear DB: {e}")
                st.markdown('</div>', unsafe_allow_html=True)
            search_button = False
    
    # Main content area
    if tab == "Search":
        st.title("🔍 Facebook Ads Library Search")
        st.markdown("Search and analyze Facebook ads by domain")
        
        if search_button:
            if not apify_token:
                st.error("Please enter your Apify API token")
            elif not domain:
                st.error("Please enter a domain URL")
            elif use_date_filter and start_date > end_date:
                st.error("Start date must be before end date")
            else:
                # Show search info
                search_info = f"Searching for **{domain}**"
                if exact_phrase:
                    search_info += " (exact match)"
                search_info += f" • {active_status.capitalize()} ads • {country}"
                if use_date_filter:
                    search_info += f" • {start_date} to {end_date}"
                
                st.info(search_info)
                
                # Run search
                with st.spinner("Searching Facebook Ads Library..."):
                    ads = run_facebook_ads_scrape(
                        apify_token=apify_token, 
                        domain=domain, 
                        count=count, 
                        country=country, 
                        exact_phrase=exact_phrase,
                        active_status=active_status,
                        start_date=start_date if use_date_filter else None,
                        end_date=end_date if use_date_filter else None
                    )
                    st.session_state.current_ads = ads
                
                if ads:
                    st.success(f"Found {len(ads)} ads")
                    
                    # Display options
                    col1, col2 = st.columns([2, 1])
                    with col2:
                        view_mode = st.selectbox("View", ["Grid", "List"])
                    
                    st.markdown("---")
                    
                    # Sticky action bar first (always at top)
                    st.markdown('<div class="generate-sticky">', unsafe_allow_html=True)
                    colA, colB = st.columns([1,1])
                    with colA:
                        save_click = st.button("Save Selected to Collection", key="save_selected_btn_top")
                    with colB:
                        generate_direct = st.button("Generate ADS for Selected", key="generate_from_search_btn_persist")
                    st.markdown('</div>', unsafe_allow_html=True)

                    # Dedicated top status area (above cards)
                    status_slot = st.empty()

                    # Render cards with checkboxes
                    selected_from_search = []
                    if view_mode == "Grid":
                        cols = st.columns(3)
                        for i, ad in enumerate(ads):
                            with cols[i % 3]:
                                display_ad_card(ad, i, True)
                                if st.checkbox("Select", key=f"sel_search_{i}"):
                                    selected_from_search.append((i, ad))
                    else:
                        for i, ad in enumerate(ads):
                            display_ad_card(ad, i, True)
                            if st.checkbox("Select", key=f"sel_search_{i}"):
                                selected_from_search.append((i, ad))
                            if i < len(ads) - 1:
                                st.markdown("---")

                    # Save selected flow
                    if save_click:
                        if not selected_from_search:
                            st.warning("Select at least one ad to save.")
                        else:
                            # Store selected ads in session and open sidebar modal
                            st.session_state.pending_save_ads = [ad for _, ad in selected_from_search]
                            st.rerun()

                else:
                    st.warning("No ads found for this search")
                    st.info("""
                        **Try adjusting your search:**
                        • Remove exact phrase matching
                        • Change the ad status filter
                        • Expand the date range
                        • Try a different domain
                    """)
        else:
            # Persist search results with selection checkboxes across reruns
            ads = st.session_state.current_ads
            if ads:
                st.success(f"Found {len(ads)} ads")

                col1, col2 = st.columns([2, 1])
                with col2:
                    view_mode = st.selectbox("View", ["Grid", "List"], key="search_view_mode_persist")

                st.markdown("---")

                # Sticky action bar first
                st.markdown('<div class="generate-sticky">', unsafe_allow_html=True)
                colA, colB = st.columns([1,1])
                with colA:
                    save_click_persist = st.button("Save Selected to Collection", key="save_selected_btn_persist")
                with colB:
                    generate_direct_persist = st.button("Generate ADS for Selected", key="generate_from_search_btn_persist")
                desired_count = st.slider("Number of images to generate", min_value=1, max_value=10, value=5, key="search_desired_count")
                st.markdown('</div>', unsafe_allow_html=True)

                # Dedicated top status area (above cards)
                status_slot = st.empty()

                # Render cards with checkboxes
                selected_from_search = []
                if view_mode == "Grid":
                    cols = st.columns(3)
                    for i, ad in enumerate(ads):
                        with cols[i % 3]:
                            display_ad_card(ad, i, True)
                            if st.checkbox("Select", key=f"sel_search_{i}"):
                                selected_from_search.append((i, ad))
                else:
                    for i, ad in enumerate(ads):
                        display_ad_card(ad, i, True)
                        if st.checkbox("Select", key=f"sel_search_{i}"):
                            selected_from_search.append((i, ad))
                        if i < len(ads) - 1:
                            st.markdown("---")

                # Save selected flow (persisted branch)
                if save_click_persist:
                    if not selected_from_search:
                        st.warning("Select at least one ad to save.")
                    else:
                        st.session_state.pending_save_ads = [ad for _, ad in selected_from_search]
                        st.rerun()

                if generate_direct_persist and selected_from_search:
                    # Multi-step status (top)
                    status_obj = None
                    try:
                        status_obj = status_slot.status("Starting…", expanded=True)
                        status_obj.update(label="Fetching selected images…", state="running")
                    except Exception:
                        status_slot.markdown("**Starting…**\n\n- Fetching selected images…")
                    grouped_images = []
                    upload_ids = []
                    for i, ad in selected_from_search:
                        url = ad.get("original_image_url") or ad.get("creative_url")
                        if not url:
                            st.warning(f"Selected ad {i+1} has no image available; skipping.")
                            continue
                        img_bytes = _fetch_image_bytes(url)
                        if not img_bytes:
                            st.error(f"Failed to fetch selected ad {i+1} image (network/CDN). Skipping.")
                            continue
                        upload_id = save_uploaded_image(f"search_{i}.png", "image/png", img_bytes)
                        grouped_images.append((f"selected_{i}", img_bytes))
                        upload_ids.append(upload_id)
                    if grouped_images:
                        try:
                            if status_obj:
                                status_obj.update(label="Analyzing with Assistant…", state="running")
                            sid = create_session(source="search", note=f"{len(grouped_images)} images")
                            st.session_state.current_session_id = sid
                            link_session_uploads(sid, upload_ids)
                            json_prompt, variants_json = ae.analyze_images(None, None, grouped_images, desired_count=desired_count)
                            # Handle new direct prompt format
                            variants = None
                            if isinstance(variants_json, dict):
                                if "vu_engine_variants" in variants_json:
                                    # Legacy format
                                    variants = variants_json["vu_engine_variants"]
                                elif "prompts" in variants_json:
                                    # New direct format - convert to expected structure
                                    prompts = variants_json["prompts"]
                                    variants = [{"id": f"var_{i+1}", "prompt": prompt} for i, prompt in enumerate(prompts)]
                            if not variants:
                                if status_obj:
                                    status_obj.update(label="No variants returned by assistant.", state="error")
                            else:
                                if status_obj:
                                    status_obj.update(label="Generating all variants…", state="running")

                                # VU Engine: Show detailed prompts prominently
                                st.markdown("### 🎨 VU Engine Generated Prompts")
                                st.info("📝 These prompts are designed to create images very similar to your reference, following VU Engine rules (±5% creativity only)")

                                for i, v in enumerate(variants):
                                    vid = v.get('id') or f"var_{i+1}"
                                    prompt_text = ae.build_prompt_text(json_prompt, v)

                                    # Display prompt prominently
                                    st.markdown(f"**🎯 VU Engine Prompt {i+1} ({vid}):**")
                                    st.text_area(
                                        f"Prompt {i+1} - Click to expand",
                                        value=prompt_text,
                                        height=120,
                                        key=f"prompt_display_{i}",
                                        help="This prompt will generate an image very similar to your reference following VU Engine rules"
                                    )
                                    st.markdown("---")

                                # Generate images after showing prompts
                                st.markdown("### 🚀 Generating Images...")
                                progress_bar = st.progress(0)
                                status_text = st.empty()

                                stop_all = False
                                for i, v in enumerate(variants):
                                    vid = v.get('id') or f"var_{i+1}"
                                    status_text.text(f"Generating image {i+1}/{len(variants)}...")

                                    # Prompt-only generation (no reference images passed)
                                    img_out = ae.generate_single_variant_image(
                                        os.getenv("GOOGLE_API_KEY"),
                                        json_prompt,
                                        v,
                                        size="1024x1024"
                                    )
                                    if img_out:
                                        save_generated_image(upload_ids[0], vid, json_prompt, v, img_out)
                                        st.success(f"✅ Image {i+1} created successfully!")
                                        progress_bar.progress((i+1)/len(variants))
                                    else:
                                        # If first prompt yields no image, stop all
                                        if i == 0:
                                            stop_all = True
                                            st.error("First prompt returned no image. Stopping further generations.")
                                            break

                                    time.sleep(0.5)  # Small delay for better UX

                                progress_bar.empty()
                                status_text.empty()

                                if status_obj:
                                    status_obj.update(label="Generation complete.", state="complete")
                                st.info("Go to the 'Generated Ads' tab to see originals and all generated variants for this run.")
                        except Exception as e:
                            variants = None
                            if status_obj:
                                status_obj.update(label=f"Analysis failed: {e}", state="error")
                            else:
                                status_slot.error(f"Analysis failed: {e}")
                    else:
                        variants = None


    elif tab == "External Ads Generator":
        st.title("🎨 External Ads Generator")
        st.caption("Upload multiple images, analyze them with your Assistant to extract VU Engine prompts, and generate ad variations with Gemini 2.5 Flash Image Preview.")

        uploaded_files = st.file_uploader("Upload images", type=["png","jpg","jpeg","webp"], accept_multiple_files=True, key="external_ads_uploader")
        desired_count_qt = st.slider("Number of prompts per image", min_value=1, max_value=10, value=5, key="qt_desired_count")

        # Show uploaded images preview
        if uploaded_files:
            st.markdown("### 📸 Uploaded Images")
            cols = st.columns(min(len(uploaded_files), 3))
            for i, uploaded in enumerate(uploaded_files):
                with cols[i % 3]:
                    st.image(uploaded, caption=f"Image {i+1}: {uploaded.name}", width=200)

        analyze_and_generate_clicked = st.button("🎨 Analyze & Generate All Ads", type="primary", key="external_ads_analyze_generate")

        if analyze_and_generate_clicked:
            if not uploaded_files:
                st.error("Please upload at least one image first.")
            else:
                try:
                    # Prepare images for analysis
                    images_data = []
                    for uploaded in uploaded_files:
                        img_bytes = uploaded.read()
                        images_data.append((uploaded.name or f"upload_{len(images_data)}", img_bytes))

                    with st.spinner("🔍 Analyzing images with Assistant…"):
                        base_json, variants_json = ae.analyze_images(None, None, images_data, desired_count=desired_count_qt)
                        prompts = []
                        if isinstance(variants_json, dict) and "prompts" in variants_json:
                            prompts = list(variants_json.get("prompts") or [])

                        if prompts:
                            st.success(f"✅ Found {len(prompts)} prompt(s) from {len(uploaded_files)} image(s)")

                            # Create a session for this generation
                            session_note = f"External Ads Generator: {len(uploaded_files)} images → {len(prompts)} prompts"
                            session_id = create_session(source="external_ads_generator", note=session_note)

                            # Save uploaded images to database
                            upload_ids = []
                            for uploaded_name, img_bytes in images_data:
                                upload_id = save_uploaded_image(uploaded_name, "image/png", img_bytes)
                                upload_ids.append(upload_id)

                            # Link uploads to session
                            link_session_uploads(session_id, upload_ids)

                            # Set the current session ID so generated images are linked properly
                            st.session_state.current_session_id = session_id

                            st.session_state.external_ads_base = base_json
                            st.session_state.external_ads_prompts = prompts
                            st.session_state.external_ads_images = images_data
                            st.session_state.external_ads_session_id = session_id

                            # Auto-generate all images
                            st.markdown("### 🎨 Generating Ads...")
                            progress_bar = st.progress(0)
                            status_text = st.empty()

                            generated_images = []
                            size = "1024x1024"  # Default size

                            for i, prompt in enumerate(prompts):
                                status_text.text(f"Generating ad {i+1}/{len(prompts)}...")
                                progress_bar.progress((i) / len(prompts))

                                try:
                                    variant_data = {"prompt": str(prompt)}
                                    img_out = ae.generate_single_variant_image(os.getenv("GOOGLE_API_KEY"), base_json, variant_data, size=size)
                                    if img_out:
                                        # Save to database
                                        variant_id = f"external_ad_{i+1}"
                                        save_generated_image(upload_ids[0], variant_id, base_json, variant_data, img_out)
                                        generated_images.append((f"Ad {i+1}", img_out))
                                    else:
                                        # Stop if first prompt fails
                                        if i == 0:
                                            st.error("❌ First prompt returned no image. Stopping generation.")
                                            break
                                except Exception as ge:
                                    st.warning(f"⚠️ Failed to generate ad {i+1}: {str(ge)[:50]}...")

                            progress_bar.progress(1.0)
                            status_text.empty()
                            progress_bar.empty()

                            if generated_images:
                                st.success(f"🎉 Generated {len(generated_images)} ad(s)! Session #{session_id} saved.")
                                st.session_state.external_ads_generated = generated_images
                                st.info("💾 Your generated ads have been saved to the 'Generated Ads' tab for future reference!")
                            else:
                                st.error("❌ No ads could be generated.")

                        else:
                            st.warning("⚠️ No prompts returned by assistant.")

                except Exception as e:
                    st.error(f"❌ Analysis failed: {e}")

        # Show generated results
        generated_ads = st.session_state.get("external_ads_generated")
        prompts_state = st.session_state.get("external_ads_prompts")

        if generated_ads:
            st.markdown("### 🎨 Generated Ads")

            # Download All button
            col1, col2 = st.columns([1, 4])
            with col1:
                import zipfile

                zip_buffer = BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for i, (title, img_bytes) in enumerate(generated_ads):
                        # Clean filename
                        safe_name = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                        safe_name = safe_name.replace(' ', '_')
                        zip_file.writestr(f"{safe_name}_{i+1}.png", img_bytes)

                zip_buffer.seek(0)
                st.download_button(
                    label="📦 Download All",
                    data=zip_buffer.getvalue(),
                    file_name=f"external_ads_session_{st.session_state.get('external_ads_session_id', 'unknown')}.zip",
                    mime="application/zip",
                    key="download_all_external_ads"
                )

            # Display images with individual download buttons
            cols = st.columns(min(len(generated_ads), 2))
            for i, (title, img_bytes) in enumerate(generated_ads):
                with cols[i % 2]:
                    st.image(img_bytes, caption=title, use_column_width=True)
                    # Individual download button
                    safe_filename = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                    safe_filename = safe_filename.replace(' ', '_')
                    st.download_button(
                        label=f"⬇️ Download {title}",
                        data=img_bytes,
                        file_name=f"{safe_filename}_{i+1}.png",
                        mime="image/png",
                        key=f"download_external_ad_{i}"
                    )

        if prompts_state:
            st.markdown("### 📝 Generated Prompts")
            with st.expander("View All Prompts", expanded=False):
                for i, p in enumerate(prompts_state, start=1):
                    st.text_area(f"Prompt {i}", value=str(p), height=80, key=f"external_prompt_{i}")

    elif tab == "Saved Collections":  # Saved Collections tab
        st.title("💾 Saved Ad Collections")
        
        if st.session_state.selected_table:
            table_name = st.session_state.selected_table
            
            # Get table info
            available_tables = get_available_tables()
            table_info = next((t for t in available_tables if t[0] == table_name), None)
            
            if table_info:
                _, desc, created = table_info
                
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.markdown(f"### 📁 {desc if desc else table_name.replace('ads_', '').title()}")
                with col2:
                    if st.button("← Back", key="back_btn"):
                        st.session_state.selected_table = None
                        st.rerun()
                with col3:
                    if st.button("🗑️ Delete Collection", key="delete_collection"):
                        if delete_table(table_name):
                            st.success("Collection deleted!")
                            st.session_state.selected_table = None
                            time.sleep(1)
                            st.rerun()
                
                st.caption(f"Created: {created[:10] if created else 'Unknown'}")

                # Generation settings
                desired_count = st.slider("Number of variants per ad", min_value=1, max_value=10, value=5, key="collection_desired_count")

                # Controls to save/generate for the entire collection
                st.markdown('<div class="generate-sticky">', unsafe_allow_html=True)
                colX, colY = st.columns([1,1])
                with colX:
                    gen_collection = st.button("Generate ADS for Collection", key="gen_collection_btn")
                with colY:
                    save_sel_to_other = st.button("Save Selected to Another Collection", key="save_sel_other_btn")
                st.markdown('</div>', unsafe_allow_html=True)

                status_slot = st.empty()

                selected_ads = []

                # Get saved ads
                saved_ads = get_saved_ads(table_name)
                
                if saved_ads:
                    st.write(f"**{len(saved_ads)} ads in this collection**")
                    
                    # Display options
                    col1, col2 = st.columns([2, 1])
                    with col2:
                        display_mode = st.selectbox("Display", ["Compact", "Full"])
                    
                    st.markdown("---")
                    
                    # Display saved ads
                    if display_mode == "Full":
                        cols = st.columns(3)
                        for i, ad in enumerate(saved_ads):
                            with cols[i % 3]:
                                # Delete button for individual ad
                                if st.button(f"🗑️", key=f"del_ad_{ad.get('id')}_{i}", help="Delete this ad"):
                                    delete_saved_ad(table_name, ad.get('id'))
                                    st.success("Ad deleted!")
                                    st.rerun()
                                
                                # Selection checkbox
                                checked = st.checkbox("Select", key=f"sel_saved_{ad.get('id')}")
                                if checked:
                                    selected_ads.append(ad)

                                # Display the ad card with saved image
                                display_saved_ad_card(ad, f"saved_{i}", False)
                                
                                # Show notes if any
                                if ad.get('notes'):
                                    st.info(f"📝 {ad.get('notes')}")
                                
                                # Show saved date
                                if ad.get('saved_at'):
                                    st.caption(f"Saved: {ad.get('saved_at')[:19]}")
                    else:  # Compact view
                        for i, ad in enumerate(saved_ads):
                            with st.expander(f"📄 {ad.get('page_name', 'Unknown')} - {ad.get('start_date', 'Date unknown')}"):
                                col1, col2 = st.columns([3, 1])
                                
                                with col1:
                                    st.write(f"**Page:** {ad.get('page_name', 'Unknown')}")
                                    if ad.get('display_url'):
                                        st.write(f"**URL:** {ad.get('display_url')}")
                                    if ad.get('cta_text'):
                                        st.write(f"**CTA:** {ad.get('cta_text')}")
                                    st.write(f"**Status:** {'🟢 Active' if ad.get('is_active') else '🔴 Inactive'}")
                                    
                                    if ad.get('notes'):
                                        st.markdown(f"**📝 Notes:** {ad.get('notes')}")
                                    
                                    st.caption(f"Saved: {ad.get('saved_at', '')[:19]}")
                                
                                with col2:
                                    if st.button(f"🗑️ Delete", key=f"del_compact_{ad.get('id')}"):
                                        delete_saved_ad(table_name, ad.get('id'))
                                        st.success("Ad deleted!")
                                        st.rerun()
                                    
                                    # Select checkbox
                                    if st.checkbox("Select", key=f"sel_saved_compact_{ad.get('id')}"):
                                        selected_ads.append(ad)
                                    
                                    # Show saved image or fallback
                                    upload_id = ad.get('upload_id')
                                    if upload_id:
                                        img_bytes = get_upload_bytes(upload_id)
                                        if img_bytes:
                                            st.image(img_bytes, width=150)
                                        else:
                                            st.write("🖼️ Saved image not found")
                                    elif ad.get('original_image_url'):
                                        try:
                                            st.image(ad.get('original_image_url'), width=150)
                                        except:
                                            st.write("🖼️ Image not available")
                                    else:
                                        st.write("🖼️ No image")
                                
                                # View on Facebook button
                                if ad.get('ad_archive_id'):
                                    fb_url = f"https://www.facebook.com/ads/library/?id={ad.get('ad_archive_id')}"
                                    st.markdown(f"[🔗 View on Facebook]({fb_url})")
                else:
                    st.info("No ads in this collection yet. Save some ads from your search results!")

                # Display generated images for this collection
                generated_images = list_generated_for_collection(table_name)
                if generated_images:
                    st.markdown("---")
                    st.markdown("### 🎨 Generated Images")

                    # Bulk delete and download controls for generated images
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        select_all_gen = st.checkbox("Select All Generated", key=f"select_all_gen_{table_name}")
                    with col2:
                        if st.button("🗑️ Delete Selected", key=f"bulk_delete_gen_{table_name}", help="Delete selected generated images"):
                            selected_to_delete = []
                            for i, gen_img in enumerate(generated_images):
                                if st.session_state.get(f"sel_gen_{table_name}_{gen_img['id']}", False):
                                    selected_to_delete.append(gen_img['id'])

                            if selected_to_delete:
                                delete_generated_images(selected_to_delete)
                                st.success(f"Deleted {len(selected_to_delete)} generated image(s)")
                                st.rerun()
                            else:
                                st.warning("No generated images selected")
                    with col3:
                        if st.button("📥 Download All", key=f"download_all_gen_{table_name}", help="Download all generated images in this collection as ZIP"):
                            import zipfile
                            import io

                            # Create a ZIP file in memory
                            zip_buffer = io.BytesIO()
                            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                                for i, gen_img in enumerate(generated_images):
                                    img_b = get_generated_image_bytes(gen_img['id'])
                                    if img_b:
                                        filename = f"collection_{table_name}_variant_{gen_img['variant_id'] or f'var_{i+1}'}.png"
                                        zip_file.writestr(filename, img_b)

                            zip_buffer.seek(0)
                            st.download_button(
                                label="📥 Download ZIP",
                                data=zip_buffer.getvalue(),
                                file_name=f"collection_{table_name}_generated_ads.zip",
                                mime="application/zip",
                                key=f"zip_dl_{table_name}"
                            )

                    if st.button("🗑️ Delete All Generated", key=f"delete_all_gen_{table_name}", help="Delete all generated images in this collection"):
                        if st.session_state.get(f"confirm_delete_all_gen_{table_name}", False):
                            all_ids = [gen_img['id'] for gen_img in generated_images]
                            delete_generated_images(all_ids)
                            st.success(f"Deleted all {len(all_ids)} generated image(s)")
                            st.rerun()
                        else:
                            st.session_state[f"confirm_delete_all_gen_{table_name}"] = True
                            st.warning("Click again to confirm deletion of ALL generated images")

                    # Display generated images
                    cols = st.columns(3)
                    for i, gen_img in enumerate(generated_images):
                        with cols[i % 3]:
                            img_b = get_generated_image_bytes(gen_img['id']) or b""
                            if img_b:
                                # Selection checkbox
                                is_selected = st.checkbox("Select", key=f"sel_gen_{table_name}_{gen_img['id']}", value=select_all_gen)

                                cap = f"Variant {gen_img['variant_id'] or ''} • Generated {gen_img['created_at'][:19]}"
                                st.image(img_b, width='stretch', caption=cap)

                                # Action buttons
                                col_dl, col_del = st.columns(2)
                                with col_dl:
                                    st.download_button(
                                        label="📥 Download",
                                        data=img_b,
                                        file_name=f"collection_{table_name}_variant_{(gen_img['variant_id'] or 'unknown')}.png",
                                        mime="image/png",
                                        key=f"dl_gen_{table_name}_{gen_img['id']}"
                                    )
                                with col_del:
                                    if st.button("🗑️ Delete", key=f"del_gen_{table_name}_{gen_img['id']}", help="Delete this generated image"):
                                        delete_generated_images([gen_img['id']])
                                        st.success("Generated image deleted")
                                        st.rerun()

                # Save selected to another collection
                if save_sel_to_other and selected_ads:
                    st.session_state.pending_save_ads = selected_ads
                    st.rerun()

                # Generate for this collection (or selected subset)
                if gen_collection and (selected_ads or saved_ads):
                    targets = selected_ads if selected_ads else saved_ads
                    status_obj2 = status_slot.status("Starting collection generation…", expanded=True)

                    # Progress bar for loading images
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    status_text.text("Loading saved images…")
                    grouped_images = []
                    upload_ids = []
                    for i, ad in enumerate(targets):
                        progress = (i + 1) / len(targets)
                        progress_bar.progress(progress)

                        # First try to use locally saved image
                        upload_id = ad.get("upload_id")
                        img_bytes = None

                        if upload_id:
                            img_bytes = get_upload_bytes(upload_id)
                            if img_bytes:
                                grouped_images.append((f"saved_ad_{ad.get('id')}", img_bytes))
                                upload_ids.append(upload_id)
                                continue

                        # Fallback: try to fetch from URL if local image not available
                        url = ad.get("original_image_url") or ad.get("creative_url")
                        if url:
                            status_text.text(f"Fetching image {i+1}/{len(targets)} from URL…")
                            img_bytes = _fetch_image_bytes(url)
                            if img_bytes:
                                upload_id = save_uploaded_image(f"collection_{i}.png", "image/png", img_bytes)
                                grouped_images.append((f"collection_{i}", img_bytes))
                                upload_ids.append(upload_id)
                                continue

                        # If no image available, skip this ad
                        st.warning(f"No image available for ad {i+1} ({ad.get('page_name', 'Unknown')}). Skipping.")

                    progress_bar.progress(1.0)
                    status_text.empty()

                    if grouped_images:
                        try:
                            # Progress bar for analysis
                            analysis_progress = st.progress(0)
                            analysis_status = st.empty()
                            analysis_status.text("Analyzing images with Assistant…")

                            sid = create_session(source=f"collection:{table_name}", note=f"{len(grouped_images)} images")
                            st.session_state.current_session_id = sid
                            link_session_uploads(sid, upload_ids)

                            # Default to desired_count slider above for collection as well
                            json_prompt, variants_json = ae.analyze_images(None, None, grouped_images, desired_count=desired_count)
                            analysis_progress.progress(1.0)
                            analysis_status.empty()

                            # Handle new direct prompt format
                            variants = None
                            if isinstance(variants_json, dict):
                                if "vu_engine_variants" in variants_json:
                                    # Legacy format
                                    variants = variants_json["vu_engine_variants"]
                                elif "prompts" in variants_json:
                                    # New direct format - convert to expected structure
                                    prompts = variants_json["prompts"]
                                    variants = [{"id": f"var_{i+1}", "prompt": prompt} for i, prompt in enumerate(prompts)]
                            if not variants:
                                status_obj2.update(label="No variants returned by assistant.", state="error")
                            else:
                                # Progress bar for generation
                                gen_progress = st.progress(0)
                                gen_status = st.empty()

                                status_obj2.update(label="Generating all variants…", state="running")

                                # Show prompts prominently
                                st.markdown("### 🎨 VU Engine Generated Prompts")
                                for idx, v in enumerate(variants):
                                    vid = v.get('id') or f"var_{idx+1}"
                                    prompt_text = ae.build_prompt_text(json_prompt, v)
                                    st.markdown(f"**🎯 VU Engine Prompt {idx+1} ({vid}):**")
                                    st.text_area(
                                        f"Prompt {idx+1}",
                                        value=prompt_text,
                                        height=120,
                                        key=f"collection_prompt_display_{idx}")

                                # Generate images with progress tracking
                                total_variants = len(variants)
                                for i, v in enumerate(variants):
                                    gen_progress.progress((i + 1) / total_variants)
                                    gen_status.text(f"Generating image {i+1}/{total_variants}…")

                                    vid = v.get('id') or f"var_{variants.index(v)}"
                                    img_out = ae.generate_single_variant_image(
                                        os.getenv("GOOGLE_API_KEY"),
                                        json_prompt,
                                        v,
                                        size="1024x1024"
                                    )
                                    if img_out:
                                        save_generated_image(upload_ids[0], vid, json_prompt, v, img_out)
                                        st.toast(f"Created image for {vid}")

                                gen_progress.progress(1.0)
                                gen_status.empty()
                                status_obj2.update(label="Generation complete.", state="complete")
                        except Exception as e:
                            status_obj2.update(label=f"Analysis failed: {e}", state="error")

        else:
            # Show all collections overview
            available_tables = get_available_tables()
            
            if not available_tables:
                st.info("No saved collections yet. Search for ads and save them to create your first collection!")
            else:
                st.markdown("### Your Collections")
                
                # Display collections as cards
                cols = st.columns(3)
                for i, (table_name, desc, created) in enumerate(available_tables):
                    with cols[i % 3]:
                        with st.container():
                            # Collection card
                            st.markdown(f"#### 📁 {desc if desc else table_name.replace('ads_', '').title()}")
                            
                            # Get count of ads in collection
                            ads_count = len(get_saved_ads(table_name))
                            st.write(f"**{ads_count} ads**")
                            st.caption(f"Created: {created[:10] if created else 'Unknown'}")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("View", key=f"view_{table_name}", width='stretch'):
                                    st.session_state.selected_table = table_name
                                    st.rerun()
                            with col2:
                                if st.button("Delete", key=f"del_{table_name}", width='stretch'):
                                    if delete_table(table_name):
                                        st.success("Collection deleted!")
                                        time.sleep(1)
                                        st.rerun()
                            
                            st.markdown("---")

    elif tab == "Generated Ads":
        st.title("🎨 Generated Ads")
        st.markdown("View your generated ad variants organized by sessions. Use the 'External Ads Generator' tab to upload and generate new ads.")

        st.markdown("---")
        st.subheader("Sessions")
        sessions = list_sessions()
        if not sessions:
            st.info("No sessions yet. Generate some ads to create your first session.")
        else:
            # Choose session to view
            default_idx = 0
            idx = st.selectbox(
                "Select a session",
                options=list(range(len(sessions))),
                format_func=lambda i: f"Session {sessions[i]['id']} • {sessions[i]['source']} • {sessions[i]['created_at'][:19]}",
                index=default_idx
            )
            session = sessions[idx]
            st.markdown(f"**Session {session['id']}** · Source: {session['source']} · Created: {session['created_at'][:19]}")
            upload_ids = list_session_uploads(session['id'])
            if not upload_ids:
                st.info("This session has no original uploads recorded.")
            else:
                st.markdown("### Original Images")
                cols = st.columns(4)
                for i, uid in enumerate(upload_ids):
                    with cols[i % 4]:
                        meta = get_upload_meta(uid)
                        img_b = get_upload_bytes(uid) or b""
                        if img_b:
                            label = meta['filename'] if meta else f"upload_{uid}"
                            st.image(img_b, caption=label, width='stretch')
            st.markdown("---")
            st.markdown("### Generated Images")
            gens = list_generated_for_session(session['id'])
            if not gens:
                st.info("No generated images for this session yet.")
            else:
                # Add bulk delete and download controls
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    select_all = st.checkbox("Select All", key=f"select_all_gen_{session['id']}")
                with col2:
                    if st.button("🗑️ Delete Selected", key=f"bulk_delete_gen_{session['id']}", help="Delete selected generated images"):
                        # Get selected images and delete them
                        selected_to_delete = []
                        for i, g in enumerate(gens):
                            if st.session_state.get(f"sel_gen_{session['id']}_{g['id']}", False):
                                selected_to_delete.append(g['id'])

                        if selected_to_delete:
                            delete_generated_images(selected_to_delete)
                            st.success(f"Deleted {len(selected_to_delete)} image(s)")
                            st.rerun()
                        else:
                            st.warning("No images selected")
                with col3:
                    if st.button("📥 Download All", key=f"download_all_gen_{session['id']}", help="Download all generated images in this session as ZIP"):
                        import zipfile
                        import io

                        # Create a ZIP file in memory
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                            for i, g in enumerate(gens):
                                img_b = get_generated_image_bytes(g['id'])
                                if img_b:
                                    filename = f"session_{session['id']}_variant_{g['variant_id'] or f'var_{i+1}'}.png"
                                    zip_file.writestr(filename, img_b)

                        zip_buffer.seek(0)
                        st.download_button(
                            label="📥 Download ZIP",
                            data=zip_buffer.getvalue(),
                            file_name=f"session_{session['id']}_generated_ads.zip",
                            mime="application/zip",
                            key=f"zip_dl_{session['id']}"
                        )

                if st.button("🗑️ Delete All", key=f"delete_all_gen_{session['id']}", help="Delete all generated images in this session"):
                    if st.session_state.get(f"confirm_delete_all_{session['id']}", False):
                        all_ids = [g['id'] for g in gens]
                        delete_generated_images(all_ids)
                        st.success(f"Deleted all {len(all_ids)} generated image(s)")
                        st.rerun()
                    else:
                        st.session_state[f"confirm_delete_all_{session['id']}"] = True
                        st.warning("Click again to confirm deletion of ALL generated images")

                cols = st.columns(3)
                for i, g in enumerate(gens):
                    with cols[i % 3]:
                        img_b = get_generated_image_bytes(g['id']) or b""
                        if img_b:
                            # Selection checkbox
                            is_selected = st.checkbox("Select", key=f"sel_gen_{session['id']}_{g['id']}", value=select_all)

                            cap = f"Variant {g['variant_id'] or ''} • from upload {g['upload_id']}"
                            st.image(img_b, width='stretch', caption=cap)

                            # Action buttons
                            col_dl, col_del = st.columns(2)
                            with col_dl:
                                st.download_button(
                                    label="📥 Download",
                                    data=img_b,
                                    file_name=f"session_{session['id']}_variant_{(g['variant_id'] or 'unknown')}.png",
                                    mime="image/png",
                                    key=f"dl_{session['id']}_{g['id']}"
                                )
                            with col_del:
                                if st.button("🗑️ Delete", key=f"del_gen_{session['id']}_{g['id']}", help="Delete this image"):
                                    delete_generated_images([g['id']])
                                    st.success("Image deleted")
                                    st.rerun()

if __name__ == "__main__":
    main()

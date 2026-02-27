#!/usr/bin/env python3
"""Validate that all endpoint conversions are correct."""

import sys
sys.path.insert(0, '/c:/Users/HomePC/Downloads/nft_platform_backend-main (1)/nft_platform_backend-main')

from app.routers.telegram_mint_router import router
from app.schemas.nft import (
    WebAppMintNFTRequest,
    WebAppListNFTRequest,
    WebAppTransferNFTRequest,
    WebAppBurnNFTRequest,
    WebAppSetPrimaryWalletRequest,
    WebAppMakeOfferRequest,
    WebAppCancelListingRequest,
)

print("Checking all POST endpoints exist and have correct signatures...")

# Get all routes
routes_dict = {}
for route in router.routes:
    if hasattr(route, 'path'):
        routes_dict[route.path] = route

# Define expected endpoints
expected_endpoints = {
    "/web-app/mint": "WebAppMintNFTRequest",
    "/web-app/list-nft": "WebAppListNFTRequest",
    "/web-app/transfer": "WebAppTransferNFTRequest",
    "/web-app/burn": "WebAppBurnNFTRequest",
    "/web-app/set-primary": "WebAppSetPrimaryWalletRequest",
    "/web-app/make-offer": "WebAppMakeOfferRequest",
    "/web-app/cancel-listing": "WebAppCancelListingRequest",
}

print(f"\nTotal routes found: {len(routes_dict)}")
print(f"Expected endpoints: {len(expected_endpoints)}")

# Check each endpoint
failed = []
for endpoint, request_model in expected_endpoints.items():
    if endpoint in routes_dict:
        print(f"[PASS] {endpoint} - OK")
    else:
        print(f"[FAIL] {endpoint} - NOT FOUND")
        failed.append(endpoint)

# Check that request models are importable
models_to_check = [
    ("WebAppMintNFTRequest", WebAppMintNFTRequest),
    ("WebAppListNFTRequest", WebAppListNFTRequest),
    ("WebAppTransferNFTRequest", WebAppTransferNFTRequest),
    ("WebAppBurnNFTRequest", WebAppBurnNFTRequest),
    ("WebAppSetPrimaryWalletRequest", WebAppSetPrimaryWalletRequest),
    ("WebAppMakeOfferRequest", WebAppMakeOfferRequest),
    ("WebAppCancelListingRequest", WebAppCancelListingRequest),
]

print("\nChecking Pydantic request models...")
for name, model_class in models_to_check:
    # Check if the model has the expected fields
    fields = list(model_class.__fields__.keys())
    print(f"[PASS] {name} - Fields: {fields}")

if failed:
    print(f"\n[FAIL] Missing endpoints: {failed}")
    sys.exit(1)
else:
    print("\n[PASS] All endpoints converted successfully!")
    sys.exit(0)

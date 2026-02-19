#!/usr/bin/env python3
"""Diagnostic script to list all registered routes."""

import asyncio
import logging
from pathlib import Path
import sys

# Add workspace to path
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    try:
        logger.info("Importing FastAPI app...")
        from app.main import app
        
        logger.info("\n" + "="*80)
        logger.info("REGISTERED API ROUTES")
        logger.info("="*80 + "\n")
        
        routes = {}
        for route in app.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                path = route.path
                methods = sorted(route.methods) if route.methods else ['GET']
                
                if path not in routes:
                    routes[path] = []
                routes[path].extend(methods)
        
        # Print organized by category
        categories = {
            '/api/v1/telegram': 'Telegram Web App API',
            '/api/v1/payments': 'Payments API',
            '/api/v1/wallets': 'Wallets API',
            '/api/v1/nfts': 'NFT API',
            '/api/v1/marketplace': 'Marketplace API',
            '/telegram': 'Telegram Bot',
        }
        
        for prefix, title in categories.items():
            matching_routes = {k: v for k, v in routes.items() if k.startswith(prefix)}
            if matching_routes:
                logger.info(f"\n{title} ({prefix}):")
                logger.info("-" * 80)
                for path in sorted(matching_routes.keys()):
                    methods = matching_routes[path]
                    method_str = " | ".join(set(methods)).ljust(15)
                    logger.info(f"  {method_str}  {path}")
        
        # Check for critical routes
        logger.info("\n" + "="*80)
        logger.info("CRITICAL ROUTE CHECKS")
        logger.info("="*80 + "\n")
        
        critical_routes = [
            '/api/v1/telegram/web-app/mint',
            '/api/v1/telegram/web-app/create-wallet',
            '/api/v1/telegram/web-app/import-wallet',
            '/api/v1/telegram/web-app/list-nft',
            '/api/v1/telegram/web-app/deposit',
            '/api/v1/payments/web-app/deposit',
            '/api/v1/payments/web-app/withdrawal',
            '/api/v1/payments/deposit/initiate',
            '/api/v1/payments/withdrawal/initiate',
        ]
        
        for route_path in critical_routes:
            if any(route_path == k for k in routes.keys()):
                logger.info(f"✅ {route_path}")
            else:
                logger.info(f"❌ {route_path} - NOT FOUND")
        
        return True
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return False

if __name__ == '__main__':
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

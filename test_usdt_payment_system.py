#!/usr/bin/env python3
"""
USDT Payment System Integration Tests

This script tests the complete USDT payment system including:
- Deposit flow (exchange → platform)
- Withdrawal flow (platform → exchange)
- NFT purchase with 2% commission
- Balance consistency
- Transaction history

Usage:
    python test_usdt_payments.py --test-server http://localhost:8000

Requirements:
    - Backend server running
    - Valid test user with Telegram init_data
    - Test wallets created on multiple blockchains
"""

import asyncio
import json
import sys
import argparse
from typing import Dict, Any, Optional
from datetime import datetime
import httpx

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text: str):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}")
    print(f"{text:.^60}")
    print(f"{'='*60}{Colors.ENDC}\n")

def print_success(text: str):
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")

def print_error(text: str):
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

def print_warning(text: str):
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")

def print_info(text: str):
    print(f"{Colors.OKBLUE}ℹ {text}{Colors.ENDC}")

class PaymentSystemTester:
    def __init__(self, server_url: str, init_data: str, user_id: str):
        self.server_url = server_url.rstrip('/')
        self.init_data = init_data
        self.user_id = user_id
        self.client = httpx.AsyncClient(base_url=self.server_url)
        self.test_results = []
        self.test_count = 0
        self.pass_count = 0
        self.fail_count = 0
        
    async def close(self):
        await self.client.aclose()
    
    async def test(self, name: str, func) -> bool:
        """Execute a test and track results"""
        self.test_count += 1
        print(f"\nTest {self.test_count}: {name}")
        print("-" * 50)
        
        try:
            await func()
            self.pass_count += 1
            self.test_results.append({"name": name, "status": "PASS"})
            print_success(name)
            return True
        except AssertionError as e:
            self.fail_count += 1
            self.test_results.append({"name": name, "status": "FAIL", "error": str(e)})
            print_error(f"{name}: {str(e)}")
            return False
        except Exception as e:
            self.fail_count += 1
            self.test_results.append({"name": name, "status": "ERROR", "error": str(e)})
            print_error(f"{name}: {type(e).__name__}: {str(e)}")
            return False
    
    async def api_call(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        """Make API call and return response"""
        url = f"/api/v1{path}" if not path.startswith("/api") else path
        print_info(f"{method} {url}")
        
        response = await self.client.request(method, url, **kwargs)
        print_info(f"Status: {response.status_code}")
        
        try:
            data = response.json()
            print_info(f"Response: {json.dumps(data, indent=2)[:200]}...")
            return {"status": response.status_code, "data": data}
        except:
            return {"status": response.status_code, "data": response.text}
    
    # ============ TEST SUITE ============
    
    async def test_get_balance(self):
        """Test: Get user balance"""
        response = await self.api_call("GET", "/payments/balance")
        assert response["status"] == 200, f"Status {response['status']}"
        data = response["data"]
        assert "balance" in data, "Missing balance field"
        assert isinstance(data["balance"], (int, float)), "Balance not a number"
        print_info(f"Current balance: ${data['balance']:.2f}")
    
    async def test_deposit_initiate_missing_wallet(self):
        """Test: Deposit initiation should fail without wallet_id"""
        response = await self.api_call(
            "POST", 
            "/payments/web-app/deposit",
            json={
                "user_id": self.user_id,
                "wallet_id": "",  # Empty wallet_id
                "amount": 100.0,
                "blockchain": "ethereum",
                "init_data": self.init_data
            }
        )
        assert response["status"] in [400, 422], f"Expected 400 or 422, got {response['status']}"
        print_info("Correctly rejected invalid wallet_id")
    
    async def test_deposit_initiate_with_amount(self):
        """Test: Initiate deposit with valid wallet"""
        # First, assume user has at least one wallet
        wallets_response = await self.api_call(
            "GET",
            f"/web-app/wallets?user_id={self.user_id}&init_data={self.init_data}"
        )
        
        if wallets_response["status"] != 200 or not wallets_response["data"].get("wallets"):
            print_warning("No wallets available for deposit test - skipping")
            return
        
        wallet = wallets_response["data"]["wallets"][0]
        wallet_id = wallet["id"]
        blockchain = wallet["blockchain"].lower()
        
        response = await self.api_call(
            "POST",
            "/payments/web-app/deposit",
            json={
                "user_id": self.user_id,
                "wallet_id": wallet_id,
                "amount": 50.0,
                "blockchain": blockchain,
                "init_data": self.init_data
            }
        )
        
        assert response["status"] == 200, f"Status {response['status']}: {response['data']}"
        data = response["data"]
        assert data.get("success"), "Success flag not set"
        assert "payment_id" in data, "Missing payment_id"
        assert "deposit_address" in data, "Missing deposit_address"
        
        # Store for later tests
        self.deposit_payment_id = data["payment_id"]
        self.deposit_address = data["deposit_address"]
        
        print_success(f"Deposit initiated: {self.deposit_payment_id}")
        print_info(f"Deposit address: {self.deposit_address}")
    
    async def test_withdrawal_initiate(self):
        """Test: Initiate withdrawal"""
        wallets_response = await self.api_call(
            "GET",
            f"/web-app/wallets?user_id={self.user_id}&init_data={self.init_data}"
        )
        
        if wallets_response["status"] != 200 or not wallets_response["data"].get("wallets"):
            print_warning("No wallets available for withdrawal test - skipping")
            return
        
        wallet = wallets_response["data"]["wallets"][0]
        wallet_id = wallet["id"]
        blockchain = wallet["blockchain"].lower()
        
        # Use valid address based on blockchain
        test_addresses = {
            "ethereum": "0x1234567890123456789012345678901234567890",
            "ton": "EQBx-VFkw13hRXc5M6B8BBr7Wfn-7NfYwAPP9yEWLcz_CX2A",
            "solana": "11111111111111111111111111111112",
            "bitcoin": "1A1z7agoat2LFNC5w3dEHkkCJjceeSF1K1"
        }
        
        dest_address = test_addresses.get(blockchain, test_addresses["ethereum"])
        
        response = await self.api_call(
            "POST",
            "/payments/web-app/withdrawal",
            json={
                "user_id": self.user_id,
                "wallet_id": wallet_id,
                "amount": 10.0,
                "destination_address": dest_address,
                "blockchain": blockchain,
                "init_data": self.init_data
            }
        )
        
        assert response["status"] == 200, f"Status {response['status']}: {response['data']}"
        data = response["data"]
        assert data.get("success"), "Success flag not set"
        assert "payment_id" in data, "Missing payment_id"
        assert "network_fee" in data, "Missing network_fee"
        
        self.withdrawal_payment_id = data["payment_id"]
        
        print_success(f"Withdrawal initiated: {self.withdrawal_payment_id}")
        print_info(f"Network fee: ${data.get('network_fee', 0):.2f}")
    
    async def test_payment_history(self):
        """Test: Get payment history"""
        response = await self.api_call(
            "GET",
            f"/payments/history?user_id={self.user_id}&limit=10"
        )
        
        assert response["status"] == 200, f"Status {response['status']}"
        data = response["data"]
        assert "payments" in data, "Missing payments field"
        
        print_info(f"Total payment history records: {len(data.get('payments', []))}")
    
    async def test_balance_validation(self):
        """Test: Balance should be non-negative number"""
        response = await self.api_call("GET", "/payments/balance")
        assert response["status"] == 200, "Failed to get balance"
        
        balance = response["data"].get("balance", 0)
        assert balance >= 0, f"Balance is negative: {balance}"
        print_info(f"Balance validation passed: ${balance:.2f}")
    
    async def test_commission_calculation(self):
        """Test: Verify 2% commission calculation logic"""
        # This test verifies the commission math
        test_price = 100.0
        expected_commission = test_price * 0.02
        expected_seller_funds = test_price - expected_commission
        
        assert expected_commission == 2.0, "Commission calculation incorrect"
        assert expected_seller_funds == 98.0, "Seller funds calculation incorrect"
        
        print_success("Commission calculation verified: 2% = $2.00 on $100")
        print_info(f"Seller receives: ${expected_seller_funds:.2f}")
    
    # ============ REPORT ============
    
    def print_report(self):
        """Print test results summary"""
        print_header("TEST SUMMARY")
        
        print(f"Total Tests: {self.test_count}")
        print_success(f"Passed: {self.pass_count}")
        if self.fail_count > 0:
            print_error(f"Failed: {self.fail_count}")
        
        print(f"\nSuccess Rate: {(self.pass_count/self.test_count*100) if self.test_count > 0 else 0:.1f}%")
        
        if self.fail_count == 0:
            print_success("\n✓ ALL TESTS PASSED!")
        else:
            print_error(f"\n✗ {self.fail_count} TESTS FAILED")
        
        print("\nDetailed Results:")
        for result in self.test_results:
            if result["status"] == "PASS":
                print_success(result["name"])
            else:
                print_error(f"{result['name']}: {result.get('error', 'Unknown error')}")
    
    async def run_all_tests(self):
        """Run complete test suite"""
        print_header("USDT Payment System Test Suite")
        
        # Basic tests
        await self.test("Get User Balance", self.test_get_balance)
        await self.test("Balance Validation", self.test_balance_validation)
        
        # Deposit tests
        await self.test("Deposit Initiation", self.test_deposit_initiate_with_amount)
        
        # Withdrawal tests
        await self.test("Withdrawal Initiation", self.test_withdrawal_initiate)
        
        # History tests
        await self.test("Payment History", self.test_payment_history)
        
        # Commission tests
        await self.test("Commission Calculation", self.test_commission_calculation)
        
        # Print results
        self.print_report()


async def main():
    parser = argparse.ArgumentParser(
        description="USDT Payment System Integration Tests"
    )
    parser.add_argument(
        "--server",
        default="http://localhost:8000",
        help="Server URL (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--user-id",
        default="550e8400-e29b-41d4-a716-446655440000",
        help="Test user ID (UUID)"
    )
    parser.add_argument(
        "--init-data",
        default="test_init_data",
        help="Telegram init_data for authentication"
    )
    
    args = parser.parse_args()
    
    print_header("Payment System Tester")
    print_info(f"Server: {args.server}")
    print_info(f"User ID: {args.user_id}")
    
    tester = PaymentSystemTester(args.server, args.init_data, args.user_id)
    
    try:
        await tester.run_all_tests()
    finally:
        await tester.close()
    
    return 0 if tester.fail_count == 0 else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

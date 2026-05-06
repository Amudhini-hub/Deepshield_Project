#!/usr/bin/env python3
"""
DeepShield Load Testing Script
Tests system performance under concurrent load and validates monitoring/alerting
"""

import asyncio
import aiohttp
import time
import statistics
import logging
from datetime import datetime
from typing import List, Dict, Optional
import json
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LoadTester:
    """Load testing client for DeepShield API"""

    def __init__(self, base_url: str = "http://localhost:8000", concurrent_users: int = 10):
        self.base_url = base_url.rstrip('/')
        self.concurrent_users = concurrent_users
        self.session: Optional[aiohttp.ClientSession] = None

        # Test results
        self.response_times: List[float] = []
        self.status_codes: List[int] = []
        self.errors: List[str] = []

        # User tokens for authenticated requests
        self.user_tokens: List[str] = []

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def setup_test_users(self, num_users: int = 5):
        """Create test users for authenticated testing"""
        logger.info(f"Setting up {num_users} test users...")

        for i in range(num_users):
            user_data = {
                "email": f"test_user_{i}_{int(time.time())}@example.com",
                "password": "TestPass123!",
                "full_name": f"Test User {i}"
            }

            try:
                async with self.session.post(f"{self.base_url}/api/v1/auth/register",
                                           json=user_data) as response:
                    if response.status == 200:
                        # Login to get token
                        login_data = {
                            "username": user_data["email"],
                            "password": user_data["password"]
                        }

                        async with self.session.post(f"{self.base_url}/api/v1/auth/login",
                                                   json=login_data) as login_response:
                            if login_response.status == 200:
                                result = await login_response.json()
                                self.user_tokens.append(result["access_token"])
                                logger.info(f"Created test user {i+1}/{num_users}")
                            else:
                                logger.error(f"Failed to login test user {i}: {login_response.status}")
                    else:
                        logger.error(f"Failed to register test user {i}: {response.status}")

            except Exception as e:
                logger.error(f"Error setting up test user {i}: {e}")

    async def make_request(self, endpoint: str, method: str = "GET",
                          data: Optional[Dict] = None, auth_token: Optional[str] = None) -> Dict:
        """Make a single HTTP request and record metrics"""
        start_time = time.time()

        headers = {}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"

        try:
            url = f"{self.base_url}{endpoint}"
            if method == "GET":
                async with self.session.get(url, headers=headers) as response:
                    status = response.status
                    content = await response.text()
            elif method == "POST":
                async with self.session.post(url, json=data, headers=headers) as response:
                    status = response.status
                    content = await response.text()
            else:
                raise ValueError(f"Unsupported method: {method}")

            response_time = (time.time() - start_time) * 1000  # Convert to milliseconds

            self.response_times.append(response_time)
            self.status_codes.append(status)

            return {
                "status_code": status,
                "response_time_ms": response_time,
                "success": status < 400,
                "content": content[:200] if content else ""  # Truncate for logging
            }

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.response_times.append(response_time)
            self.errors.append(str(e))

            return {
                "status_code": 0,
                "response_time_ms": response_time,
                "success": False,
                "error": str(e)
            }

    async def run_health_check_load_test(self, duration_seconds: int = 60):
        """Test health endpoint under load"""
        logger.info(f"Running health check load test for {duration_seconds} seconds...")

        end_time = time.time() + duration_seconds
        request_count = 0

        while time.time() < end_time:
            tasks = []
            for _ in range(self.concurrent_users):
                tasks.append(self.make_request("/health"))

            results = await asyncio.gather(*tasks, return_exceptions=True)
            request_count += len([r for r in results if not isinstance(r, Exception)])

            await asyncio.sleep(0.1)  # Small delay between batches

        return self._analyze_results("health_check", request_count)

    async def run_api_load_test(self, duration_seconds: int = 60):
        """Test various API endpoints under load"""
        logger.info(f"Running API load test for {duration_seconds} seconds...")

        endpoints = [
            ("/", "GET", None),
            ("/health", "GET", None),
            ("/metrics/health", "GET", None),
        ]

        # Add authenticated endpoints if we have tokens
        if self.user_tokens:
            endpoints.extend([
                ("/api/v1/users/me", "GET", None),
                ("/api/v1/behavioral/baseline", "GET", None),
            ])

        end_time = time.time() + duration_seconds
        request_count = 0

        while time.time() < end_time:
            tasks = []

            for _ in range(self.concurrent_users):
                endpoint, method, data = endpoints[request_count % len(endpoints)]
                auth_token = self.user_tokens[request_count % len(self.user_tokens)] if self.user_tokens else None
                tasks.append(self.make_request(endpoint, method, data, auth_token))

            results = await asyncio.gather(*tasks, return_exceptions=True)
            request_count += len([r for r in results if not isinstance(r, Exception)])

            await asyncio.sleep(0.2)  # Slightly longer delay for API calls

        return self._analyze_results("api_load", request_count)

    async def run_registration_load_test(self, num_registrations: int = 50):
        """Test user registration under load"""
        logger.info(f"Running registration load test with {num_registrations} registrations...")

        tasks = []
        for i in range(num_registrations):
            user_data = {
                "email": f"load_test_user_{i}_{int(time.time())}@example.com",
                "password": "LoadTest123!",
                "full_name": f"Load Test User {i}"
            }
            tasks.append(self.make_request("/api/v1/auth/register", "POST", user_data))

        # Run in batches to avoid overwhelming the server
        batch_size = 10
        results = []

        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i + batch_size]
            batch_results = await asyncio.gather(*batch, return_exceptions=True)
            results.extend(batch_results)
            await asyncio.sleep(0.5)  # Delay between batches

        return self._analyze_results("registration", len(results))

    def _analyze_results(self, test_name: str, total_requests: int) -> Dict:
        """Analyze test results and return statistics"""
        if not self.response_times:
            return {"error": "No requests completed"}

        successful_requests = len([s for s in self.status_codes if s and s < 400])
        error_count = len(self.errors)

        results = {
            "test_name": test_name,
            "timestamp": datetime.now().isoformat(),
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "error_count": error_count,
            "success_rate": (successful_requests / total_requests * 100) if total_requests > 0 else 0,
            "response_time_stats": {
                "min_ms": min(self.response_times),
                "max_ms": max(self.response_times),
                "avg_ms": statistics.mean(self.response_times),
                "median_ms": statistics.median(self.response_times),
                "p95_ms": statistics.quantiles(self.response_times, n=20)[18] if len(self.response_times) >= 20 else max(self.response_times),
                "p99_ms": statistics.quantiles(self.response_times, n=100)[98] if len(self.response_times) >= 100 else max(self.response_times)
            },
            "status_code_distribution": {},
            "errors": self.errors[:10]  # First 10 errors
        }

        # Status code distribution
        for code in set(self.status_codes):
            if code:
                count = self.status_codes.count(code)
                results["status_code_distribution"][str(code)] = count

        # Calculate requests per second
        if self.response_times:
            total_time = sum(self.response_times) / 1000  # Convert to seconds
            results["requests_per_second"] = total_requests / total_time if total_time > 0 else 0

        # Clear results for next test
        self.response_times.clear()
        self.status_codes.clear()
        self.errors.clear()

        return results

    async def run_comprehensive_test(self, duration_seconds: int = 120):
        """Run comprehensive load testing suite"""
        logger.info("Starting comprehensive load test...")

        results = {}

        # Setup test users
        await self.setup_test_users(5)

        # Run individual tests
        results["health_check"] = await self.run_health_check_load_test(duration_seconds // 4)
        results["api_load"] = await self.run_api_load_test(duration_seconds // 4)
        results["registration"] = await self.run_registration_load_test(20)

        # Get monitoring data after tests
        try:
            async with self.session.get(f"{self.base_url}/metrics") as response:
                if response.status == 200:
                    results["final_metrics"] = await response.json()
                else:
                    results["final_metrics"] = {"error": f"Failed to get metrics: {response.status}"}
        except Exception as e:
            results["final_metrics"] = {"error": str(e)}

        # Get alert data
        try:
            async with self.session.get(f"{self.base_url}/alerts/active") as response:
                if response.status == 200:
                    results["active_alerts"] = await response.json()
                else:
                    results["active_alerts"] = {"error": f"Failed to get alerts: {response.status}"}
        except Exception as e:
            results["active_alerts"] = {"error": str(e)}

        return results

async def main():
    """Main load testing function"""
    import argparse

    parser = argparse.ArgumentParser(description="DeepShield Load Testing")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL of the API")
    parser.add_argument("--users", type=int, default=10, help="Number of concurrent users")
    parser.add_argument("--duration", type=int, default=60, help="Test duration in seconds")
    parser.add_argument("--output", help="Output file for results")

    args = parser.parse_args()

    logger.info(f"Starting load test against {args.url} with {args.users} concurrent users")

    async with LoadTester(args.url, args.users) as tester:
        results = await tester.run_comprehensive_test(args.duration)

        # Print summary
        print("\n" + "="*60)
        print("LOAD TEST RESULTS SUMMARY")
        print("="*60)

        for test_name, test_results in results.items():
            if test_name in ["health_check", "api_load", "registration"]:
                print(f"\n{test_name.upper()}:")
                print(f"  Total Requests: {test_results.get('total_requests', 0)}")
                print(f"  Success Rate: {test_results.get('success_rate', 0):.1f}%")
                print(f"  Avg Response Time: {test_results.get('response_time_stats', {}).get('avg_ms', 0):.1f}ms")
                print(f"  P95 Response Time: {test_results.get('response_time_stats', {}).get('p95_ms', 0):.1f}ms")
                print(f"  Requests/sec: {test_results.get('requests_per_second', 0):.1f}")

        # Save detailed results
        if args.output:
            output_file = Path(args.output)
            output_file.parent.mkdir(exist_ok=True)

            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)

            logger.info(f"Detailed results saved to {args.output}")
        else:
            # Print detailed results
            print("\nDetailed Results:")
            print(json.dumps(results, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
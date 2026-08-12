import threading
import time
import requests
import json
import statistics

API_URL = "http://127.0.0.1:8000/api/v1/screener?min_roe=15"
NUM_REQUESTS = 10

def make_request(results, index):
    start_time = time.time()
    try:
        response = requests.get(API_URL, timeout=15)
        elapsed = time.time() - start_time
        results[index] = {
            "status_code": response.status_code,
            "time": elapsed,
            "error": None
        }
    except Exception as e:
        elapsed = time.time() - start_time
        results[index] = {
            "status_code": None,
            "time": elapsed,
            "error": str(e)
        }

def run_load_test():
    print(f"Starting load test: {NUM_REQUESTS} concurrent requests to {API_URL}")
    results = [None] * NUM_REQUESTS
    threads = []
    
    start_all = time.time()
    
    for i in range(NUM_REQUESTS):
        thread = threading.Thread(target=make_request, args=(results, i))
        threads.append(thread)
        thread.start()
        
    for thread in threads:
        thread.join()
        
    total_time = time.time() - start_all
    
    times = [r["time"] for r in results if r["time"] is not None]
    successes = sum(1 for r in results if r["status_code"] == 200)
    
    print("\n--- Load Test Results ---")
    print(f"Total time for all requests: {total_time:.2f} seconds")
    print(f"Successful requests: {successes}/{NUM_REQUESTS}")
    print(f"Average response time: {statistics.mean(times):.2f} seconds")
    print(f"Max response time: {max(times):.2f} seconds")
    print(f"Min response time: {min(times):.2f} seconds")
    
    if total_time < 10:
        print("SUCCESS: All requests completed within 10 seconds.")
    else:
        print("FAILED: Total time exceeded 10 seconds.")
        
if __name__ == "__main__":
    run_load_test()

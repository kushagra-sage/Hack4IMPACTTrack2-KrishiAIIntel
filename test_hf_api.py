import requests

model_id = "mistralai/Mistral-7B-Instruct-v0.2"

urls = [
    f"https://api-inference.huggingface.co/models/{model_id}",
    f"https://router.huggingface.co/hf-inference/models/{model_id}",
    f"https://api-inference.huggingface.co/models/{model_id}/v1/chat/completions",
    f"https://router.huggingface.co/hf-inference/v1/chat/completions"
]

payload1 = {"inputs": "Test", "parameters": {"max_new_tokens": 10}}
payload2 = {"model": model_id, "messages": [{"role": "user", "content": "Test"}]}

print("Testing without token (expecting 401 if endpoint exists, 404 if not, 410 if deprecated):")
for url in urls:
    print(f"\n--- URL: {url} ---")
    
    # Test with payload 1
    res1 = requests.post(url, json=payload1)
    print(f"Payload 1 (inputs) status: {res1.status_code}")
    if res1.status_code != 401:
        print(f"Response: {res1.text[:200]}")
        
    # Test with payload 2 if applicable
    if "v1/chat/completions" in url:
        res2 = requests.post(url, json=payload2)
        print(f"Payload 2 (OpenAI) status: {res2.status_code}")
        if res2.status_code != 401:
            print(f"Response: {res2.text[:200]}")

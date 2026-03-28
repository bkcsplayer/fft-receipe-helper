import urllib.request, json

url = 'https://api.minimax.io/v1/chat/completions'
headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer sk-api-b85KvoPAm3WTkwKiPIYTnL52ohyf0yoTHD-7u0Uh9V5KqTvD3Y8652bfLsYWwHFNHR12Z4E_mABoquUM4APumQQFnIKxxclvXEyGXu3qnQGH3BrgmtXshJs'
}

models_to_test = ['abab6.5s-chat', 'MiniMax-VL-01', 'MiniMax-V-01', 'abab6.5g-chat', 'MiniMax-M2.5', 'minimax-vl-01']

for model in models_to_test:
    data = json.dumps({
        'model': model,
        'messages': [{
            'role': 'user',
            'content': [
                {'type': 'text', 'text': 'Are you a vision model? Extract JSON'},
                {'type': 'image_url', 'image_url': {'url': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII='}}
            ]
        }],
        'max_tokens': 100
    }).encode('utf-8')
    
    req = urllib.request.Request(url, data=data, headers=headers)
    try:
        print(f"Testing {model}...")
        with urllib.request.urlopen(req) as r:
            resp = json.loads(r.read().decode('utf-8'))
            print("  SUCCESS!")
            try:
                print("  Response:", resp['choices'][0]['message']['content'][:200])
            except Exception:
                print("  Response structure:", list(resp.keys()))
    except Exception as e:
        msg = e.read().decode('utf-8') if hasattr(e, 'read') else str(e)
        print("  FAILED:", getattr(e, 'code', 'Error'), msg[:200])

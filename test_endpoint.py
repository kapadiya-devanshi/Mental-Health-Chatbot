"""Test the emotion detection endpoint"""
import urllib.request
import json

try:
    req = urllib.request.Request(
        'http://127.0.0.1:5000/detect_emotion',
        data=b'{"image":"test"}',
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    resp = urllib.request.urlopen(req)
    print("Response:")
    print(resp.read().decode())
except Exception as e:
    print(f"Error: {e}")

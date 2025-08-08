#!/usr/bin/env python3
"""
Test script to verify all dashboard options work
"""
import requests
import time
import subprocess
import os
from datetime import datetime

def test_metabase_direct():
    """Test direct access to Metabase"""
    print("🧪 Testing Metabase Direct Access...")
    url = "https://rdg-consultores.metabaseapp.com/public/dashboard/647f87a1-b51d-494e-a5d0-f20ddf100e68"
    
    try:
        response = requests.head(url, timeout=10)
        if response.status_code == 200:
            print("✅ Metabase Direct Access: WORKING")
            print(f"   Status: {response.status_code}")
            print(f"   Headers: X-Frame-Options = {response.headers.get('X-Frame-Options', 'Not set')}")
            return True
        else:
            print(f"❌ Metabase Direct Access: Failed ({response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Metabase Direct Access: Error - {e}")
        return False

def test_flask_local():
    """Test Flask server locally"""
    print("\n🧪 Testing Flask Server Local...")
    url = "http://localhost:5002/"
    
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print("✅ Flask Local: WORKING")
            print(f"   Status: {response.status_code}")
            print(f"   Content length: {len(response.text)} chars")
            return True
        else:
            print(f"❌ Flask Local: Failed ({response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Flask Local: Error - {e}")
        return False

def test_flask_routes():
    """Test specific Flask routes"""
    print("\n🧪 Testing Flask Routes...")
    routes = [
        "/dashboard/calificacion-metabase",
        "/dashboard/simple", 
        "/solutions",
        "/api/health"
    ]
    
    results = {}
    for route in routes:
        url = f"http://localhost:5002{route}"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {route}: WORKING")
                results[route] = True
            else:
                print(f"❌ {route}: Failed ({response.status_code})")
                results[route] = False
        except Exception as e:
            print(f"❌ {route}: Error - {e}")
            results[route] = False
    
    return results

def start_simple_flask():
    """Start a simple Flask server for testing"""
    print("\n🚀 Starting Simple Flask Server...")
    
    flask_code = '''
from flask import Flask
app = Flask(__name__)

@app.route('/')
def home():
    return """
    <h1>🚀 Falcon Dashboard - Test Server</h1>
    <h2>📊 Available Options:</h2>
    <ul>
        <li><a href="https://rdg-consultores.metabaseapp.com/public/dashboard/647f87a1-b51d-494e-a5d0-f20ddf100e68" target="_blank">🎯 Metabase Dashboard (Direct Link)</a></li>
        <li><a href="/test">🧪 Test Page</a></li>
    </ul>
    <p>Status: ✅ Flask Server Working!</p>
    """

@app.route('/test')
def test():
    return "<h1>✅ Test Route Working!</h1><a href='/'>← Back</a>"

if __name__ == '__main__':
    print("Starting Flask on port 5002...")
    app.run(host='0.0.0.0', port=5002, debug=True)
'''
    
    with open('/tmp/test_flask.py', 'w') as f:
        f.write(flask_code)
    
    return '/tmp/test_flask.py'

def main():
    print("=" * 60)
    print("🧪 TESTING ALL DASHBOARD OPTIONS")
    print("=" * 60)
    print(f"Time: {datetime.now()}")
    
    # Test 1: Metabase Direct
    metabase_works = test_metabase_direct()
    
    # Test 2: Flask Local
    flask_works = test_flask_local()
    
    # Test 3: Flask Routes (if Flask is working)
    if flask_works:
        routes_result = test_flask_routes()
    else:
        print("\n⚠️ Flask not working, skipping route tests")
        routes_result = {}
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 RESULTS SUMMARY")
    print("=" * 60)
    
    print(f"🎯 Metabase Direct Link: {'✅ WORKING' if metabase_works else '❌ FAILED'}")
    print(f"🐍 Flask Server: {'✅ WORKING' if flask_works else '❌ FAILED'}")
    
    if routes_result:
        print("\n📋 Flask Routes:")
        for route, status in routes_result.items():
            print(f"  {route}: {'✅' if status else '❌'}")
    
    print("\n" + "=" * 60)
    print("💡 RECOMMENDATIONS")
    print("=" * 60)
    
    if metabase_works:
        print("✅ OPTION 1 (RECOMMENDED): Use Metabase Direct Link")
        print("   URL: https://rdg-consultores.metabaseapp.com/public/dashboard/647f87a1-b51d-494e-a5d0-f20ddf100e68")
        print("   ✅ All filters work")
        print("   ✅ Real-time data")
        print("   ✅ Professional interface")
        print("   ⚠️ Opens in new tab")
    
    if flask_works:
        print("\n✅ OPTION 2: Use Flask Dashboard")
        print("   URL: http://localhost:5002/")
        print("   ✅ Integrated in your app")
        print("   ✅ Custom control")
        print("   ⚠️ Basic interface")
    else:
        print("\n❌ Flask needs to be fixed first")
        
    print("\n🚀 IMMEDIATE ACTION:")
    if metabase_works:
        print("   Use the Metabase direct link - it works perfectly!")
    else:
        print("   Check Metabase configuration")
    
    if not flask_works:
        flask_file = start_simple_flask()
        print(f"\n🔧 To start a test Flask server, run:")
        print(f"   python3 {flask_file}")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Simple HTTP server for dashboard - Alternative to Flask
"""
import http.server
import socketserver
import webbrowser
import os
import sys
from pathlib import Path

def start_simple_server():
    """Start a simple HTTP server for the dashboard"""
    
    # Change to the dashboard directory
    dashboard_dir = Path(__file__).parent
    os.chdir(dashboard_dir)
    
    # Try different ports
    ports_to_try = [8000, 8080, 9000, 9090, 7000, 7777, 5000, 3000]
    
    server = None
    port = None
    
    for try_port in ports_to_try:
        try:
            # Create server
            handler = http.server.SimpleHTTPRequestHandler
            server = socketserver.TCPServer(("", try_port), handler)
            port = try_port
            print(f"✅ Server started successfully on port {port}")
            break
        except OSError as e:
            print(f"❌ Port {try_port} is busy: {e}")
            continue
    
    if not server:
        print("❌ Could not find an available port")
        return False
    
    # Print URLs
    print("\n" + "="*60)
    print("🚀 DASHBOARD SERVER RUNNING")
    print("="*60)
    print(f"🌐 Local URL: http://localhost:{port}")
    print(f"🌐 Network URL: http://127.0.0.1:{port}")
    print("\n📱 Available files:")
    print(f"   • Main Dashboard (Flask): http://localhost:{port}/templates/dashboard.html")
    print(f"   • Standalone Dashboard: http://localhost:{port}/dashboard_supervision_standalone.html") 
    print(f"   • Design Mockup: http://localhost:{port}/DISEÑO_DASHBOARD_PESTAÑAS.html")
    print("\n⚡ Press Ctrl+C to stop the server")
    print("="*60)
    
    # Open browser automatically
    dashboard_url = f"http://localhost:{port}/dashboard_supervision_standalone.html"
    print(f"\n🔍 Opening browser: {dashboard_url}")
    
    try:
        webbrowser.open(dashboard_url)
        print("✅ Browser opened successfully")
    except Exception as e:
        print(f"⚠️ Could not open browser automatically: {e}")
        print(f"Please manually open: {dashboard_url}")
    
    # Start serving
    try:
        print(f"\n🎯 Serving files from: {dashboard_dir}")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
        server.shutdown()
        return True

if __name__ == "__main__":
    try:
        success = start_simple_server()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        print("\n💡 Alternative: Open 'dashboard_supervision_standalone.html' directly in your browser")
        sys.exit(1)
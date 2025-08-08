#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return '''
    <h1>Dashboard Supervisión</h1>
    <p><a href="/dashboard">Ver Dashboard</a></p>
    <p><a href="/api/test">Test API</a></p>
    '''

@app.route('/dashboard')
def dashboard():
    return render_template('wireframe_dashboard_v2.html')

@app.route('/api/wireframe/sucursales')
def api_sucursales():
    # Datos de prueba simples
    data = [
        {
            'name': '01 Centro Tampico',
            'grupo': 'OCHTER TAMPICO', 
            'ciudad': 'Tampico',
            'estado': 'Tamaulipas',
            'lat': 22.2331,
            'lng': -97.8614,
            'calificacion': 94.5,
            'tier': 'Excelente',
            'trimestre': 'Q4 2024',
            'areasOportunidad': ['LIMPIEZA BAÑOS (89%)', 'ATENCIÓN (91%)', 'ORDEN (92%)']
        },
        {
            'name': '15 Plaza Ogas',
            'grupo': 'OGAS',
            'ciudad': 'Reynosa', 
            'estado': 'Tamaulipas',
            'lat': 26.0968,
            'lng': -98.2796,
            'calificacion': 87.3,
            'tier': 'Bueno',
            'trimestre': 'Q4 2024',
            'areasOportunidad': ['FREIDORA (78%)', 'LIMPIEZA (82%)', 'SERVICIO (84%)']
        },
        {
            'name': '32 Laguna Center',
            'grupo': 'PLOG LAGUNA',
            'ciudad': 'Torreón',
            'estado': 'Coahuila', 
            'lat': 25.5487,
            'lng': -103.4647,
            'calificacion': 76.8,
            'tier': 'Regular',
            'trimestre': 'Q4 2024',
            'areasOportunidad': ['ASADORES (65%)', 'SERVICIO (71%)', 'LIMPIEZA (74%)']
        }
    ]
    
    return jsonify({
        'status': 'success',
        'data': data,
        'count': len(data)
    })

@app.route('/api/test')
def test():
    return jsonify({'status': 'working', 'message': 'API funcionando'})

if __name__ == '__main__':
    print('Dashboard Simple - Puerto 9090')
    print('http://127.0.0.1:9090/dashboard')
    app.run(host='127.0.0.1', port=9090, debug=False)
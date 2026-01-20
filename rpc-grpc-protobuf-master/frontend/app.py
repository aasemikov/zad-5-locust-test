from flask import Flask, render_template, request, jsonify, redirect, url_for
import grpc
import json
import os
from datetime import datetime
import sys
sys.path.append('../dictionary_service')
import dictionary_pb2
import dictionary_pb2_grpc

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

class DictionaryGRPCClient:
    def __init__(self, host='dictionary-grpc', port=50051):
        self.host = host
        self.port = port
        self._channel = None
        self._stub = None
    
    @property
    def stub(self):
        if self._stub is None:
            self._channel = grpc.insecure_channel(f'{self.host}:{self.port}')
            self._stub = dictionary_pb2_grpc.DictionaryServiceStub(self._channel)
        return self._stub
    
    def get_term(self, term):
        try:
            response = self.stub.GetTerm(dictionary_pb2.GetTermRequest(term=term))
            return {
                'success': True,
                'data': {
                    'term': response.term,
                    'definition': response.definition,
                    'category': response.category,
                    'related_terms': list(response.related_terms),
                    'source': response.source,
                    'created_at': response.created_at,
                    'updated_at': response.updated_at
                } if response.term else None
            }
        except grpc.RpcError as e:
            return {'success': False, 'error': e.details()}
    
    def add_term(self, term_data):
        try:
            response = self.stub.AddTerm(dictionary_pb2.AddTermRequest(
                term=term_data['term'],
                definition=term_data['definition'],
                category=term_data['category'],
                related_terms=term_data.get('related_terms', []),
                source=term_data.get('source', '')
            ))
            return {
                'success': response.success,
                'message': response.message,
                'term': response.term
            }
        except grpc.RpcError as e:
            return {'success': False, 'error': e.details()}
    
    def get_all_terms(self, page=1, page_size=50):
        try:
            response = self.stub.GetAllTerms(dictionary_pb2.GetAllRequest(
                page=page,
                page_size=page_size
            ))
            terms = []
            for term in response.terms:
                terms.append({
                    'term': term.term,
                    'definition': term.definition,
                    'category': term.category,
                    'related_terms': list(term.related_terms),
                    'source': term.source,
                    'created_at': term.created_at,
                    'updated_at': term.updated_at
                })
            
            return {
                'success': True,
                'terms': terms,
                'total_count': response.total_count
            }
        except grpc.RpcError as e:
            return {'success': False, 'error': e.details()}
    
    def search_terms(self, query, category=None):
        try:
            response = self.stub.SearchTerms(dictionary_pb2.SearchRequest(
                query=query,
                category=category or ""
            ))
            terms = []
            for term in response.terms:
                terms.append({
                    'term': term.term,
                    'definition': term.definition,
                    'category': term.category,
                    'related_terms': list(term.related_terms),
                    'source': term.source,
                    'created_at': term.created_at,
                    'updated_at': term.updated_at
                })
            
            return {
                'success': True,
                'terms': terms,
                'total_count': response.total_count
            }
        except grpc.RpcError as e:
            return {'success': False, 'error': e.details()}
    
    def get_terms_by_category(self, category):
        try:
            response = self.stub.GetTermsByCategory(
                dictionary_pb2.CategoryRequest(category=category)
            )
            terms = []
            for term in response.terms:
                terms.append({
                    'term': term.term,
                    'definition': term.definition,
                    'category': term.category,
                    'related_terms': list(term.related_terms),
                    'source': term.source,
                    'created_at': term.created_at,
                    'updated_at': term.updated_at
                })
            
            return {
                'success': True,
                'terms': terms,
                'total_count': response.total_count
            }
        except grpc.RpcError as e:
            return {'success': False, 'error': e.details()}

client = DictionaryGRPCClient()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/terms', methods=['GET'])
def get_terms():
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 50, type=int)
    
    result = client.get_all_terms(page=page, page_size=page_size)
    return jsonify(result)

@app.route('/api/terms/<term>', methods=['GET'])
def get_term(term):
    result = client.get_term(term)
    return jsonify(result)

@app.route('/api/terms', methods=['POST'])
def add_term():
    data = request.get_json()
    
    required_fields = ['term', 'definition', 'category']
    for field in required_fields:
        if field not in data:
            return jsonify({
                'success': False,
                'error': f'Missing required field: {field}'
            }), 400
    
    result = client.add_term(data)
    return jsonify(result)

@app.route('/api/search', methods=['GET'])
def search_terms():
    query = request.args.get('q', '')
    category = request.args.get('category', '')
    
    if not query:
        return jsonify({
            'success': False,
            'error': 'Query parameter "q" is required'
        }), 400
    
    result = client.search_terms(query, category if category else None)
    return jsonify(result)

@app.route('/api/categories/<category>', methods=['GET'])
def get_terms_by_category(category):
    result = client.get_terms_by_category(category)
    return jsonify(result)

@app.route('/api/categories', methods=['GET'])
def get_categories():
    result = client.get_all_terms(page_size=1000)
    if not result['success']:
        return jsonify(result)
    
    categories = set()
    for term in result['terms']:
        categories.add(term['category'])
    
    return jsonify({
        'success': True,
        'categories': sorted(list(categories))
    })

@app.route('/health')
def health():
    try:
        result = client.get_all_terms(page_size=1)
        return jsonify({
            'status': 'healthy',
            'grpc_connection': 'ok' if result['success'] else 'error'
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'grpc_connection': 'error',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
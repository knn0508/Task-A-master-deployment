# routes/chat_routes.py
"""Improved chat routes with automatic document detection"""
import json
import re
import unicodedata
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

chat_bp = Blueprint('chat', __name__, url_prefix='/api/chat')

def init_chat_routes(db_manager, rag_service, config):
    """Initialize chat routes with intelligent document selection"""
    
    @chat_bp.route('/ask', methods=['POST'])
    @jwt_required(locations=['cookies', 'headers'])
    def ask_question():
        """Smart question answering with automatic document detection"""
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            
            question = data.get('question', '').strip()
            document_id = data.get('document_id')  # Optional
            conversation_id = data.get('conversation_id')
            
            if not question:
                return jsonify({'error': 'Sual tələb olunur'}), 400
            
            # Get available documents
            claims = get_jwt()
            if claims.get('role') == 'admin':
                documents = db_manager.get_documents()
            else:
                documents = db_manager.get_documents(user_id)

            # If no documents exist → use direct LLM chat
            if not documents:
                answer = rag_service.model.generate_content(question).text
                return jsonify({
                    "answer": answer,
                    "conversation_id": None,
                    "document_used": None
                })
            
            # If no document specified, try to find the most relevant one
            if not document_id:
                document_id = find_relevant_document(question, documents, rag_service)

                if not document_id:
                    # fallback: general chat through LLM
                    answer = rag_service.model.generate_content(question).text

                    return jsonify({
                        "answer": answer,
                        "conversation_id": None,
                        "document_used": None
                    })
            
            # Check document exists and is processed
            doc = next((d for d in documents if d['id'] == document_id), None)
            
            if not doc:
                return jsonify({'error': 'Sənəd tapılmadı və ya icazəniz yoxdur'}), 404
            
            if not doc.get('is_processed'):
                return jsonify({'error': 'Sənəd hələ işlənməyib'}), 400

            if len(question) < 4:
                answer = rag_service.model.generate_content(question).text
                return jsonify({
                    "answer": answer,
                    "conversation_id": None,
                    "document_used": None
                })

            # Get answer from RAG
            result = rag_service.answer_question(question, document_id)
            
            if not result['success']:
                return jsonify({
                    'error': result.get('error', 'Cavab alına bilmədi'),
                    'answer': result.get('answer', 'Xəta baş verdi')
                }), 500
            
            answer = result['answer']
            
            # Add document info to answer
            answer_with_source = f"**Mənbə:** {doc['original_name']}\n\n{answer}"
            
            # Save to conversation
            message = {
                'question': question,
                'answer': answer_with_source,
                'document_id': document_id,
                'document_name': doc['original_name'],
                'timestamp': datetime.utcnow().isoformat()
            }
            
            if conversation_id:
                # Update existing conversation
                conversation = db_manager.get_conversation(conversation_id, user_id)
                if conversation:
                    messages = json.loads(conversation['messages'])
                    messages.append(message)
                    db_manager.update_conversation(conversation_id, json.dumps(messages))
                else:
                    conversation_id = None
            
            if not conversation_id:
                # Create new conversation
                title = f"{doc['original_name']}: {question[:30]}..."
                messages = [message]
                conversation_id = db_manager.create_conversation(
                    user_id=user_id,
                    document_id=document_id,
                    title=title,
                    messages=json.dumps(messages)
                )
            
            return jsonify({
                'answer': answer_with_source,
                'conversation_id': conversation_id,
                'document_used': {
                    'id': doc['id'],
                    'name': doc['original_name']
                },
                'context_length': result.get('context_length', 0)
            })
            
        except Exception as e:
            return jsonify({'error': f'Chat xətası: {str(e)}'}), 500
    
    def find_relevant_document(question, documents, rag_service):
        """Try to find the most relevant document for the question"""
        question_lower = question.lower()
        question_norm = unicodedata.normalize('NFKD', question.casefold())
        question_norm = ''.join(ch for ch in question_norm if not unicodedata.combining(ch))
        question_norm = re.sub(r'[_\-\./]+', ' ', question_norm)
        question_norm = re.sub(r'\s+', ' ', question_norm).strip()
        question_tokens = set(re.findall(r'[a-z0-9əçıöüşğ]+', question_norm))
        
        # First, check if document name is mentioned in the question
        best_doc_id = None
        best_score = 0
        for doc in documents:
            doc_name_lower = doc['original_name'].lower()
            # Remove extension for matching
            doc_name_without_ext = doc_name_lower.rsplit('.', 1)[0]

            doc_base = re.sub(r'\.[^.]+$', '', doc['original_name'])
            doc_norm = unicodedata.normalize('NFKD', doc_base.casefold())
            doc_norm = ''.join(ch for ch in doc_norm if not unicodedata.combining(ch))
            doc_norm = re.sub(r'[_\-\./]+', ' ', doc_norm)
            doc_norm = re.sub(r'\s+', ' ', doc_norm).strip()
            doc_tokens = set(re.findall(r'[a-z0-9əçıöüşğ]+', doc_norm))

            score = 0
            if doc_name_without_ext in question_lower or doc_name_lower in question_lower:
                score += 30
            if doc_norm and doc_norm in question_norm:
                score += 100
            for token in question_tokens.intersection(doc_tokens):
                if len(token) >= 3:
                    score += 25

            if score > best_score:
                best_score = score
                best_doc_id = doc['id']

        if best_doc_id and best_score >= 25:
            return best_doc_id
        
        # If only one document exists, use it
        if len(documents) == 1:
            return documents[0]['id']
        
        # Try to match by document type keywords
        doc_type_keywords = {
            'pdf': ['pdf', 'sənəd', 'fayl'],
            'docx': ['word', 'docx', 'məktub'],
            'xlsx': ['excel', 'cədvəl', 'statistika', 'rəqəm'],
            'txt': ['mətn', 'text', 'txt'],
            'json': ['json', 'data', 'məlumat']
        }
        
        for doc in documents:
            file_type = doc.get('file_type', '').lower()
            if file_type in doc_type_keywords:
                for keyword in doc_type_keywords[file_type]:
                    if keyword in question_lower:
                        return doc['id']
        
        # If can't determine, return None to ask for clarification
        return None
    
    @chat_bp.route('/conversations', methods=['GET'])
    @jwt_required(locations=['cookies', 'headers'])
    def list_conversations():
        """List user conversations"""
        try:
            user_id = get_jwt_identity()
            conversations = db_manager.get_conversations(user_id)
            
            return jsonify({
                'conversations': [
                    {
                        'id': conv['id'],
                        'title': conv['title'],
                        'document_id': conv['document_id'],
                        'document_name': conv.get('document_name'),
                        'message_count': len(json.loads(conv['messages'])),
                        'created_at': conv['created_at'],
                        'updated_at': conv['updated_at']
                    }
                    for conv in conversations
                ]
            })
            
        except Exception as e:
            return jsonify({'error': f'Conversations xətası: {str(e)}'}), 500
    
    @chat_bp.route('/conversations/<int:conv_id>', methods=['GET'])
    @jwt_required(locations=['cookies', 'headers'])
    def get_conversation(conv_id):
        """Get conversation messages"""
        try:
            user_id = get_jwt_identity()
            conversation = db_manager.get_conversation(conv_id, user_id)
            
            if not conversation:
                return jsonify({'error': 'Söhbət tapılmadı'}), 404
            
            return jsonify({
                'conversation': {
                    'id': conversation['id'],
                    'title': conversation['title'],
                    'document_id': conversation['document_id'],
                    'messages': json.loads(conversation['messages']),
                    'created_at': conversation['created_at'],
                    'updated_at': conversation['updated_at']
                }
            })
            
        except Exception as e:
            return jsonify({'error': f'Conversation xətası: {str(e)}'}), 500
    
    @chat_bp.route('/conversations/<int:conv_id>', methods=['DELETE'])
    @jwt_required(locations=['cookies', 'headers'])
    def delete_conversation(conv_id):
        """Delete conversation"""
        try:
            user_id = get_jwt_identity()
            success = db_manager.delete_conversation(conv_id, user_id)
            
            if success:
                return jsonify({'message': 'Söhbət silindi'})
            else:
                return jsonify({'error': 'Söhbət tapılmadı'}), 404
            
        except Exception as e:
            return jsonify({'error': f'Delete xətası: {str(e)}'}), 500
    
    @chat_bp.route('/search', methods=['POST'])
    @jwt_required(locations=['cookies', 'headers'])
    def search_across_documents():
        """Search across all available documents"""
        try:
            user_id = get_jwt_identity()
            claims = get_jwt()
            data = request.get_json()
            
            query = data.get('query', '').strip()
            if not query:
                return jsonify({'error': 'Axtarış sorğusu tələb olunur'}), 400
            
            # Get available documents
            if claims.get('role') == 'admin':
                documents = db_manager.get_documents()
            else:
                documents = db_manager.get_documents(user_id)
            
            # Search in each document
            results = []
            for doc in documents:
                if doc.get('is_processed'):
                    context = rag_service.search_relevant_content(query, doc['id'], k=2)
                    if context:
                        results.append({
                            'document_id': doc['id'],
                            'document_name': doc['original_name'],
                            'relevant_content': context[:500] + '...' if len(context) > 500 else context
                        })
            
            return jsonify({
                'query': query,
                'results': results,
                'total_results': len(results)
            })
            
        except Exception as e:
            return jsonify({'error': f'Search xətası: {str(e)}'}), 500
    
    return chat_bp
# services/hr_questions_handler.py
"""Special handler for HR_Suallar.docx document priority"""
from datetime import datetime, timezone
import re
import json
from typing import Optional, Dict


class HRQuestionsHandler:
    """Handle HR questions with special priority"""
    
    def __init__(self, db_manager, rag_service):
        self.db_manager = db_manager
        self.rag_service = rag_service
        
        # HR related keywords
        self.hr_keywords = [
            # Employment terms
            'məzuniyyət', 'ezamiyyət', 'əmək haqqı', 'maaş', 'iş saatı', 'iş günü',
            'işə qəbul', 'işdən çıxma', 'işdən azad', 'müqavilə', 'əmək müqaviləsi',
            
            # Benefits and policies
            'sığorta', 'tibbi sığorta', 'pensiya', 'müavinət', 'kompensasiya',
            'qaydalar', 'prosedur', 'siyasət', 'intizam', 'cəza',
            
            # Time off
            'bayram', 'istirahət', 'xəstəlik', 'xəstəlik vərəqi', 'icazə',
            'ödənişli məzuniyyət', 'ödənişsiz məzuniyyət',
            
            # Performance
            'qiymətləndirmə', 'performans', 'bonus', 'mükafat', 'artım', 'təlim',
            'karyera', 'inkişaf', 'vəzifə artımı',
            
            # General HR
            'hr', 'kadr', 'insan resursları', 'personal', 'işçi hüquqları',
            'ştat', 'struktur', 'təşkilat', 'departament', 'şöbə'
        ]
        
        # Question patterns that indicate HR queries
        self.hr_question_patterns = [
            r'\b(nə qədər|neçə gün|nə vaxt|haçan)\s+(məzuniyyət|ezamiyyət|istirahət)',
            r'\b(işə qəbul|işdən çıxma|işdən azad)',
            r'\b(əmək haqqı|maaş|bonus|mükafat)',
            r'\b(sığorta|müavinət|kompensasiya)',
            r'\b(iş saatı|iş günü|qrafik)',
            r'\b(qaydalar|prosedur|siyasət)',
            r'\b(hüquq|öhdəlik|məsuliyyət)',
        ]
    
    def is_hr_question(self, question: str) -> bool:
        """Check if question is HR-related"""
        question_lower = question.lower()
        
        # Check for HR keywords
        for keyword in self.hr_keywords:
            if keyword in question_lower:
                return True
        
        # Check for HR patterns
        for pattern in self.hr_question_patterns:
            if re.search(pattern, question_lower, re.IGNORECASE):
                return True
        
        return False
    
    def find_hr_document(self) -> Optional[Dict]:
        """Find HR_Suallar.docx document in the database"""
        try:
            # Look for HR document
            result = self.db_manager.execute_query(
                """SELECT * FROM documents 
                   WHERE LOWER(original_name) LIKE '%hr%sual%' 
                      OR LOWER(original_name) LIKE '%hr_sual%'
                      OR LOWER(original_name) = 'hr_suallar.docx'
                      OR (document_type = 'other' AND LOWER(original_name) LIKE '%sual%')
                   ORDER BY 
                      CASE 
                        WHEN LOWER(original_name) = 'hr_suallar.docx' THEN 1
                        WHEN LOWER(original_name) LIKE 'hr_sual%' THEN 2
                        ELSE 3
                      END
                   LIMIT 1""",
                fetch_one=True
            )
            
            if result:
                return dict(result)
            
            # Alternative: Look for document with HR keywords
            documents = self.db_manager.get_documents()
            for doc in documents:
                doc_name_lower = doc['original_name'].lower()
                if 'hr' in doc_name_lower and ('sual' in doc_name_lower or 'question' in doc_name_lower):
                    return doc
                
                # Check keywords for HR content
                if doc.get('keywords'):
                    try:
                        keywords = json.loads(doc['keywords'])
                        keywords_lower = [kw.lower() for kw in keywords]
                        hr_keyword_matches = sum(1 for kw in self.hr_keywords[:10] if kw in keywords_lower)
                        if hr_keyword_matches >= 3:  # If at least 3 HR keywords match
                            return doc
                    except:
                        pass
            
            return None
            
        except Exception as e:
            print(f"Error finding HR document: {e}")
            return None
    
    def process_hr_question(self, question: str) -> Dict:
        """Process HR-related question with priority to HR_Suallar.docx"""
        
        # Find HR document
        hr_doc = self.find_hr_document()
        
        if not hr_doc:
            return {
                'success': False,
                'answer': 'HR suallar sənədi tapılmadı. Zəhmət olmasa HR_Suallar.docx faylını yükləyin.',
                'type': 'hr_document_not_found'
            }
        
        if not hr_doc.get('is_processed'):
            return {
                'success': False,
                'answer': 'HR sənədi hələ işlənməyib. Zəhmət olmasa bir az gözləyin.',
                'type': 'hr_document_not_processed'
            }
        
        print(f"Using HR document: {hr_doc['original_name']} (ID: {hr_doc['id']})")
        
        # Get answer from HR document
        result = self.rag_service.answer_question(question, hr_doc['id'])
        
        if not result.get('success'):
            return {
                'success': False,
                'answer': 'HR sənədində bu suala cavab tapılmadı.',
                'type': 'hr_answer_not_found'
            }
        
        # Format HR answer
        answer = result.get('answer', '')
        formatted_answer = self.format_hr_answer(answer, question, hr_doc['original_name'])
        
        return {
            'success': True,
            'answer': formatted_answer,
            'source': hr_doc['original_name'],
            'document_id': hr_doc['id'],
            'type': 'hr_answer'
        }
    
    def format_hr_answer(self, raw_answer: str, question: str, doc_name: str) -> str:
        """Format HR answer with proper structure"""
        
        # Add header
        formatted = f"**📋 HR Cavab (Mənbə: {doc_name})**\n\n"
        
        # Check if answer contains policy/procedure info
        if any(word in raw_answer.lower() for word in ['qayda', 'prosedur', 'siyasət']):
            formatted += "**Müvafiq Qaydalar:**\n"
        
        # Format the answer
        lines = raw_answer.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                formatted += "\n"
                continue
            
            # Check for numbered items
            if re.match(r'^\d+[\.)]\s', line):
                formatted += f"• {line}\n"
            # Check for important points
            elif any(word in line.lower() for word in ['qeyd:', 'vacib:', 'diqqət:']):
                formatted += f"**{line}**\n"
            # Check for dates/deadlines
            elif re.search(r'\d+\s*(gün|ay|il)', line, re.IGNORECASE):
                formatted += f"⏰ {line}\n"
            else:
                formatted += f"{line}\n"
        
        # Add footer note
        formatted += "\n---\n*Bu məlumat rəsmi HR sənədindən götürülüb. Əlavə suallarınız varsa, HR şöbəsi ilə əlaqə saxlayın.*"
        
        return formatted
    
    def enhance_with_hr_keywords(self, doc_id: int) -> bool:
        """Enhance HR document with specific HR keywords"""
        try:
            # Get current keywords
            result = self.db_manager.execute_query(
                "SELECT keywords FROM documents WHERE id = ?",
                (doc_id,),
                fetch_one=True
            )
            
            existing_keywords = []
            if result:
                try:
                    existing_keywords = json.loads(dict(result).get('keywords', '[]'))
                except:
                    existing_keywords = []
            
            # Add important HR keywords
            hr_essential_keywords = [
                'məzuniyyət', 'ezamiyyət', 'əmək haqqı', 'sığorta', 
                'iş saatı', 'qaydalar', 'müqavilə', 'hr', 'kadr',
                'işçi hüquqları', 'kompensasiya', 'bonus'
            ]
            
            # Merge keywords
            all_keywords = list(set(existing_keywords + hr_essential_keywords))[:15]
            
            # Update database
            self.db_manager.execute_query(
                "UPDATE documents SET keywords = ? WHERE id = ?",
                (json.dumps(all_keywords, ensure_ascii=False), doc_id)
            )
            
            print(f"Enhanced HR document with keywords: {all_keywords}")
            return True
            
        except Exception as e:
            print(f"Error enhancing HR keywords: {e}")
            return False


# Integration function to add to simple_app.py
def integrate_hr_handler(app, db_manager, rag_service, chat_service):
    """Integrate HR handler into the chat system"""
    
    hr_handler = HRQuestionsHandler(db_manager, rag_service)
    
    # Override chat service process method
    original_process = chat_service.process_chat_message
    
    def enhanced_process_chat_message(question: str, user_id: int, conversation_id: Optional[int] = None) -> Dict:
        """Enhanced chat processing with HR priority"""
        
        # Check if this is an HR question
        if hr_handler.is_hr_question(question):
            print("🏢 HR question detected - using HR document priority")
            
            # Try to get answer from HR document
            hr_result = hr_handler.process_hr_question(question)
            
            if hr_result['success']:
                # Save conversation
                message = {
                    'question': question,
                    'answer': hr_result['answer'],
                    'document_id': hr_result.get('document_id'),
                    'document_name': hr_result.get('source'),
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
                
                if not conversation_id:
                    title = f"HR Sual: {question[:30]}..."
                    conversation_id = db_manager.create_conversation(
                        user_id=user_id,
                        document_id=hr_result.get('document_id'),
                        title=title,
                        messages=json.dumps([message])
                    )
                else:
                    conv = db_manager.get_conversation(conversation_id, user_id)
                    if conv:
                        messages = json.loads(conv['messages'])
                        messages.append(message)
                        db_manager.update_conversation(conversation_id, json.dumps(messages))
                
                return {
                    'answer': hr_result['answer'],
                    'conversation_id': conversation_id,
                    'document_used': {
                        'id': hr_result.get('document_id'),
                        'name': hr_result.get('source')
                    },
                    'type': 'hr_priority_answer'
                }
        
        # Fall back to original processing
        return original_process(question, user_id, conversation_id)
    
    # Replace the method
    chat_service.process_chat_message = enhanced_process_chat_message
    
      
    return app
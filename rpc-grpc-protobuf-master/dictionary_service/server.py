import grpc
from concurrent import futures
import logging
import time
from datetime import datetime
import json
import os
from typing import Dict, List, Optional

import dictionary_pb2
import dictionary_pb2_grpc

class DictionaryService:
    def __init__(self):
        self.terms: Dict[str, dict] = {}
        self.load_initial_data()
    
    def load_initial_data(self):
        """Загрузка начальных данных глоссария"""
        initial_terms = [
            {
                "term": "gRPC",
                "definition": "gRPC Remote Procedure Calls - высокопроизводительный фреймворк для удаленного вызова процедур от Google, использующий HTTP/2 и Protocol Buffers",
                "category": "RPC",
                "related_terms": ["Protobuf", "HTTP/2", "Microservices"],
                "source": "Google",
                "created_at": "2024-01-15T10:00:00Z",
                "updated_at": "2024-01-15T10:00:00Z"
            },
            {
                "term": "Protobuf",
                "definition": "Protocol Buffers - механизм сериализации структурированных данных от Google, используемый для коммуникации между сервисами",
                "category": "Serialization",
                "related_terms": ["gRPC", "Serialization", "Schema"],
                "source": "Google",
                "created_at": "2024-01-15T10:00:00Z",
                "updated_at": "2024-01-15T10:00:00Z"
            },
            {
                "term": "REST",
                "definition": "Representational State Transfer - архитектурный стиль для создания веб-сервисов, использующий HTTP методы",
                "category": "API",
                "related_terms": ["HTTP", "JSON", "API Design"],
                "source": "Roy Fielding",
                "created_at": "2024-01-15T10:00:00Z",
                "updated_at": "2024-01-15T10:00:00Z"
            },
            {
                "term": "GraphQL",
                "definition": "Язык запросов для API и среда выполнения для их выполнения с существующими данными",
                "category": "API",
                "related_terms": ["Query Language", "API", "Facebook"],
                "source": "Facebook",
                "created_at": "2024-01-15T10:00:00Z",
                "updated_at": "2024-01-15T10:00:00Z"
            },
            {
                "term": "Docker",
                "definition": "Платформа для разработки, доставки и запуска приложений в контейнерах",
                "category": "Containerization",
                "related_terms": ["Container", "Kubernetes", "OCI"],
                "source": "Docker Inc.",
                "created_at": "2024-01-15T10:00:00Z",
                "updated_at": "2024-01-15T10:00:00Z"
            }
        ]
        
        for term_data in initial_terms:
            self.terms[term_data["term"]] = term_data

class DictionaryServicer(dictionary_pb2_grpc.DictionaryServiceServicer):
    def __init__(self):
        self.service = DictionaryService()
    
    def GetTerm(self, request, context):
        try:
            term = request.term
            if term in self.service.terms:
                term_data = self.service.terms[term]
                return dictionary_pb2.TermResponse(
                    term=term_data["term"],
                    definition=term_data["definition"],
                    category=term_data["category"],
                    related_terms=term_data["related_terms"],
                    source=term_data["source"],
                    created_at=term_data["created_at"],
                    updated_at=term_data["updated_at"]
                )
            else:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Term '{term}' not found")
                return dictionary_pb2.TermResponse()
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return dictionary_pb2.TermResponse()
    
    def AddTerm(self, request, context):
        try:
            term = request.term
            if term in self.service.terms:
                context.set_code(grpc.StatusCode.ALREADY_EXISTS)
                context.set_details(f"Term '{term}' already exists")
                return dictionary_pb2.OperationResponse(
                    success=False,
                    message=f"Term '{term}' already exists"
                )
            
            current_time = datetime.utcnow().isoformat() + "Z"
            self.service.terms[term] = {
                "term": term,
                "definition": request.definition,
                "category": request.category,
                "related_terms": list(request.related_terms),
                "source": request.source,
                "created_at": current_time,
                "updated_at": current_time
            }
            
            return dictionary_pb2.OperationResponse(
                success=True,
                message=f"Term '{term}' added successfully",
                term=term
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return dictionary_pb2.OperationResponse(
                success=False,
                message=str(e)
            )
    
    def UpdateTerm(self, request, context):
        try:
            term = request.term
            if term not in self.service.terms:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Term '{term}' not found")
                return dictionary_pb2.OperationResponse(
                    success=False,
                    message=f"Term '{term}' not found"
                )
            
            current_time = datetime.utcnow().isoformat() + "Z"
            self.service.terms[term].update({
                "definition": request.definition,
                "category": request.category,
                "related_terms": list(request.related_terms),
                "source": request.source,
                "updated_at": current_time
            })
            
            return dictionary_pb2.OperationResponse(
                success=True,
                message=f"Term '{term}' updated successfully",
                term=term
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return dictionary_pb2.OperationResponse(
                success=False,
                message=str(e)
            )
    
    def DeleteTerm(self, request, context):
        try:
            term = request.term
            if term not in self.service.terms:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Term '{term}' not found")
                return dictionary_pb2.OperationResponse(
                    success=False,
                    message=f"Term '{term}' not found"
                )
            
            del self.service.terms[term]
            return dictionary_pb2.OperationResponse(
                success=True,
                message=f"Term '{term}' deleted successfully",
                term=term
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return dictionary_pb2.OperationResponse(
                success=False,
                message=str(e)
            )
    
    def GetAllTerms(self, request, context):
        try:
            page = request.page or 1
            page_size = request.page_size or 10
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            
            all_terms = list(self.service.terms.values())
            paginated_terms = all_terms[start_idx:end_idx]
            
            terms_list = []
            for term_data in paginated_terms:
                terms_list.append(dictionary_pb2.TermResponse(
                    term=term_data["term"],
                    definition=term_data["definition"],
                    category=term_data["category"],
                    related_terms=term_data["related_terms"],
                    source=term_data["source"],
                    created_at=term_data["created_at"],
                    updated_at=term_data["updated_at"]
                ))
            
            return dictionary_pb2.TermsList(
                terms=terms_list,
                total_count=len(all_terms)
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return dictionary_pb2.TermsList()
    
    def SearchTerms(self, request, context):
        try:
            query = request.query.lower()
            category = request.category
            
            results = []
            for term_data in self.service.terms.values():
                if (query in term_data["term"].lower() or 
                    query in term_data["definition"].lower() or
                    query in term_data["category"].lower()):
                    
                    if category and term_data["category"] != category:
                        continue
                    
                    results.append(dictionary_pb2.TermResponse(
                        term=term_data["term"],
                        definition=term_data["definition"],
                        category=term_data["category"],
                        related_terms=term_data["related_terms"],
                        source=term_data["source"],
                        created_at=term_data["created_at"],
                        updated_at=term_data["updated_at"]
                    ))
            
            return dictionary_pb2.TermsList(
                terms=results,
                total_count=len(results)
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return dictionary_pb2.TermsList()
    
    def GetTermsByCategory(self, request, context):
        try:
            category = request.category
            results = []
            
            for term_data in self.service.terms.values():
                if term_data["category"] == category:
                    results.append(dictionary_pb2.TermResponse(
                        term=term_data["term"],
                        definition=term_data["definition"],
                        category=term_data["category"],
                        related_terms=term_data["related_terms"],
                        source=term_data["source"],
                        created_at=term_data["created_at"],
                        updated_at=term_data["updated_at"]
                    ))
            
            return dictionary_pb2.TermsList(
                terms=results,
                total_count=len(results)
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return dictionary_pb2.TermsList()

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    dictionary_pb2_grpc.add_DictionaryServiceServicer_to_server(
        DictionaryServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("gRPC Dictionary Server started on port 50051")
    
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    serve()
# locust/grpc_client.py
import grpc
import dictionary_pb2
import dictionary_pb2_grpc

class DictionaryGrpcClient:
    def __init__(self, host: str = "localhost", port: int = 50051):
        self.channel = grpc.insecure_channel(f"{host}:{port}")
        self.stub = dictionary_pb2_grpc.DictionaryServiceStub(self.channel)

    def get_term(self, term: str):
        request = dictionary_pb2.GetTermRequest(term=term)
        return self.stub.GetTerm(request)

    def add_term(self, term: str, definition: str, category: str, related_terms=None, source=""):
        if related_terms is None:
            related_terms = []
        request = dictionary_pb2.AddTermRequest(
            term=term,
            definition=definition,
            category=category,
            related_terms=related_terms,
            source=source
        )
        return self.stub.AddTerm(request)

    def get_all_terms(self, page: int = 1, page_size: int = 10):
        request = dictionary_pb2.GetAllRequest(page=page, page_size=page_size)
        return self.stub.GetAllTerms(request)

    def search_terms(self, query: str, category: str = ""):
        request = dictionary_pb2.SearchRequest(query=query, category=category)
        return self.stub.SearchTerms(request)

    def get_terms_by_category(self, category: str):
        request = dictionary_pb2.CategoryRequest(category=category)
        return self.stub.GetTermsByCategory(request)

    def close(self):
        self.channel.close()
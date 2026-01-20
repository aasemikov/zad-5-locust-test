import grpc
import dictionary_pb2
import dictionary_pb2_grpc

class DictionaryClient:
    def __init__(self, host='localhost', port=50051):
        self.channel = grpc.insecure_channel(f'{host}:{port}')
        self.stub = dictionary_pb2_grpc.DictionaryServiceStub(self.channel)
    
    def get_term(self, term):
        try:
            response = self.stub.GetTerm(dictionary_pb2.GetTermRequest(term=term))
            return response
        except grpc.RpcError as e:
            print(f"Error getting term: {e.details()}")
            return None
    
    def add_term(self, term, definition, category, related_terms=None, source=""):
        try:
            if related_terms is None:
                related_terms = []
            
            response = self.stub.AddTerm(dictionary_pb2.AddTermRequest(
                term=term,
                definition=definition,
                category=category,
                related_terms=related_terms,
                source=source
            ))
            return response
        except grpc.RpcError as e:
            print(f"Error adding term: {e.details()}")
            return None
    
    def get_all_terms(self, page=1, page_size=10):
        try:
            response = self.stub.GetAllTerms(dictionary_pb2.GetAllRequest(
                page=page,
                page_size=page_size
            ))
            return response
        except grpc.RpcError as e:
            print(f"Error getting all terms: {e.details()}")
            return None
    
    def search_terms(self, query, category=None):
        try:
            response = self.stub.SearchTerms(dictionary_pb2.SearchRequest(
                query=query,
                category=category or ""
            ))
            return response
        except grpc.RpcError as e:
            print(f"Error searching terms: {e.details()}")
            return None

def main():
    client = DictionaryClient()

    print("=== Dictionary gRPC Client ===")

    term = client.get_term("gRPC")
    if term and term.term:
        print(f"Found term: {term.term}")
        print(f"Definition: {term.definition}")
        print(f"Category: {term.category}")
        print(f"Related terms: {', '.join(term.related_terms)}")

    result = client.add_term(
        term="Kubernetes",
        definition="Система оркестрации контейнеров с открытым исходным кодом",
        category="Containerization",
        related_terms=["Docker", "Containers", "Orchestration"],
        source="Google"
    )
    if result and result.success:
        print(f"Successfully added term: {result.term}")
    
    search_result = client.search_terms("container")
    if search_result:
        print(f"Found {search_result.total_count} terms:")
        for term in search_result.terms:
            print(f" - {term.term} ({term.category})")

if __name__ == '__main__':
    main()
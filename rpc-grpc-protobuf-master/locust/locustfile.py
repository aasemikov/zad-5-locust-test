# locust/locustfile.py
from locust import User, task, between
import time
import random
from grpc import RpcError
from grpc_client import DictionaryGrpcClient

# Список терминов из начальных данных — для реалистичных запросов
EXISTING_TERMS = ["gRPC", "Protobuf", "REST", "GraphQL", "Docker"]
CATEGORIES = ["RPC", "Serialization", "API", "Containerization"]
SEARCH_QUERIES = ["API", "container", "protocol", "Google", "web"]

class GrpcUser(User):
    abstract = True

    def __init__(self, environment):
        super().__init__(environment)
        # В Docker-сети имя сервиса — dictionary-grpc
        self.client = DictionaryGrpcClient(host="localhost", port=50051)

    def on_stop(self):
        self.client.close()

class DictionaryUser(GrpcUser):
    # Пауза между действиями: от 0.5 до 3 секунд
    wait_time = between(0.5, 3.0)

    @task(6)
    def get_existing_term(self):
        term = random.choice(EXISTING_TERMS)
        self._make_grpc_call(
            name="GetTerm (existing)",
            func=self.client.get_term,
            args=(term,)
        )

    @task(3)
    def get_nonexistent_term(self):
        # Генерируем уникальное имя, чтобы избежать случайных совпадений
        term = f"NonExistent_{int(time.time() * 1000000) % 1000000}"
        self._make_grpc_call(
            name="GetTerm (not found)",
            func=self.client.get_term,
            args=(term,),
            expect_not_found=True
        )

    @task(4)
    def search_terms(self):
        query = random.choice(SEARCH_QUERIES)
        self._make_grpc_call(
            name="SearchTerms",
            func=self.client.search_terms,
            args=(query,)
        )

    @task(3)
    def get_all_terms(self):
        self._make_grpc_call(
            name="GetAllTerms",
            func=self.client.get_all_terms,
            kwargs={"page": 1, "page_size": 10}
        )

    @task(2)
    def get_by_category(self):
        category = random.choice(CATEGORIES)
        self._make_grpc_call(
            name="GetTermsByCategory",
            func=self.client.get_terms_by_category,
            args=(category,)
        )

    @task(1)
    def add_unique_term(self):
        # Генерируем уникальный термин, чтобы не было конфликтов ALREADY_EXISTS
        unique_id = f"LoadTest_{int(time.time() * 1000000)}"
        self._make_grpc_call(
            name="AddTerm",
            func=self.client.add_term,
            kwargs={
                "term": unique_id,
                "definition": "Definition for load testing",
                "category": "LoadTest",
                "related_terms": ["test", "performance"],
                "source": "Locust"
            }
        )

    def _make_grpc_call(self, name: str, func, args=(), kwargs=None, expect_not_found=False):
        if kwargs is None:
            kwargs = {}
        start_time = time.time()
        try:
            response = func(*args, **kwargs)
            total_time_ms = int((time.time() - start_time) * 1000)
            response_size = len(response.SerializeToString())

            # Для GetTerm (not found): если вернулся термин — это ошибка
            if name == "GetTerm (not found)" and hasattr(response, 'term') and response.term:
                self.environment.events.request.fire(
                    request_type="gRPC",
                    name=name,
                    response_time=total_time_ms,
                    response_length=response_size,
                    exception=AssertionError("Unexpected term found")
                )
            else:
                self.environment.events.request.fire(
                    request_type="gRPC",
                    name=name,
                    response_time=total_time_ms,
                    response_length=response_size,
                    exception=None,
                )
        except RpcError as e:
            total_time_ms = int((time.time() - start_time) * 1000)
            # Если ожидаем NOT_FOUND — считаем успехом
            if expect_not_found and e.code().name == "NOT_FOUND":
                self.environment.events.request.fire(
                    request_type="gRPC",
                    name=name,
                    response_time=total_time_ms,
                    response_length=0,
                    exception=None,
                )
            else:
                self.environment.events.request.fire(
                    request_type="gRPC",
                    name=name,
                    response_time=total_time_ms,
                    response_length=0,
                    exception=e,
                )
        except Exception as e:
            total_time_ms = int((time.time() - start_time) * 1000)
            self.environment.events.request.fire(
                request_type="gRPC",
                name=name,
                response_time=total_time_ms,
                response_length=0,
                exception=e,
            )
import time
import random
from locust import HttpUser, task, between, TaskSet, events
from locust.runners import MasterRunner, WorkerRunner
import json
import uuid

TECH_TERMS = [
    "API", "База данных", "Кэширование", "Контейнеризация", "Микросервисы",
    "Очередь сообщений", "Репликация", "Шардирование", "Индексация", "Кластеризация",
    "Балансировка нагрузки", "Мониторинг", "Логирование", "Аутентификация", "Авторизация",
    "Docker", "Kubernetes", "CI/CD", "DevOps", "Agile", "Scrum", "Kanban",
    "REST", "GraphQL", "gRPC", "WebSocket", "JWT", "OAuth", "OpenID Connect"
]

DEFINITIONS = [
    "система или протокол для взаимодействия между программными компонентами",
    "организованная структура для хранения, управления и извлечения данных",
    "техника хранения данных во временной памяти для ускорения доступа",
    "технология упаковки приложения со всеми зависимостями в изолированную среду",
    "архитектурный подход к разработке приложений как набора небольших сервисов",
    "механизм асинхронной передачи сообщений между компонентами системы",
    "процесс копирования данных с одного сервера на другой для обеспечения отказоустойчивости",
    "метод горизонтального масштабирования базы данных путем разделения на части",
    "создание структур для ускорения поиска данных в базе данных",
    "объединение нескольких серверов в единую систему для повышения производительности",
    "распределение нагрузки между несколькими серверами для улучшения производительности",
    "процесс сбора и анализа метрик для оценки работы системы",
    "запись событий и действий в системе для последующего анализа",
    "процесс проверки личности пользователя",
    "процесс определения прав доступа пользователя к ресурсам"
]

class GlossaryUserBehavior(TaskSet):
    """Поведение пользователя Glossary API"""
    
    def on_start(self):
        """Инициализация пользователя"""
        self.user_id = f"user_{str(uuid.uuid4())[:8]}"
        self.created_term_keys = []
        self.session_start = time.time()
        
        self.test_term = f"Термин_{int(time.time()) % 1000}"
        self.test_definition = f"Определение для тестирования нагрузкой. Создано пользователем {self.user_id}"
    
    @task(5) 
    def browse_terms(self):
        """Просмотр списка терминов с разными параметрами пагинации"""
        skip = random.choice([0, 10, 20, 30, 40, 50])
        limit = random.choice([5, 10, 20, 50, 100])
        
        params = {"skip": skip, "limit": limit}
        endpoint_name = f"GET /terms/?skip={skip}&limit={limit}"
        
        time.sleep(random.uniform(0.3, 1.2))
        
        with self.client.get("/terms/", 
                           params=params,
                           name=endpoint_name,
                           catch_response=True) as response:
            self._validate_response(response, "browse_terms")
    
    @task(4)
    def view_specific_term(self):
        """Просмотр конкретного термина"""
        if not self.parent.existing_term_keys:
            self.browse_terms()
            return
        
        term_key = random.choice(self.parent.existing_term_keys)
        
        time.sleep(random.uniform(0.5, 2.0))
        
        with self.client.get(f"/terms/{term_key}",
                           name="GET /terms/[key]",
                           catch_response=True) as response:
            self._validate_response(response, "view_term")
    
    @task(3)
    def create_new_term(self):
        """Создание нового термина"""
        if random.random() < 0.7:
            term = random.choice(TECH_TERMS)
            definition = random.choice(DEFINITIONS)
        else: 
            term = f"{self.test_term}_{random.randint(1, 1000)}"
            definition = self.test_definition
        
        payload = {
            "term": term,
            "definition": definition
        }
        
        time.sleep(random.uniform(1.5, 3.0))
        
        with self.client.post("/terms/",
                            json=payload,
                            name="POST /terms/",
                            catch_response=True) as response:
            if self._validate_response(response, "create_term"):
                try:
                    term_data = response.json()
                    new_key = f"user_term_{len(self.created_term_keys)}_{self.user_id}"
                    self.created_term_keys.append(new_key)
                except Exception as e:
                    print(f"Ошибка при обработке ответа: {e}")
    
    @task(2) 
    def update_term(self):
        """Обновление существующего термина"""
        available_keys = self.created_term_keys + self.parent.existing_term_keys
        
        if not available_keys or random.random() < 0.6:
            return
        
        term_key = random.choice(available_keys)
        
        new_definitions = [
            "Обновленное определение для нагрузочного тестирования",
            "Новое описание термина после редактирования",
            "Скорректированная дефиниция с учетом последних изменений",
            f"Определение отредактировано в {time.strftime('%H:%M:%S')}",
            "Уточненная формулировка после ревизии",
            "Расширенное объяснение понятия",
            "Актуализированное описание термина"
        ]
        
        payload = {
            "definition": random.choice(new_definitions)
        }
        
        time.sleep(random.uniform(1.0, 2.5))
        
        with self.client.put(f"/terms/{term_key}",
                           json=payload,
                           name="PUT /terms/[key]",
                           catch_response=True) as response:
            self._validate_response(response, "update_term")
    
    @task(1)
    def delete_term(self):
        """Удаление термина"""
        if not self.created_term_keys or random.random() < 0.8:
            return
        
        term_key = self.created_term_keys.pop()

        time.sleep(random.uniform(2.0, 4.0))
        
        with self.client.delete(f"/terms/{term_key}",
                              name="DELETE /terms/[key]",
                              catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"DELETE failed: {response.status_code}")
    
    @task(3)
    def get_root_and_stats(self):
        """Получение корневого пути"""
        time.sleep(random.uniform(0.2, 0.8))
        
        with self.client.get("/",
                           name="GET /",
                           catch_response=True) as response:
            self._validate_response(response, "get_root")
    
    def _validate_response(self, response, action_name):
        """Валидация ответа сервера"""
        if response.status_code >= 200 and response.status_code < 300:
            try:
                if response.content:
                    data = response.json()
                    
                    if action_name == "browse_terms":
                        if not isinstance(data, list):
                            response.failure(f"Expected array, got {type(data)}")
                            return False
                        if data and not all(isinstance(item, dict) and 'term' in item and 'definition' in item for item in data):
                            response.failure("Invalid item structure in array")
                            return False
                    
                    elif action_name in ["view_term", "create_term", "update_term"]:
                        if not isinstance(data, dict):
                            response.failure(f"Expected object, got {type(data)}")
                            return False
                        if 'term' not in data or 'definition' not in data:
                            response.failure("Missing required fields in response")
                            return False
                    
                    response.success()
                    return True
                else:
                    response.success()
                    return True
                    
            except json.JSONDecodeError:
                response.failure("Invalid JSON response")
                return False
            except Exception as e:
                response.failure(f"Response validation error: {str(e)}")
                return False
        else:
            if response.status_code == 422:
                try:
                    error_data = response.json()
                    response.failure(f"Validation error: {error_data.get('detail', 'Unknown')}")
                except:
                    response.failure(f"Validation error (status {response.status_code})")
            else:
                response.failure(f"Status {response.status_code}: {response.text[:100]}")
            return False
    
    def on_stop(self):
        """Действия при остановке пользователя"""
        session_duration = time.time() - self.session_start
        print(f"User {self.user_id} completed session: {len(self.created_term_keys)} terms created, duration: {session_duration:.2f}s")

class GlossaryUser(HttpUser):
    """Основной класс пользователя Glossary API"""
    tasks = [GlossaryUserBehavior]
    wait_time = between(1, 3)
    
    existing_term_keys = ["term_0", "term_1", "term_2", "term_3", "term_4", 
                         "term_5", "term_6", "term_7", "term_8", "term_9"]
    
    def on_start(self):
        """Инициализация общего списка терминов"""
        pass

@events.init.add_listener
def on_locust_init(environment, **kwargs):
    """Инициализация тестовой среды"""
    if isinstance(environment.runner, MasterRunner):
        print("Master node initialized")
    elif isinstance(environment.runner, WorkerRunner):
        print(f"Worker node initialized: {environment.runner.worker_index}")
    else:
        print("Running in standalone mode")

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Запуск теста"""
    print(f"Test started at {time.strftime('%H:%M:%S')}")
    print(f"Target host: {environment.host}")
    print("Testing Glossary API endpoints:")
    print("   - GET /terms/?skip=X&limit=Y")
    print("   - POST /terms/")
    print("   - GET /terms/{term_key}")
    print("   - PUT /terms/{term_key}")
    print("   - DELETE /terms/{term_key}")
    print("   - GET /")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Остановка теста"""
    print(f"Test stopped at {time.strftime('%H:%M:%S')}")
    print("Final statistics collected")

@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, context, **kwargs):
    """Сбор дополнительных метрик по каждому запросу"""
    if exception:
        with open("locust_errors.log", "a") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {request_type} {name} - {exception}\n")
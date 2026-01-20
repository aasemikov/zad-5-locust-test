#!/bin/bash
echo "Запуск нагрузочного тестирования Glossary API"
echo "=============================================="

if [ -d "venv" ]; then
    echo "Активация виртуального окружения..."
    source venv/bin/activate
fi

echo "1. Проверка Python..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    PIP_CMD="pip3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
    PIP_CMD="pip"
else
    echo "ОШИБКА: Python не найден. Установите Python 3.8+"
    echo "   macOS: brew install python"
    echo "   Ubuntu: sudo apt install python3 python3-pip"
    echo "   Windows: скачайте с python.org"
    exit 1
fi

echo "   Используется: $($PYTHON_CMD --version 2>&1)"

echo "2. Установка зависимостей..."
$PIP_CMD install --upgrade pip
$PIP_CMD install -r requirements.txt

echo "3. Запуск FastAPI приложения..."
$PYTHON_CMD app.py &
APP_PID=$!
echo "Приложение запущено (PID: $APP_PID)"
echo "   Проверяем доступность..."
sleep 3

if ! curl -s http://localhost:8000/ > /dev/null; then
    echo "ОШИБКА: Приложение не запустилось. Проверьте ошибки выше."
    kill $APP_PID 2>/dev/null
    exit 1
fi

echo "ПРИЛОЖЕНИЕ ДОСТУПНО: http://localhost:8000"

run_test() {
    local scenario=$1
    local users=$2
    local spawn_rate=$3
    local duration=$4
    
    echo ""
    echo "Запуск сценария: $scenario"
    echo "   Пользователей: $users, Скорость роста: $spawn_rate/сек, Длительность: $duration"
    
    if ! command -v locust &> /dev/null; then
        LOCUST_CMD="$PYTHON_CMD -m locust"
        echo "   Используем: $LOCUST_CMD"
    else
        LOCUST_CMD="locust"
    fi
    
    $LOCUST_CMD -f locustfile.py \
        --host=http://localhost:8000 \
        --users=$users \
        --spawn-rate=$spawn_rate \
        --run-time=$duration \
        --headless \
        --csv=results/${scenario} \
        --html=results/${scenario}_report.html 2>&1
    
    echo "Сценарий $scenario завершен"
}

mkdir -p results

echo ""
echo "4. Запуск сценариев тестирования..."
echo "=================================="

run_test "sanity_check" 10 1 "1m"

run_test "normal_load" 50 5 "5m"

run_test "peak_load" 200 20 "3m"

# Длительная нагрузка (комментируем для быстрого теста)
# run_test "endurance" 100 10 "30m"

echo ""
echo "Быстрый тест с разной нагрузкой..."
for users in 10 30 50 100; do
    echo "   Тест с $users пользователями (30 секунд)..."
    
    if command -v locust &> /dev/null; then
        LOCUST_CMD="locust"
    else
        LOCUST_CMD="$PYTHON_CMD -m locust"
    fi
    
    $LOCUST_CMD -f locustfile.py \
        --host=http://localhost:8000 \
        --users=$users \
        --spawn-rate=10 \
        --run-time="30s" \
        --headless \
        --csv=results/ramp_up_${users}users \
        --only-summary 2>&1 | grep -E "(Average|FAILURE|RPS)"
done

echo ""
echo "5. Остановка приложения..."
kill $APP_PID 2>/dev/null
wait $APP_PID 2>/dev/null

echo ""
echo "ТЕСТИРОВАНИЕ ЗАВЕРШЕНО!"
echo "Результаты сохранены в папке 'results/'"
echo ""
echo "Для просмотра отчетов:"
echo "   - Откройте в браузере: results/normal_load_report.html"
echo "   - Или посмотрите CSV файлы: results/*_stats.csv"
echo ""
echo "Пример просмотра результатов:"
echo "   cat results/normal_load_stats.csv | head -5"
echo ""

echo ""
echo "==============================================="
echo "РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ"
echo "==============================================="
echo ""

if [ -d "results" ] && [ "$(ls -A results/*_stats.csv 2>/dev/null)" ]; then
    echo "Детальные результаты по сценариям:"
    echo "----------------------------------------------------------------------"

    echo "+--------------------+-----------+-----------+------------+-----------+-----------+"
    echo "| Сценарий           | Пользоват.| RPS (ср.) | Ср. время  | p95 (ms)  | Ошибки    |"
    echo "|                    |           |           | ответа(ms) |           |           |"
    echo "+--------------------+-----------+-----------+------------+-----------+-----------+"
    
    for csv_file in results/*_stats.csv; do
        if [ -f "$csv_file" ]; then
            scenario_name=$(basename "$csv_file" _stats.csv)
            
            if [ -f "$csv_file" ] && [ $(wc -l < "$csv_file") -gt 1 ]; then
                rps=$(awk -F, 'NR==2 {printf "%.1f", $4}' "$csv_file" 2>/dev/null || echo "N/A")
                avg_response=$(awk -F, 'NR==2 {printf "%.0f", $5}' "$csv_file" 2>/dev/null || echo "N/A")
                p95=$(awk -F, 'NR==2 {printf "%.0f", $7}' "$csv_file" 2>/dev/null || echo "N/A")
                failures=$(awk -F, 'NR==2 {print $8}' "$csv_file" 2>/dev/null || echo "N/A")
                requests=$(awk -F, 'NR==2 {print $2}' "$csv_file" 2>/dev/null || echo "N/A")

                case "$scenario_name" in
                    sanity_check) users=10 ;;
                    normal_load) users=50 ;;
                    peak_load) users=200 ;;
                    ramp_up_10users) users=10 ;;
                    ramp_up_30users) users=30 ;;
                    ramp_up_50users) users=50 ;;
                    ramp_up_100users) users=100 ;;
                    *) users="N/A" ;;
                esac
                
                printf "| %-18s | %-9s | %-9s | %-10s | %-9s | %-9s |\n" \
                    "$scenario_name" "$users" "$rps" "$avg_response" "$p95" "$failures"
            fi
        fi
    done
    
    echo "+--------------------+-----------+-----------+------------+-----------+-----------+"
    echo ""
    
    echo "Сводка по сценариям:"
    echo "----------------------------------------------------------------------"
    
    for scenario in sanity_check normal_load peak_load; do
        if [ -f "results/${scenario}_stats.csv" ]; then
            echo ""
            echo "Сценарий: $scenario"
            echo "  - Всего запросов: $(awk -F, 'NR==2 {print $2}' results/${scenario}_stats.csv 2>/dev/null || echo 'N/A')"
            echo "  - Запросов в секунду: $(awk -F, 'NR==2 {printf "%.1f", $4}' results/${scenario}_stats.csv 2>/dev/null || echo 'N/A')"
            echo "  - Среднее время ответа: $(awk -F, 'NR==2 {printf "%.0f ms", $5}' results/${scenario}_stats.csv 2>/dev/null || echo 'N/A')"
            echo "  - 95-й процентиль: $(awk -F, 'NR==2 {printf "%.0f ms", $7}' results/${scenario}_stats.csv 2>/dev/null || echo 'N/A')"
            echo "  - Количество ошибок: $(awk -F, 'NR==2 {print $8}' results/${scenario}_stats.csv 2>/dev/null || echo 'N/A')"
            
            if [ -f "results/${scenario}_failures.csv" ]; then
                failure_count=$(wc -l < "results/${scenario}_failures.csv" 2>/dev/null)
                if [ "$failure_count" -gt 1 ]; then
                    echo "  - Типы ошибок:"
                    tail -n +2 "results/${scenario}_failures.csv" | head -5 | while IFS=, read -r method name error count; do
                        echo "    * $error (количество: $count)"
                    done
                fi
            fi
        fi
    done
    
    echo ""
    echo "Файлы с результатами:"
    echo "----------------------------------------------------------------------"
    ls -la results/*.csv results/*.html 2>/dev/null | awk '{print "  - " $9 " (" $5 " bytes)"}'
    
    echo ""
    echo "Для детального анализа откройте HTML отчеты:"
    echo "  - results/sanity_check_report.html - проверка работоспособности"
    echo "  - results/normal_load_report.html  - нормальная нагрузка"
    echo "  - results/peak_load_report.html    - пиковая нагрузка"
    
else
    echo "РЕЗУЛЬТАТЫ НЕ НАЙДЕНЫ."
    echo "Возможные причины:"
    echo "  1. Тесты не были выполнены успешно"
    echo "  2. Файлы результатов не были созданы"
    echo "  3. Папка 'results' не существует"
    echo ""
    echo "Проверьте сообщения об ошибках выше."
fi

echo ""
echo "==============================================="
echo "ТЕСТИРОВАНИЕ ЗАВЕРШЕНО - $(date)"
echo "==============================================="
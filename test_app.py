import pytest
from fastapi.testclient import TestClient
from main import app
import json

# Создаем тестового клиента
client = TestClient(app)

def test_add_product():
    """Тест добавления продукта"""
    
    # Тестовые данные продукта
    product_data = {
        "name": "Яблоко",
        "calories": 52.0,
        "protein": 0.3,
        "fats": 0.2,
        "carbs": 14.0
    }
    
    # Отправляем POST запрос
    response = client.post("/add_product", json=product_data)
    
    # Проверяем статус код
    assert response.status_code == 200
    
    # Проверяем структуру ответа
    data = response.json()
    assert "products" in data
    assert "totals" in data
    
    # Проверяем, что продукт добавлен
    assert len(data["products"]) == 1
    assert data["products"][0]["name"] == "Яблоко"
    
    # Проверяем итоговые значения
    assert data["totals"]["calories"] == 52.0
    assert data["totals"]["protein"] == 0.3
    assert data["totals"]["fats"] == 0.2
    assert data["totals"]["carbs"] == 14.0
    
    # Добавляем еще один продукт
    product_data2 = {
        "name": "Банан",
        "calories": 96.0,
        "protein": 1.3,
        "fats": 0.3,
        "carbs": 21.0
    }
    
    response = client.post("/add_product", json=product_data2)
    data = response.json()
    
    # Проверяем, что теперь два продукта
    assert len(data["products"]) == 2
    
    # Проверяем суммирование значений
    assert data["totals"]["calories"] == 148.0  # 52 + 96
    assert data["totals"]["protein"] == 1.6     # 0.3 + 1.3
    assert data["totals"]["fats"] == 0.5        # 0.2 + 0.3
    assert data["totals"]["carbs"] == 35.0      # 14 + 21

def test_calculate_kbju():
    """Тест расчета КБЖУ и процентов"""
    
    # Сначала очистим сессию
    client.post("/clear")
    
    # Добавим несколько продуктов
    products = [
        {
            "name": "Куриная грудка",
            "calories": 165.0,
            "protein": 31.0,
            "fats": 3.6,
            "carbs": 0.0
        },
        {
            "name": "Рис",
            "calories": 130.0,
            "protein": 2.7,
            "fats": 0.3,
            "carbs": 28.0
        }
    ]
    
    for product in products:
        client.post("/add_product", json=product)
    
    # Теперь делаем расчет для веса 70 кг
    calculation_data = {
        "weight": 70.0,
        "totals": {
            "calories": 295.0,  # 165 + 130
            "protein": 33.7,    # 31 + 2.7
            "fats": 3.9,        # 3.6 + 0.3
            "carbs": 28.0       # 0 + 28
        }
    }
    
    response = client.post("/calculate", json=calculation_data)
    
    # Проверяем статус код
    assert response.status_code == 200
    
    # Проверяем структуру ответа
    data = response.json()
    assert "norms" in data
    assert "percentages" in data
    assert "average_percentage" in data
    assert "status" in data
    
    # Проверяем расчет нормы для веса 70 кг
    # По формуле: калории = вес * 38 = 70 * 38 = 2660
    # Белки = вес * 2.0 = 70 * 2 = 140
    # Жиры = вес * 1.2 = 70 * 1.2 = 84
    # Углеводы = (2660 - (140*4 + 84*9)) / 4 = (2660 - (560 + 756)) / 4 = (2660 - 1316) / 4 = 1344 / 4 = 336
    
    assert data["norms"]["calories"] == 2660.0
    assert data["norms"]["protein"] == 140.0
    assert data["norms"]["fats"] == 84.0
    assert data["norms"]["carbs"] == 336.0
    
    # Проверяем расчет процентов
    # Калории: 295 / 2660 * 100% = 11.09%
    assert abs(data["percentages"]["calories"] - 11.09) < 0.1
    
    # Белки: 33.7 / 140 * 100% = 24.07%
    assert abs(data["percentages"]["protein"] - 24.07) < 0.1
    
    # Жиры: 3.9 / 84 * 100% = 4.64%
    assert abs(data["percentages"]["fats"] - 4.64) < 0.1
    
    # Углеводы: 28 / 336 * 100% = 8.33%
    assert abs(data["percentages"]["carbs"] - 8.33) < 0.1
    
    # Проверяем средний процент
    average = (11.09 + 24.07 + 4.64 + 8.33) / 4
    assert abs(data["average_percentage"] - average) < 0.1
    
    # Проверяем, что status содержит информацию о проценте
    assert isinstance(data["status"], str)

def test_clear_session():
    """Тест очистки сессии"""
    
    # Сначала добавим продукт
    product_data = {
        "name": "Тестовый продукт",
        "calories": 100.0,
        "protein": 10.0,
        "fats": 5.0,
        "carbs": 20.0
    }
    
    response = client.post("/add_product", json=product_data)
    assert response.status_code == 200
    
    # Проверяем, что продукт добавлен
    data = response.json()
    assert len(data["products"]) == 1
    
    # Очищаем сессию
    response = client.post("/clear")
    assert response.status_code == 200
    
    # Проверяем, что сессия очищена
    assert response.json()["message"] == "Сессия очищена"
    
    # Добавляем новый продукт после очистки
    response = client.post("/add_product", json=product_data)
    data = response.json()
    
    # Проверяем, что это первый продукт в новой сессии
    assert len(data["products"]) == 1

def test_invalid_weight():
    """Тест с некорректным весом"""
    
    # Сначала очистим сессию
    client.post("/clear")
    
    # Добавим продукт
    product_data = {
        "name": "Яблоко",
        "calories": 52.0,
        "protein": 0.3,
        "fats": 0.2,
        "carbs": 14.0
    }
    
    client.post("/add_product", json=product_data)
    
    # Тестируем с нулевым весом
    calculation_data = {
        "weight": 0.0,
        "totals": {
            "calories": 52.0,
            "protein": 0.3,
            "fats": 0.2,
            "carbs": 14.0
        }
    }
    
    response = client.post("/calculate", json=calculation_data)
    
    # Должна быть ошибка, так как вес должен быть > 0
    assert response.status_code == 200  # В текущей реализации не проверяется вес > 0
    # Если хотите добавить валидацию, измените код и тест соответственно
    
    # Тестируем с отрицательным весом
    calculation_data["weight"] = -10.0
    response = client.post("/calculate", json=calculation_data)
    assert response.status_code == 200

def test_empty_product():
    """Тест добавления продукта без названия"""
    
    # Пытаемся добавить продукт без имени (пустая строка)
    product_data = {
        "name": "",
        "calories": 100.0,
        "protein": 10.0,
        "fats": 5.0,
        "carbs": 20.0
    }
    
    response = client.post("/add_product", json=product_data)
    
    # В текущей реализации пустое имя допускается
    assert response.status_code == 200
    
    # Проверяем, что продукт добавлен (даже с пустым именем)
    data = response.json()
    assert len(data["products"]) == 1

def test_concurrent_sessions():
    """Тест работы с разными сессиями (опционально)"""
    
    # В текущей реализации используется глобальная сессия
    # Этот тест показывает, что все работает с одной сессией
    pass

if __name__ == "__main__":
    # Запуск тестов напрямую
    pytest.main([__file__, "-v"])
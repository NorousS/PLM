from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

app = FastAPI(title="КБЖУ калькулятор")

# Модели данных
class Product(BaseModel):
    name: str
    calories: float
    protein: float
    fats: float
    carbs: float

class SessionData(BaseModel):
    weight: float
    products: List[Product] = []
    total_calories: float = 0
    total_protein: float = 0
    total_fats: float = 0
    total_carbs: float = 0

# Храним сессии в памяти (без БД)
sessions = {}

def calculate_norms(weight: float):
    """Расчет нормы КБЖУ для набора массы"""
    # Простая формула: 35-40 ккал на кг веса для набора массы
    calories_norm = weight * 38
    
    # Белки: 1.8-2.2 г на кг
    protein_norm = weight * 2.0
    
    # Жиры: 1-1.5 г на кг
    fats_norm = weight * 1.2
    
    # Углеводы: остаток калорий
    # (калории - (белки*4 + жиры*9)) / 4
    carbs_calories = calories_norm - (protein_norm * 4 + fats_norm * 9)
    carbs_norm = carbs_calories / 4
    
    return {
        "calories": round(calories_norm, 1),
        "protein": round(protein_norm, 1),
        "fats": round(fats_norm, 1),
        "carbs": round(carbs_norm, 1)
    }

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Главная страница"""
    return """
    <html>
        <head>
            <title>Калькулятор КБЖУ</title>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                .container { display: flex; gap: 30px; }
                .section { flex: 1; border: 1px solid #ddd; padding: 20px; border-radius: 5px; }
                input { width: 100%; padding: 8px; margin: 5px 0 15px 0; }
                button { padding: 10px 20px; background: #4CAF50; color: white; border: none; cursor: pointer; }
                .result { margin-top: 20px; padding: 15px; background: #f5f5f5; border-radius: 5px; }
                .progress-bar { height: 20px; background: #e0e0e0; border-radius: 10px; margin: 10px 0; }
                .progress { height: 100%; background: #4CAF50; border-radius: 10px; }
                .product-item { padding: 5px; border-bottom: 1px solid #eee; }
            </style>
        </head>
        <body>
            <h1>Калькулятор суточной нормы КБЖУ</h1>
            <div class="container">
                <div class="section">
                    <h2>Ввод данных</h2>
                    <label>Ваш вес (кг):</label>
                    <input type="number" id="weight" step="0.1" placeholder="70">
                    
                    <h3>Добавить продукт:</h3>
                    <input type="text" id="productName" placeholder="Название продукта">
                    <label>Калории:</label>
                    <input type="number" id="calories" step="0.1" placeholder="0">
                    <label>Белки (г):</label>
                    <input type="number" id="protein" step="0.1" placeholder="0">
                    <label>Жиры (г):</label>
                    <input type="number" id="fats" step="0.1" placeholder="0">
                    <label>Углеводы (г):</label>
                    <input type="number" id="carbs" step="0.1" placeholder="0">
                    
                    <button onclick="addProduct()">Добавить продукт</button>
                    <button onclick="calculate()">Рассчитать</button>
                    <button onclick="clearSession()" style="background: #f44336;">Очистить</button>
                </div>
                
                <div class="section">
                    <h2>Результаты</h2>
                    <div id="results"></div>
                    <h3>Добавленные продукты:</h3>
                    <div id="productsList"></div>
                </div>
            </div>
            
            <script src="/static/script.js"></script>
        </body>
    </html>
    """

@app.post("/api/calculate")
async def calculate_kbju(data: dict):
    """Расчет процента от нормы"""
    weight = data.get("weight", 0)
    current = data.get("current", {})
    
    # Расчет нормы
    norms = calculate_norms(weight)
    
    # Расчет процентов
    percentages = {}
    for key in ["calories", "protein", "fats", "carbs"]:
        if norms[key] > 0:
            percentage = (current.get(key, 0) / norms[key]) * 100
            percentages[key] = round(min(percentage, 100), 1)
        else:
            percentages[key] = 0
    
    # Средний процент
    avg_percentage = round(sum(percentages.values()) / len(percentages), 1)
    
    return {
        "norms": norms,
        "percentages": percentages,
        "average": avg_percentage,
        "current": current
    }

@app.post("/api/add_product")
async def add_product(data: dict):
    """Добавление продукта в сессию"""
    session_id = data.get("session_id", "default")
    
    if session_id not in sessions:
        sessions[session_id] = SessionData(weight=0)
    
    product = Product(
        name=data["name"],
        calories=data["calories"],
        protein=data["protein"],
        fats=data["fats"],
        carbs=data["carbs"]
    )
    
    sessions[session_id].products.append(product)
    sessions[session_id].total_calories += product.calories
    sessions[session_id].total_protein += product.protein
    sessions[session_id].total_fats += product.fats
    sessions[session_id].total_carbs += product.carbs
    
    return {
        "total": {
            "calories": sessions[session_id].total_calories,
            "protein": sessions[session_id].total_protein,
            "fats": sessions[session_id].total_fats,
            "carbs": sessions[session_id].total_carbs
        },
        "products": [p.dict() for p in sessions[session_id].products]
    }

@app.post("/api/clear_session")
async def clear_session(data: dict):
    """Очистка сессии"""
    session_id = data.get("session_id", "default")
    if session_id in sessions:
        sessions[session_id] = SessionData(weight=0)
    return {"status": "cleared"}

# Статические файлы
app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
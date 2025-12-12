let sessionProducts = [];
let currentTotals = {
    calories: 0,
    protein: 0,
    fats: 0,
    carbs: 0
};

async function addProduct() {
    const product = {
        name: document.getElementById('productName').value || 'Без названия',
        calories: parseFloat(document.getElementById('calories').value) || 0,
        protein: parseFloat(document.getElementById('protein').value) || 0,
        fats: parseFloat(document.getElementById('fats').value) || 0,
        carbs: parseFloat(document.getElementById('carbs').value) || 0,
        session_id: 'default'
    };
    
    try {
        const response = await fetch('/api/add_product', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(product)
        });
        
        const data = await response.json();
        currentTotals = data.total;
        sessionProducts = data.products;
        
        updateProductsList();
        clearInputs();
    } catch (error) {
        console.error('Error:', error);
    }
}

async function calculate() {
    const weight = parseFloat(document.getElementById('weight').value);
    
    if (!weight || weight <= 0) {
        alert('Введите корректный вес');
        return;
    }
    
    try {
        const response = await fetch('/api/calculate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                weight: weight,
                current: currentTotals
            })
        });
        
        const data = await response.json();
        displayResults(data);
    } catch (error) {
        console.error('Error:', error);
    }
}

function displayResults(data) {
    const resultsDiv = document.getElementById('results');
    
    let html = `
        <h3>Ваша норма для набора массы (вес: ${document.getElementById('weight').value} кг):</h3>
        <p>Калории: ${data.norms.calories} ккал</p>
        <p>Белки: ${data.norms.protein} г</p>
        <p>Жиры: ${data.norms.fats} г</p>
        <p>Углеводы: ${data.norms.carbs} г</p>
        
        <h3>Текущее потребление:</h3>
        <p>Калории: ${currentTotals.calories} ккал</p>
        <p>Белки: ${currentTotals.protein} г</p>
        <p>Жиры: ${currentTotals.fats} г</p>
        <p>Углеводы: ${currentTotals.carbs} г</p>
        
        <h3>Процент от нормы:</h3>
    `;
    
    // Проценты для каждого компонента
    const components = [
        { name: 'Калории', percent: data.percentages.calories },
        { name: 'Белки', percent: data.percentages.protein },
        { name: 'Жиры', percent: data.percentages.fats },
        { name: 'Углеводы', percent: data.percentages.carbs }
    ];
    
    components.forEach(comp => {
        html += `
            <p>${comp.name}: ${comp.percent}%</p>
            <div class="progress-bar">
                <div class="progress" style="width: ${Math.min(comp.percent, 100)}%"></div>
            </div>
        `;
    });
    
    html += `<h3>Средний процент: ${data.average}%</h3>`;
    
    if (data.average >= 100) {
        html += `<p style="color: green; font-weight: bold;">✓ Норма достигнута!</p>`;
    } else {
        html += `<p style="color: orange;">⏳ Норма еще не достигнута</p>`;
    }
    
    resultsDiv.innerHTML = html;
}

function updateProductsList() {
    const listDiv = document.getElementById('productsList');
    
    if (sessionProducts.length === 0) {
        listDiv.innerHTML = '<p>Нет добавленных продуктов</p>';
        return;
    }
    
    let html = '<div>';
    sessionProducts.forEach((product, index) => {
        html += `
            <div class="product-item">
                <strong>${product.name}</strong><br>
                К: ${product.calories} | Б: ${product.protein} | Ж: ${product.fats} | У: ${product.carbs}
            </div>
        `;
    });
    
    html += `
        <div style="margin-top: 10px; padding-top: 10px; border-top: 2px solid #333;">
            <strong>Итого:</strong><br>
            Калории: ${currentTotals.calories} | 
            Белки: ${currentTotals.protein} | 
            Жиры: ${currentTotals.fats} | 
            Углеводы: ${currentTotals.carbs}
        </div>
    `;
    
    listDiv.innerHTML = html;
}

function clearInputs() {
    document.getElementById('productName').value = '';
    document.getElementById('calories').value = '';
    document.getElementById('protein').value = '';
    document.getElementById('fats').value = '';
    document.getElementById('carbs').value = '';
}

async function clearSession() {
    try {
        await fetch('/api/clear_session', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ session_id: 'default' })
        });
        
        sessionProducts = [];
        currentTotals = { calories: 0, protein: 0, fats: 0, carbs: 0 };
        document.getElementById('results').innerHTML = '';
        updateProductsList();
    } catch (error) {
        console.error('Error:', error);
    }
}

// Инициализация
document.addEventListener('DOMContentLoaded', function() {
    updateProductsList();
});
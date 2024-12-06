// static/script.js
document.addEventListener('DOMContentLoaded', function() {
    // Navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', () => {
            document.querySelectorAll('.nav-item').forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');
            
            const step = item.dataset.step;
            document.querySelectorAll('.panel').forEach(panel => panel.classList.remove('active'));
            document.querySelector(`.${step}-panel`).classList.add('active');
        });
    });
    
    // Number input controls
    document.querySelectorAll('.number-input').forEach(wrapper => {
        const input = wrapper.querySelector('input');
        const decrease = wrapper.querySelector('.decrease');
        const increase = wrapper.querySelector('.increase');
        
        decrease.addEventListener('click', () => {
            if (input.value > parseInt(input.min)) {
                input.value = parseInt(input.value) - 1;
                input.dispatchEvent(new Event('change'));
            }
        });
        
        increase.addEventListener('click', () => {
            if (input.value < parseInt(input.max)) {
                input.value = parseInt(input.value) + 1;
                input.dispatchEvent(new Event('change'));
            }
        });
    });
    
    function updateMatrices() {
        const sources = parseInt(document.getElementById('sources').value);
        const destinations = parseInt(document.getElementById('destinations').value);
        
        const costsMatrix = document.getElementById('costs-matrix');
        costsMatrix.style.gridTemplateColumns = `repeat(${destinations}, 1fr)`;
        costsMatrix.innerHTML = '';
        
        for (let i = 0; i < sources; i++) {
            for (let j = 0; j < destinations; j++) {
                const input = document.createElement('input');
                input.type = 'number';
                input.min = '0';
                input.className = 'cost-cell';
                input.placeholder = `O${i+1}→D${j+1}`;
                costsMatrix.appendChild(input);
            }
        }
        
        const supplyVector = document.getElementById('supply-vector');
        supplyVector.innerHTML = '';
        for (let i = 0; i < sources; i++) {
            const input = document.createElement('input');
            input.type = 'number';
            input.min = '0';
            input.className = 'supply-cell';
            input.placeholder = `Origen ${i+1}`;
            supplyVector.appendChild(input);
        }
        
        const demandVector = document.getElementById('demand-vector');
        demandVector.innerHTML = '';
        for (let j = 0; j < destinations; j++) {
            const input = document.createElement('input');
            input.type = 'number';
            input.min = '0';
            input.className = 'demand-cell';
            input.placeholder = `Destino ${j+1}`;
            demandVector.appendChild(input);
        }
    }
    
    document.getElementById('sources').addEventListener('change', updateMatrices);
    document.getElementById('destinations').addEventListener('change', updateMatrices);
    
    // Optimize button handler
    document.getElementById('optimize').addEventListener('click', async function() {
        const sources = parseInt(document.getElementById('sources').value);
        const destinations = parseInt(document.getElementById('destinations').value);
        
        // Get costs matrix
        const costs = [];
        const costInputs = document.querySelectorAll('.cost-cell');
        for (let i = 0; i < sources; i++) {
            const row = [];
            for (let j = 0; j < destinations; j++) {
                const value = parseFloat(costInputs[i * destinations + j].value);
                row.push(isNaN(value) ? 0 : value);
            }
            costs.push(row);
        }
        
        // Get supply and demand vectors
        const supply = Array.from(document.querySelectorAll('.supply-cell'))
            .map(input => {
                const value = parseFloat(input.value);
                return isNaN(value) ? 0 : value;
            });
            
        const demand = Array.from(document.querySelectorAll('.demand-cell'))
            .map(input => {
                const value = parseFloat(input.value);
                return isNaN(value) ? 0 : value;
            });
        
        try {
            const response = await fetch('/optimize', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    costs: costs,
                    supply: supply,
                    demand: demand,
                    method: 'minimum_cost'  // northwest vogel o minimum cost
                })
            });
            
            if (!response.ok) {
                throw new Error('Error en la optimización');
            }
            
            const result = await response.json();
            
            // Display total cost
            document.getElementById('total-cost').textContent = 
                result.total_cost.toFixed(2);
            
            // Display solution matrix
            const solutionMatrix = document.getElementById('solution-matrix');
            solutionMatrix.style.gridTemplateColumns = `repeat(${destinations}, 1fr)`;
            solutionMatrix.innerHTML = '';
            
            for (let i = 0; i < sources; i++) {
                for (let j = 0; j < destinations; j++) {
                    const cell = document.createElement('div');
                    cell.className = 'solution-cell';
                    const value = result.solution[i][j];
                    cell.textContent = Math.abs(value) < 0.0001 ? '-' : value.toFixed(3);
                    solutionMatrix.appendChild(cell);
                }
            }
            
            // Switch to solution panel
            document.querySelector('[data-step="solution"]').click();
            
        } catch (error) {
            alert('Error al procesar la optimización: ' + error.message);
        }
    });
    
    // Initialize matrices
    updateMatrices();
});
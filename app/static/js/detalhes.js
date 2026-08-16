// ==========================================
// 1. LOG DE INICIALIZAÇÃO E LISTENERS
// ==========================================
console.log("🔥 SCRIPT DETALHES.JS CARREGADO!");

document.addEventListener("DOMContentLoaded", () => {
    console.log("⚡ DOM LOADED - Iniciando montagem da tela...");
    
    carregarDetalhesUsina();

    const btnAtualizar = document.getElementById('btnAtualizarDataloggers');
    if (btnAtualizar) {
        btnAtualizar.addEventListener('click', () => {
            console.log("🖱️ Botão de atualizar clicado!");
            carregarDetalhesUsina();
        });
    }
});

let chartInstance = null;
let chartHistoricoInstance = null; // Nova variável para o gráfico de barras

// ==========================================
// 2. FUNÇÃO PRINCIPAL DE BUSCA (API)
// ==========================================
async function carregarDetalhesUsina() {
    const container = document.getElementById('container-detalhes-usina');
    if (!container) return;

    container.innerHTML = '<div class="loading-state"><p>Buscando telemetria avançada da usina...</p></div>';

    try {
        if (!window.AppConfig || !window.AppConfig.marcaUsina || !window.AppConfig.plantId) {
            throw new Error("As variáveis da usina não foram carregadas corretamente pelo servidor.");
        }

        const url = `/api/${window.AppConfig.marcaUsina}/dataloggers/${window.AppConfig.plantId}`;
        const response = await fetch(url);

        if (!response.ok) {
            let errorMsg = `Erro HTTP ${response.status}`;
            try {
                const errData = await response.json();
                errorMsg = errData.detail || errorMsg;
            } catch(e) {}
            throw new Error(errorMsg);
        }

        const data = await response.json();
        console.log("📦 Dados recebidos:", data);
        
        // --- 1. PREPARA OS CARDS DE FLUXO E BATERIA ---
        let htmlFluxo = "";
        const f = data.fluxo || {};
        
        if (f.battery_soc !== undefined) {
            htmlFluxo += `
                <div class="kpi-card" style="border-left: 4px solid #8b5cf6;">
                    <span class="kpi-label" style="color: #8b5cf6;">Bateria (SOC)</span>
                    <span class="kpi-value" style="color: #8b5cf6;">${f.battery_soc} <span class="kpi-unit" style="color: #a78bfa;">%</span></span>
                    <span class="kpi-unit" style="margin-top: 4px; font-size: 0.75rem;">
                        ${f.charge_power ? `↑ Carg: ${f.charge_power}kW` : ''} 
                        ${f.discharge_power ? `↓ Desc: ${f.discharge_power}kW` : ''}
                    </span>
                </div>
            `;
        }
        
        if (f.consumption_power !== undefined) {
            htmlFluxo += `
                <div class="kpi-card" style="border-left: 4px solid #f59e0b;">
                    <span class="kpi-label" style="color: #f59e0b;">Consumo Local</span>
                    <span class="kpi-value" style="color: #f59e0b;">${f.consumption_power} <span class="kpi-unit" style="color: #fbbf24;">kW</span></span>
                    <span class="kpi-unit" style="margin-top: 4px; font-size: 0.75rem;">
                        ${f.purchase_power ? `↓ Rede: ${f.purchase_power}kW` : ''} 
                        ${f.grid_power ? `↑ Injetando: ${f.grid_power}kW` : ''}
                    </span>
                </div>
            `;
        }

        // --- 2. RENDERIZA A ESTRUTURA PRINCIPAL ---
        const tipoInstalacaoStr = data.installation_type === 'HOUSE_ROOF' ? 'Residencial' : (data.installation_type || 'N/A');
        const injecaoStr = data.interconnection_type === 'EXCESS' ? '(Injeção de Excedente)' : '';

        container.innerHTML = `
            <div class="kpi-grid">
                <div class="kpi-card">
                    <span class="kpi-label">Potência Atual</span>
                    <span class="kpi-value valor-destaque-azul">${data.current_power || 0} <span class="kpi-unit">kW</span></span>
                </div>
                <div class="kpi-card">
                    <span class="kpi-label">Energia Hoje</span>
                    <span class="kpi-value valor-destaque-verde">${data.daily_energy || 0} <span class="kpi-unit">kWh</span></span>
                </div>
                <div class="kpi-card">
                    <span class="kpi-label">Energia Mês</span>
                    <span class="kpi-value">${data.monthly_energy || 0} <span class="kpi-unit">kWh</span></span>
                </div>
                <div class="kpi-card">
                    <span class="kpi-label">Energia Total</span>
                    <span class="kpi-value">${data.total_energy || 0} <span class="kpi-unit">kWh</span></span>
                </div>
                ${htmlFluxo}
            </div>

            <!-- Gráfico 1: Curva de Geração (Hoje) -->
            <div class="chart-container" style="margin-top: 24px; background: var(--bg-card); padding: 20px; border-radius: 8px; box-shadow: var(--card-shadow); border: 1px solid var(--border-subtle);">
                
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px;">
                    <h3 style="font-size: 14px; font-weight: 500; color: var(--text-main); margin: 0;">Curva de Geração (Hoje)</h3>
                    
                    <div style="text-align: right; font-size: 0.75rem; color: var(--text-muted); line-height: 1.4;">
                        Ativação: <strong style="color: var(--text-main);">${data.start_date || 'N/A'}</strong><br>
                        Sistema: <strong style="color: var(--text-main);">${tipoInstalacaoStr}</strong> ${injecaoStr}
                    </div>
                </div>
                
                <div style="position: relative; height: 300px; width: 100%;">
                    <canvas id="geracaoChart"></canvas>
                </div>
            </div>

            <!-- Gráfico 2: Histórico do Mês -->
            <div class="chart-container" style="margin-top: 24px; background: var(--bg-card); padding: 20px; border-radius: 8px; box-shadow: var(--card-shadow); border: 1px solid var(--border-subtle);">
                <h3 style="font-size: 14px; font-weight: 500; color: var(--text-main); margin-bottom: 16px;">Histórico de Geração (Dias do Mês)</h3>
                <div style="position: relative; height: 300px; width: 100%;">
                    <canvas id="historicoChart"></canvas>
                </div>
            </div>

            <div id="tabela-inversores-wrapper" style="margin-top: 24px;"></div>
        `;

        // --- 3. RENDERIZA OS COMPONENTES EXTRAS ---
        if (data.chart && data.chart.length > 0) {
            renderizarGrafico(data.chart);
        } else {
            document.getElementById('geracaoChart').parentElement.innerHTML = '<p style="text-align:center; color: var(--text-muted); font-size: 13px; margin-top: 40px;">Nenhum dado de geração registrado para o dia de hoje.</p>';
        }

        // NOVO: Renderiza o gráfico de Histórico Mensal
        if (data.history_chart && data.history_chart.length > 0) {
            renderizarGraficoHistorico(data.history_chart);
        } else {
            document.getElementById('historicoChart').parentElement.innerHTML = '<p style="text-align:center; color: var(--text-muted); font-size: 13px; margin-top: 40px;">Nenhum histórico registrado para este mês.</p>';
        }

        if (data.dataloggers && data.dataloggers.length > 0) {
            renderizarTabela(data.dataloggers);
        } else {
            document.getElementById('tabela-inversores-wrapper').innerHTML = `
                <div class="loading-state" style="margin-top: 20px;">
                    <p>Nenhum equipamento vinculado a esta usina.</p>
                </div>`;
        }

    } catch (error) {
        console.error("❌ ERRO GRAVE:", error);
        container.innerHTML = `
            <div class="error-state">
                <h3 style="color: var(--text-main); font-weight: 400; margin-bottom: 12px; font-size: 1.1rem;">Falha de Comunicação</h3>
                <p>Erro ao obter dados detalhados.</p>
                <p style="font-size: 0.8rem; margin-top: 16px; color: var(--status-offline); opacity: 0.8;">Detalhes: ${error.message}</p>
            </div>`;
    }
}

// ==========================================
// 3. FUNÇÕES DE RENDERIZAÇÃO SECUNDÁRIAS
// ==========================================
function renderizarGrafico(chartData) {
    try {
        const canvas = document.getElementById('geracaoChart');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        
        const labels = chartData.map(item => {
            let dateObj;
            if (typeof item.time === 'number') {
                dateObj = new Date(item.time > 9999999999 ? item.time : item.time * 1000);
            } else {
                dateObj = new Date(item.time);
            }
            return `${String(dateObj.getHours()).padStart(2, '0')}:${String(dateObj.getMinutes()).padStart(2, '0')}`;
        });

        const values = chartData.map(item => item.power);

        if (chartInstance) chartInstance.destroy();

        chartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Potência (kW)',
                    data: values,
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    borderWidth: 2,
                    pointRadius: 1,
                    pointHoverRadius: 5,
                    fill: true,
                    tension: 0.3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { 
                    x: { grid: { display: false } }, 
                    y: { beginAtZero: true } 
                }
            }
        });
    } catch (e) {
        console.error("❌ ERRO AO RENDERIZAR GRÁFICO:", e);
    }
}

// NOVA FUNÇÃO: Renderiza o gráfico de barras (Histórico Mensal)
function renderizarGraficoHistorico(chartData) {
    try {
        const canvas = document.getElementById('historicoChart');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        
        // Tratamento da Data blindado contra fuso horário (Timezone UTC)
        const labels = chartData.map(item => {
            let dateObj;
            if (typeof item.time === 'number') {
                dateObj = new Date(item.time > 9999999999 ? item.time : item.time * 1000);
            } else if (typeof item.time === 'string') {
                // Se for string "2026-08-15", forçamos para meio-dia para evitar que o UTC-4 empurre para o dia 14
                const safeTimeStr = item.time.includes('T') ? item.time : item.time + 'T12:00:00';
                dateObj = new Date(safeTimeStr);
            } else {
                dateObj = new Date();
            }
            return `${String(dateObj.getDate()).padStart(2, '0')}/${String(dateObj.getMonth() + 1).padStart(2, '0')}`;
        });

        const values = chartData.map(item => item.energy);

        if (chartHistoricoInstance) chartHistoricoInstance.destroy();

        chartHistoricoInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Energia (kWh)',
                    data: values,
                    backgroundColor: 'rgba(16, 185, 129, 0.8)',
                    borderRadius: 4,
                    borderWidth: 0,
                    barPercentage: 0.6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { 
                    x: { grid: { display: false } }, 
                    y: { beginAtZero: true, grid: { color: 'rgba(0,0,0,0.05)' } } 
                }
            }
        });
    } catch (e) {
        console.error("❌ ERRO AO RENDERIZAR GRÁFICO DE HISTÓRICO:", e);
    }
}

function renderizarTabela(dataloggers) {
    try {
        let html = `
            <div class="datalogger-container" style="background: var(--bg-card); padding: 0; border-radius: 8px; box-shadow: var(--card-shadow); border: 1px solid var(--border-subtle); overflow: hidden;">
                <h3 style="font-size: 14px; font-weight: 500; color: var(--text-main); margin: 0; padding: 20px 24px; background: var(--bg-panel); border-bottom: 1px solid var(--border-subtle);">
                    Lista de Equipamentos
                </h3>
                <div style="overflow-x: auto;">
                    <table class="datalogger-table">
                        <thead><tr><th>Status</th><th>Nº de Série</th><th>Fabricante</th><th>Modelo</th><th>Última Att.</th></tr></thead>
                        <tbody>
        `;

        dataloggers.forEach(dl => {
            const statusVisual = dl.lost ? 
                '<span class="badge-status status-offline"><span class="status-dot"></span>OFFLINE</span>' : 
                '<span class="badge-status status-online"><span class="status-dot"></span>ONLINE</span>';

            let dataAtualizacao = '<span style="color: var(--text-muted);">Sem dados</span>';
            if(dl.last_update_time) {
                const t = dl.last_update_time;
                const dia = String(t.date).padStart(2, '0');
                const mes = String(t.month).padStart(2, '0');
                const hora = String(t.hours).padStart(2, '0');
                const min = String(t.minutes).padStart(2, '0');
                dataAtualizacao = `${dia}/${mes}/${t.year + 1900} às ${hora}:${min}`;
            }

            html += `<tr><td>${statusVisual}</td><td><span class="sn-highlight">${dl.sn}</span></td><td>${dl.manufacturer}</td><td>${dl.model || 'INVERTER'}</td><td>${dataAtualizacao}</td></tr>`;
        });

        html += `</tbody></table></div></div>`;
        document.getElementById('tabela-inversores-wrapper').innerHTML = html;
    } catch (e) {
        console.error("❌ ERRO AO RENDERIZAR TABELA:", e);
    }
}
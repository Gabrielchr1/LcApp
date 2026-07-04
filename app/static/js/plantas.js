function obterStatusConfig(statusCodigo) {
    // O tipo (online, offline, falha) é usado para somar no contador
    switch (parseInt(statusCodigo)) {
        case 1:
            return { classe: 'status-online', texto: 'ONLINE', tipo: 'online' };
        case 0:
        case -1:
            return { classe: 'status-offline', texto: 'OFFLINE', tipo: 'offline' };
        default:
            return { classe: 'status-falha', texto: 'FALHA', tipo: 'falha' };
    }
}

function renderizarPlantas(plantas) {
    const container = document.getElementById('container-plantas');
    container.innerHTML = ''; 

    let contadores = { online: 0, offline: 0, falha: 0 };

    plantas.forEach(planta => {
        const configStatus = obterStatusConfig(planta.status);
        contadores[configStatus.tipo]++;

        // Formatação com a classe .valor-unidade para diminuir a importância do "kW" e focar no número
        const potAtual = planta.current_power !== undefined 
            ? `${planta.current_power} <span class="valor-unidade">${planta.current_power_unit || 'kW'}</span>` 
            : '-';
            
        const geracaoHoje = planta.daily_energy !== undefined 
            ? `${planta.daily_energy} <span class="valor-unidade">${planta.daily_energy_unit || 'kWh'}</span>` 
            : '-';
            
        const local = planta.address || `${planta.city || ''} ${planta.country || ''}`.trim() || 'Não informado';

        const row = document.createElement('div');
        row.className = 'row-planta';
        
        row.innerHTML = `
            <div class="planta-info">
                <div class="badge-status ${configStatus.classe}">
                    <span class="status-dot"></span>
                    ${configStatus.texto}
                </div>
                <span class="planta-nome" title="${planta.name || 'Usina sem nome'}">
                    ${planta.name || 'Usina sem nome'}
                </span>
            </div>

            <div class="planta-detalhes">
                <span>
                    <span class="detalhe-label">Pot. Atual</span>
                    <span class="detalhe-valor valor-destaque-azul">${potAtual}</span>
                </span>
                
                <span>
                    <span class="detalhe-label">Ger. Hoje</span>
                    <span class="detalhe-valor valor-destaque-verde">${geracaoHoje}</span>
                </span>
                
                <span>
                    <span class="detalhe-label">Ger. Total</span>
                    <span class="detalhe-valor">${planta.total_energy || 0} <span class="valor-unidade">kWh</span></span>
                </span>
                
                <span>
                    <span class="detalhe-label">Capacidade</span>
                    <span class="detalhe-valor">${planta.peak_power || 0} <span class="valor-unidade">kWp</span></span>
                </span>
                
                <span style="overflow: hidden;">
                    <span class="detalhe-label">Local</span>
                    <span class="detalhe-valor" style="font-size: 0.85rem; color: #CBD5E1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${local}">
                        ${local}
                    </span>
                </span>
            </div>

            <div class="planta-acao">
                <!-- Adicionado o parâmetro da marca no clique -->
                <button class="btn-acao" onclick="abrirDetalhesPlanta(${planta.plant_id}, '${planta.marca}')">
                    Equipamentos
                </button>
            </div>
        `;
        
        container.appendChild(row);
    });

    document.getElementById('count-online').textContent = contadores.online;
    document.getElementById('count-offline').textContent = contadores.offline;
    document.getElementById('count-falha').textContent = contadores.falha;
}

// Atualizada para receber e repassar a marca na URL
function abrirDetalhesPlanta(plantId, marca) {
    window.location.href = `/dashboard/plantas/${marca.toLowerCase()}/${plantId}`;
}
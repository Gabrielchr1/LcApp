
function calcularTotalFinanceiro() {
    const valor = parseFloat(document.getElementById('cliValorCobranca').value) || 0;
    const qtd = parseInt(document.getElementById('cliParcelas').value) || 1;
    const total = valor * qtd;
    document.getElementById('cliValorTotal').value = total.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

// ==========================================
// 1. LÓGICA DE INTERFACE E VIA CEP
// ==========================================
function mudarTipoDocumento() {
    const isCnpj = document.getElementById('cliTipoDoc').checked;
    document.getElementById('lblNome').textContent = isCnpj ? 'Razão Social *' : 'Nome Completo *';
    document.getElementById('lblDoc').textContent = isCnpj ? 'CNPJ *' : 'CPF *';
    document.getElementById('cliDocumento').placeholder = isCnpj ? '00.000.000/0000-00' : '000.000.000-00';
}

function toggleFinanceiro() {
    const gerar = document.getElementById('cliGerarCobranca').checked;
    document.getElementById('camposFinanceiro').style.display = gerar ? 'flex' : 'none';
}

async function buscarCep(cep) {
    const cepLimpo = cep.replace(/\D/g, '');
    if (cepLimpo.length !== 8) return;

    document.getElementById('cepLoader').style.display = 'block';
    try {
        const response = await fetch(`https://viacep.com.br/ws/${cepLimpo}/json/`);
        const data = await response.json();
        if (!data.erro) {
            document.getElementById('cliLogradouro').value = data.logradouro;
            document.getElementById('cliBairro').value = data.bairro;
            document.getElementById('cliCidade').value = data.localidade;
            document.getElementById('cliEstado').value = data.uf;
            document.getElementById('cliNumero').focus();
        }
    } catch (e) { console.error("Erro ViaCEP:", e); }
    document.getElementById('cepLoader').style.display = 'none';
}

// ==========================================
// 2. CRUD: ABRIR MODAL, LISTAR, SALVAR
// ==========================================
function abrirModal(isEdit = false) {
    document.getElementById('modalCliente').classList.add('active');
    document.getElementById('formNovoCliente').reset();
    document.getElementById('modalResult').style.display = 'none';
    mudarTipoDocumento();

    if (!isEdit) {
        document.getElementById('modalTitle').textContent = "Cadastrar Novo Cliente";
        document.getElementById('cliId').value = "";
        document.getElementById('sessaoFinanceiro').style.display = 'block'; // Mostra financeiro no cadastro
    }
}

function fecharModal() {
    document.getElementById('modalCliente').classList.remove('active');
}

async function carregarClientes() {
    const tbody = document.getElementById('tabela-clientes-body');
    const kpiContainer = document.getElementById('kpiContainer');
    
    try {
        const response = await fetch('/clientes/api/lista');
        const data = await response.json(); // Agora recebemos { kpis: {...}, clientes: [...] }
        
        // 1. Renderiza os KPIs
        kpiContainer.innerHTML = `
            <div class="kpi-card">
                <span class="kpi-label">Clientes Ativos</span>
                <span class="kpi-value">${data.kpis.ativos}</span>
            </div>
            <div class="kpi-card">
                <span class="kpi-label">A Receber</span>
                <span class="kpi-value success">${data.kpis.valor_receber.toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'})}</span>
            </div>
            <div class="kpi-card" ${data.kpis.atrasados > 0 ? 'style="border-color: #ef4444;"' : ''}>
                <span class="kpi-label">Clientes em Atraso</span>
                <span class="kpi-value ${data.kpis.atrasados > 0 ? 'danger' : ''}">${data.kpis.atrasados} cl.</span>
            </div>
            <div class="kpi-card" ${data.kpis.valor_atrasado > 0 ? 'style="border-color: #ef4444; background: rgba(239, 68, 68, 0.05);"' : ''}>
                <span class="kpi-label">Valores em Atraso</span>
                <span class="kpi-value ${data.kpis.valor_atrasado > 0 ? 'danger' : ''}">${data.kpis.valor_atrasado.toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'})}</span>
            </div>
        `;

        // 2. Renderiza a Tabela
        tbody.innerHTML = '';
        if (data.clientes.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-gray);">Nenhum cliente encontrado.</td></tr>';
            return;
        }

        data.clientes.forEach(cli => {
            const statusBadge = cli.status ? `<span class="badge-ativo">Ativo</span>` : `<span class="badge-inativo">Inativo</span>`;
            const contato = cli.telefone || cli.email || '-';
            const local = cli.cidade ? `${cli.cidade}/${cli.estado}` : '-';
            
            // Renderiza o Valor Monetário e o Alerta de Atraso
            const valorFormatado = cli.valor_total.toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'});
            const alertaAtraso = cli.tem_atraso ? `<div class="text-danger"><i class='bx bx-error-circle'></i> Parcela(s) em atraso</div>` : '';

            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><strong>${cli.nome}</strong></td>
                <td>${contato}</td>
                <td>${local}</td>
                <td>
                    <span style="font-weight: 500;">${valorFormatado}</span>
                    ${alertaAtraso}
                </td>
                <td>${statusBadge}</td>
                <td>
                    <div class="action-group">
                        <button class="btn-icon" onclick="abrirFaturas(${cli.id}, '${cli.nome.replace(/'/g, "\\'")}')" title="Financeiro" style="color: #10b981; border-color: #10b981;"><i class='bx bx-dollar-circle'></i></button>
                        <button class="btn-icon edit" onclick="editarCliente(${cli.id})" title="Editar"><i class='bx bx-edit-alt'></i></button>
                        <button class="btn-icon delete" onclick="excluirCliente(${cli.id})" title="Excluir"><i class='bx bx-trash'></i></button>
                    </div>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: #ef4444;">Erro ao carregar dados.</td></tr>';
    }
}

// SALVAR (CRIAÇÃO OU ATUALIZAÇÃO)
document.getElementById('formNovoCliente').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const id = document.getElementById('cliId').value;
    const isEdit = id !== "";
    const btnSalvar = document.getElementById('btnSalvar');
    const resultBox = document.getElementById('modalResult');
    
    btnSalvar.disabled = true;
    btnSalvar.textContent = "Salvando...";
    
    // Monta o payload base
    const isCnpj = document.getElementById('cliTipoDoc').checked;
    let payload = {
        nome: document.getElementById('cliNome').value.trim(),
        tipo_documento: isCnpj ? 'CNPJ' : 'CPF',
        documento: document.getElementById('cliDocumento').value.trim() || null,
        email: document.getElementById('cliEmail').value.trim() || null,
        telefone: document.getElementById('cliTelefone').value.trim() || null,
        cep: document.getElementById('cliCep').value.trim() || null,
        logradouro: document.getElementById('cliLogradouro').value.trim() || null,
        numero: document.getElementById('cliNumero').value.trim() || null,
        bairro: document.getElementById('cliBairro').value.trim() || null,
        cidade: document.getElementById('cliCidade').value.trim() || null,
        estado: document.getElementById('cliEstado').value.trim() || null
    };

    // Adiciona regras financeiras apenas na Criação
    if (!isEdit && document.getElementById('cliGerarCobranca').checked) {
        payload.gerar_cobranca = true;
        payload.valor_cobranca = parseFloat(document.getElementById('cliValorCobranca').value) || 0;
        payload.qtd_parcelas = parseInt(document.getElementById('cliParcelas').value) || 1;
        payload.data_primeiro_vencimento = document.getElementById('cliVencimento').value || null;
    }

    const url = isEdit ? `/clientes/api/atualizar/${id}` : `/clientes/api/criar`;
    const method = isEdit ? 'PUT' : 'POST';

    try {
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await response.json();
        resultBox.style.display = "block";
        
        if (response.ok) {
            resultBox.className = 'result-box success';
            resultBox.innerHTML = `<strong>✅ ${data.message}</strong>`;
            carregarClientes();
            setTimeout(() => { fecharModal(); }, 1500);
        } else {
            resultBox.className = 'result-box error';
            resultBox.innerHTML = `<strong>❌ Erro:</strong> ${data.detail || 'Falha ao salvar.'}`;
        }
    } catch (error) {
        resultBox.style.display = "block";
        resultBox.className = 'result-box error';
        resultBox.innerHTML = `<strong>❌ Falha na comunicação com o servidor.</strong>`;
    } finally {
        btnSalvar.disabled = false;
        btnSalvar.textContent = "Salvar Cliente";
    }
});

// ==========================================
// 3. CRUD: EDITAR E EXCLUIR
// ==========================================
async function editarCliente(id) {
    abrirModal(true); // Abre em modo edição
    document.getElementById('modalTitle').textContent = "Editar Cliente";
    document.getElementById('sessaoFinanceiro').style.display = 'none'; // Esconde finanças na edição
    document.getElementById('cliId').value = id;

    try {
        const response = await fetch(`/clientes/api/${id}`);
        if (response.ok) {
            const cli = await response.json();
            
            // Preenche os dados
            document.getElementById('cliTipoDoc').checked = (cli.tipo_documento === 'CNPJ');
            mudarTipoDocumento(); // Atualiza labels

            document.getElementById('cliNome').value = cli.nome || '';
            document.getElementById('cliDocumento').value = cli.documento || '';
            document.getElementById('cliTelefone').value = cli.telefone || '';
            document.getElementById('cliEmail').value = cli.email || '';
            document.getElementById('cliCep').value = cli.cep || '';
            document.getElementById('cliLogradouro').value = cli.logradouro || '';
            document.getElementById('cliNumero').value = cli.numero || '';
            document.getElementById('cliBairro').value = cli.bairro || '';
            document.getElementById('cliCidade').value = cli.cidade || '';
            document.getElementById('cliEstado').value = cli.estado || '';
        }
    } catch (e) { alert("Erro ao carregar dados do cliente."); fecharModal(); }
}

async function excluirCliente(id) {
    if(confirm("ATENÇÃO: Tem certeza que deseja excluir este cliente? Todas as contas a receber vinculadas a ele também serão excluídas!")) {
        try {
            const response = await fetch(`/clientes/api/excluir/${id}`, { method: 'DELETE' });
            if (response.ok) {
                carregarClientes(); // Atualiza a tabela
            } else {
                const data = await response.json();
                alert(data.detail || "Erro ao excluir.");
            }
        } catch (e) { alert("Erro de comunicação."); }
    }
}

// Inicializa
document.addEventListener('DOMContentLoaded', carregarClientes);

// ==========================================
// 4. GESTÃO DE FATURAS (NOVO)
// ==========================================
function fecharModalFaturas() {
    document.getElementById('modalFaturas').classList.remove('active');
}

async function abrirFaturas(clienteId, nomeCliente) {
    document.getElementById('modalFaturas').classList.add('active');
    document.getElementById('nomeClienteFatura').textContent = nomeCliente;
    const tbody = document.getElementById('tabela-faturas-body');
    const resultBox = document.getElementById('faturaResult');
    resultBox.style.display = 'none';
    
    tbody.innerHTML = '<tr><td colspan="6" style="text-align: center;">Carregando...</td></tr>';

    try {
        const response = await fetch(`/clientes/api/${clienteId}/faturas`);
        const faturas = await response.json();
        
        tbody.innerHTML = '';
        if (faturas.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-gray);">Nenhuma fatura encontrada.</td></tr>';
            return;
        }

        const hoje = new Date();
        hoje.setHours(0,0,0,0);

        faturas.forEach(fat => {
            // Formata data e valor
            const dataVenc = new Date(fat.data_vencimento);
            const dataFormatada = dataVenc.toLocaleDateString('pt-BR', { timeZone: 'UTC' });
            const valorFormatado = fat.valor.toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'});
            
            // Verifica status dinamicamente
            let statusBadge = '';
            let btnAcao = '';

            if (fat.status === 'pago') {
                statusBadge = `<span class="badge-pago"><i class='bx bx-check'></i> Pago</span>`;
                btnAcao = `<span style="font-size: 11px; color: var(--text-gray);">Baixado</span>`;
            } else {
                // Se não está pago, verifica se está atrasado
                if (dataVenc < hoje) {
                    statusBadge = `<span class="badge-atrasado"><i class='bx bx-error'></i> Atrasado</span>`;
                } else {
                    statusBadge = `<span class="badge-pendente"><i class='bx bx-time'></i> Pendente</span>`;
                }
                
                btnAcao = `<button class="btn-pay" onclick="confirmarPagamento(${fat.id}, ${clienteId}, '${nomeCliente}')"><i class='bx bx-check-circle'></i> Dar Baixa</button>`;
            }

            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><strong>${fat.descricao}</strong></td>
                <td>${fat.parcela || '-'}</td>
                <td>${dataFormatada}</td>
                <td style="font-weight: 500;">${valorFormatado}</td>
                <td>${statusBadge}</td>
                <td style="text-align: right;">${btnAcao}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: #ef4444;">Erro ao carregar faturas.</td></tr>';
    }
}

async function confirmarPagamento(faturaId, clienteId, nomeCliente) {
    if(confirm("Confirma o recebimento desta parcela?")) {
        const resultBox = document.getElementById('faturaResult');
        try {
            const response = await fetch(`/clientes/api/faturas/${faturaId}/pagar`, { method: 'PUT' });
            const data = await response.json();
            
            if (response.ok) {
                // Atualiza a lista de faturas do modal
                abrirFaturas(clienteId, nomeCliente);
                // Atualiza o dashboard global no fundo
                carregarClientes();
                
                resultBox.className = 'result-box success';
                resultBox.innerHTML = `<strong>✅ ${data.message}</strong>`;
                resultBox.style.display = 'block';
                setTimeout(() => { resultBox.style.display = 'none'; }, 3000);
            } else {
                alert(data.detail || "Erro ao processar pagamento.");
            }
        } catch (e) {
            alert("Erro de comunicação com o servidor.");
        }
    }
}
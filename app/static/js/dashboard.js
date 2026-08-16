let todasAsUsinasGlobal = [];
let autoScrollInterval;
let isAutoScrolling = false;

document.addEventListener("DOMContentLoaded", () => {
    carregarUsinas();

    document.getElementById('btnAtualizar').addEventListener('click', carregarUsinas);
    document.getElementById('btnAutoScroll').addEventListener('click', toggleAutoScroll);
    document.getElementById('btnFullScreen').addEventListener('click', toggleFullScreen);
    document.getElementById('btnConfig').addEventListener('click', () => { window.location.href='/dashboard/configuracoes'; });

    document.querySelectorAll('.btn-filtro').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const marca = e.target.getAttribute('data-marca');
            aplicarFiltro(marca, e.target);
        });
    });
});

async function carregarUsinas() {
    const container = document.getElementById('container-plantas');
    container.innerHTML = '<div class="loading-state"><p>Buscando dados nas APIs...</p></div>';
    
    todasAsUsinasGlobal = [];
    let erros = [];

    const fetchApi = async (url, marca) => {
        try {
            const res = await fetch(url);
            if (!res.ok) throw new Error((await res.json()).detail || `Erro HTTP ${res.status}`);
            const data = await res.json();
            if (data.plants) {
                const plantsWithMarca = data.plants.map(p => marca === 'Growatt' ? {...p, marca: 'Growatt'} : p);
                todasAsUsinasGlobal.push(...plantsWithMarca);
            }
        } catch (e) {
            erros.push(`${marca}: ${e.message}`);
            console.error(e);
        }
    };

    // Consultando todas as APIs em paralelo
    await Promise.all([
        fetchApi('/api/growatt/plants', 'Growatt'),
        fetchApi('/api/sungrow/plants', 'Sungrow'),
        fetchApi('/api/solis/plants', 'Solis'),
        fetchApi('/api/saj/plants', 'SAJ'),
        fetchApi('/api/deye/plants', 'Deye')
    ]);

    if (todasAsUsinasGlobal.length > 0) {
        const botaoAtivo = document.querySelector('.btn-filtro.active') || document.querySelector('.btn-filtro');
        aplicarFiltro(botaoAtivo.getAttribute('data-marca'), botaoAtivo);
    } else {
        container.innerHTML = `
            <div class="error-state">
                <h3 style="color: var(--text-main); font-weight: 400; margin-bottom: 12px; font-size: 1.1rem;">Falha de Comunicação</h3>
                <p>Não foi possível estabelecer conexão com as usinas.</p>
                <p style="font-size: 0.8rem; margin-top: 16px; color: var(--status-offline); opacity: 0.8;">Detalhes técnicos:<br>${erros.join('<br>') || 'Timeout nos servidores'}</p>
            </div>
        `;
        ['count-online', 'count-offline', 'count-falha'].forEach(id => document.getElementById(id).textContent = '0');
    }
}

function aplicarFiltro(marca, botaoClicado) {
    if (botaoClicado) {
        document.querySelectorAll('.btn-filtro').forEach(btn => btn.classList.remove('active'));
        botaoClicado.classList.add('active');
    }

    let usinasFiltradas = marca !== 'Todas' 
        ? todasAsUsinasGlobal.filter(p => p.marca.toUpperCase() === marca.toUpperCase()) 
        : todasAsUsinasGlobal;

    if (usinasFiltradas.length > 0) {
        if (typeof renderizarPlantas === "function") {
            renderizarPlantas(usinasFiltradas);
        } else {
            console.error("Função renderizarPlantas não encontrada no contexto global.");
        }
    } else {
        document.getElementById('container-plantas').innerHTML = `<div class="loading-state"><p>Nenhuma usina encontrada para o filtro selecionado.</p></div>`;
        ['count-online', 'count-offline', 'count-falha'].forEach(id => document.getElementById(id).textContent = '0');
    }
}

function toggleFullScreen() {
    if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen().catch(e => console.error(e));
    } else if (document.exitFullscreen) {
        document.exitFullscreen();
    }
}

function toggleAutoScroll() {
    const list = document.getElementById('container-plantas');
    const btn = document.getElementById('btnAutoScroll');
    const icon = btn.querySelector('i');
    
    if (isAutoScrolling) {
        clearInterval(autoScrollInterval);
        isAutoScrolling = false;
        icon.className = 'bx bx-play';
        btn.style.color = 'var(--text-muted)';
    } else {
        isAutoScrolling = true;
        icon.className = 'bx bx-pause';
        btn.style.color = 'var(--status-online)';
        
        autoScrollInterval = setInterval(() => {
            if (list.scrollTop + list.clientHeight >= list.scrollHeight - 2) {
                list.scrollTo({ top: 0, behavior: 'smooth' });
                clearInterval(autoScrollInterval);
                setTimeout(() => { if (isAutoScrolling) toggleAutoScroll(); toggleAutoScroll(); }, 2000);
            } else {
                list.scrollBy({ top: 1, behavior: 'auto' });
            }
        }, 45);
    }
}
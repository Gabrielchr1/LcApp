document.addEventListener("DOMContentLoaded", () => {

    // ==========================================
    // LÓGICA DO FORMULÁRIO DA DEYE
    // ==========================================
    const deyeConfigForm = document.getElementById('deyeConfigForm');
    if (deyeConfigForm) {
        deyeConfigForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const btn = document.getElementById('btnTestarDeye');
            const resultBox = document.getElementById('resultMessageDeye');
            
            btn.textContent = "Salvando credenciais...";
            btn.disabled = true;
            resultBox.style.display = "none";
            resultBox.className = "result-box"; 

            const payload = {
                api_url: "https://us1-developer.deyecloud.com",
                app_id: document.getElementById('deyeAppId').value.trim(),
                app_secret: document.getElementById('deyeAppSecret').value.trim(),
                email: document.getElementById('deyeEmail').value.trim(),
                password: document.getElementById('deyePassword').value.trim(),
                company_id: null 
            };

            try {
                const response = await fetch('/api/deye/configurar', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                const data = await response.json();

                if (response.ok && data.success) {
                    resultBox.classList.add('success');
                    resultBox.innerHTML = `<strong>✅ ${data.message}</strong>`;
                } else {
                    resultBox.classList.add('error');
                    resultBox.innerHTML = `<strong>❌ Erro:</strong> ${data.detail || data.message || 'Falha ao salvar.'}`;
                }
            } catch (error) {
                console.error("Erro na requisição Deye:", error);
                resultBox.classList.add('error');
                resultBox.innerHTML = `<strong>❌ Falha na comunicação com o servidor.</strong>`;
            } finally {
                resultBox.style.display = "block";
                btn.textContent = "Salvar";
                btn.disabled = false;
            }
        });
    }

    // ==========================================
    // LÓGICA DO FORMULÁRIO DA GROWATT
    // ==========================================
    const growattConfigForm = document.getElementById('growattConfigForm');
    if (growattConfigForm) {
        growattConfigForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const btn = document.getElementById('btnTestarGrowatt');
            const resultBox = document.getElementById('resultMessageGrowatt');
            
            btn.textContent = "Salvando credenciais...";
            btn.disabled = true;
            resultBox.style.display = "none";
            resultBox.className = "result-box"; 

            const payload = {
                api_url: document.getElementById('growattApiUrl').value.trim(),
                api_token: document.getElementById('growattApiToken').value.trim()
            };

            try {
                const response = await fetch('/api/growatt/configurar', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                const data = await response.json();

                if (response.ok && data.success) {
                    resultBox.classList.add('success');
                    resultBox.innerHTML = `<strong>✅ ${data.message}</strong>`;
                } else {
                    resultBox.classList.add('error');
                    resultBox.innerHTML = `<strong>❌ Erro:</strong> ${data.detail || data.message || 'Falha ao salvar.'}`;
                }
            } catch (error) {
                console.error("Erro na requisição Growatt:", error);
                resultBox.classList.add('error');
                resultBox.innerHTML = `<strong>❌ Falha na comunicação com o servidor.</strong>`;
            } finally {
                resultBox.style.display = "block";
                btn.textContent = "Salvar Credenciais Growatt";
                btn.disabled = false;
            }
        });
    }

    // ==========================================
    // LÓGICA DO FORMULÁRIO DA SUNGROW
    // ==========================================
    const sungrowConfigForm = document.getElementById('sungrowConfigForm');
    if (sungrowConfigForm) {
        sungrowConfigForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const btn = document.getElementById('btnTestar');
            const resultBox = document.getElementById('resultMessage');
            
            btn.textContent = "Autenticando aguarde...";
            btn.disabled = true;
            resultBox.style.display = "none";
            resultBox.className = "result-box";

            const payload = {
                app_key: document.getElementById('appKey').value.trim(),
                secret_key: document.getElementById('secretKey').value.trim(),
                user_account: document.getElementById('userAccount').value.trim(),
                user_password: document.getElementById('userPassword').value.trim()
            };

            try {
                const response = await fetch('/api/sungrow/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                const data = await response.json();

                if (response.ok && data.success) {
                    resultBox.classList.add('success');
                    resultBox.innerHTML = `
                        <strong>✅ ${data.message}</strong><br>
                        Seu Token de acesso é:
                        <div class="token-display">${data.token}</div>
                    `;
                } else {
                    resultBox.classList.add('error');
                    resultBox.innerHTML = `<strong>❌ Erro:</strong> ${data.message || 'Falha na autenticação.'}`;
                }
            } catch (error) {
                console.error("Erro na requisição:", error);
                resultBox.classList.add('error');
                resultBox.innerHTML = `<strong>❌ Falha na comunicação com o servidor.</strong> Verifique o console.`;
            } finally {
                resultBox.style.display = "block";
                btn.textContent = "Autenticar e Salvar";
                btn.disabled = false;
            }
        });
    }

    // ==========================================
    // LÓGICA DO FORMULÁRIO DA SOLIS
    // ==========================================
    const solisConfigForm = document.getElementById('solisConfigForm');
    if (solisConfigForm) {
        solisConfigForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const btn = document.getElementById('btnTestarSolis');
            const resultBox = document.getElementById('resultMessageSolis');
            
            btn.textContent = "Salvando credenciais...";
            btn.disabled = true;
            resultBox.style.display = "none";
            resultBox.className = "result-box"; 

            const payload = {
                api_url: "https://www.soliscloud.com:13333",
                key_id: document.getElementById('solisKeyId').value.trim(),
                key_secret: document.getElementById('solisKeySecret').value.trim()
            };

            try {
                const response = await fetch('/api/solis/configurar', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                const data = await response.json();

                if (response.ok && data.success) {
                    resultBox.classList.add('success');
                    resultBox.innerHTML = `<strong>✅ ${data.message}</strong>`;
                } else {
                    resultBox.classList.add('error');
                    resultBox.innerHTML = `<strong>❌ Erro:</strong> ${data.detail || data.message || 'Falha ao salvar.'}`;
                }
            } catch (error) {
                console.error("Erro na requisição Solis:", error);
                resultBox.classList.add('error');
                resultBox.innerHTML = `<strong>❌ Falha na comunicação com o servidor.</strong>`;
            } finally {
                resultBox.style.display = "block";
                btn.textContent = "Salvar Credenciais Solis";
                btn.disabled = false;
            }
        });
    }

    // ==========================================
    // LÓGICA DO FORMULÁRIO DA SAJ
    // ==========================================
    const sajConfigForm = document.getElementById('sajConfigForm');
    if (sajConfigForm) {
        sajConfigForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const btn = document.getElementById('btnTestarSaj');
            const resultBox = document.getElementById('resultMessageSaj');
            
            btn.textContent = "Salvando credenciais...";
            btn.disabled = true;
            resultBox.style.display = "none";
            resultBox.className = "result-box"; 

            const payload = {
                api_url: "https://intl-developer.saj-electric.com/prod-api",
                app_id: document.getElementById('sajAppId').value.trim(),
                app_secret: document.getElementById('sajAppSecret').value.trim()
            };

            try {
                const response = await fetch('/api/saj/configurar', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                const data = await response.json();

                if (response.ok && data.success) {
                    resultBox.classList.add('success');
                    resultBox.innerHTML = `<strong>✅ ${data.message}</strong>`;
                } else {
                    resultBox.classList.add('error');
                    resultBox.innerHTML = `<strong>❌ Erro:</strong> ${data.detail || data.message || 'Falha ao salvar.'}`;
                }
            } catch (error) {
                console.error("Erro na requisição SAJ:", error);
                resultBox.classList.add('error');
                resultBox.innerHTML = `<strong>❌ Falha na comunicação com o servidor.</strong>`;
            } finally {
                resultBox.style.display = "block";
                btn.textContent = "Salvar Credenciais SAJ";
                btn.disabled = false;
            }
        });
    }

});
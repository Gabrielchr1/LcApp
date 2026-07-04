// Exemplo de como o frontend buscará os dados das plantas sem saber da API Key da Growatt
async function fetchPlants(userName) {
    try {
        const response = await fetch(`/api/growatt/plants/${userName}`);
        if (!response.ok) throw new Error("Erro ao buscar plantas");
        
        const data = await response.json();
        console.log("Plantas encontradas:", data.plants);
        
        // Aqui você adicionará a lógica para renderizar no DOM (ex: criar cards para cada planta)
        
    } catch (error) {
        console.error("Falha na comunicação:", error);
    }
}
document.addEventListener('DOMContentLoaded', () => {
    const sidebar = document.getElementById('sidebar');
    const toggleBtn = document.getElementById('toggle-btn');
    const submenuLinks = document.querySelectorAll('.has-submenu');

    // Função de encolher/expandir o Sidebar
    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', () => {
            sidebar.classList.toggle('collapsed');
            
            // Se fechou o sidebar, fechamos todos os submenus para não ficar feio visualmente
            if (sidebar.classList.contains('collapsed')) {
                submenuLinks.forEach(link => {
                    link.classList.remove('open');
                    const submenu = link.nextElementSibling;
                    if (submenu) {
                        submenu.classList.remove('open');
                    }
                });
            }
        });
    }

    // Função de abrir/fechar Submenus (Accordion)
    submenuLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Se o sidebar estiver recolhido, expandimos ele antes de abrir o submenu
            if (sidebar.classList.contains('collapsed')) {
                sidebar.classList.remove('collapsed');
            }

            // Alternar o próprio submenu clicado
            this.classList.toggle('open');
            const submenu = this.nextElementSibling;
            
            if (submenu) {
                submenu.classList.toggle('open');
            }
        });
    });
});
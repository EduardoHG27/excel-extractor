    function copiarTicketCode() {
        const ticketCode = document.querySelector('[style*="font-family: \'Fira Code\'"]').textContent.trim();
        
        navigator.clipboard.writeText(ticketCode)
            .then(() => {
                const btn = event.currentTarget;
                const originalHtml = btn.innerHTML;
                btn.innerHTML = '<i class="bi bi-check-circle me-2"></i>Copiado!';
                setTimeout(() => {
                    btn.innerHTML = originalHtml;
                }, 2000);
            })
            .catch(err => {
                console.error('Error al copiar: ', err);
                alert('Error al copiar el código del ticket');
            });
    }
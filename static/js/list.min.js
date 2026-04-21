    let openDetail = null;
    
    function showDetails(index) {
        const detailRow = document.getElementById(`details-${index}`);
        
        // Cerrar el detalle abierto previamente si existe
        if (openDetail !== null && openDetail !== index) {
            const previousDetail = document.getElementById(`details-${openDetail}`);
            previousDetail.style.display = 'none';
        }
        
        // Alternar visibilidad del detalle actual
        if (detailRow.style.display === 'none' || detailRow.style.display === '') {
            detailRow.style.display = 'table-row';
            openDetail = index;
        } else {
            detailRow.style.display = 'none';
            openDetail = null;
        }
    }
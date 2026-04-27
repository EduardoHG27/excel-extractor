document.addEventListener('DOMContentLoaded', function() {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('excel_file');
    const browseButton = document.getElementById('browseButton');
    const dropZoneContent = document.getElementById('dropZoneContent');
    const fileInfo = document.getElementById('fileInfo');
    const fileName = document.getElementById('fileName');
    const fileSize = document.getElementById('fileSize');
    const changeFileButton = document.getElementById('changeFileButton');
    const uploadForm = document.getElementById('uploadForm');
    const loadingOverlay = document.getElementById('loadingOverlay');

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    function highlight() {
        if (dropZone) {
            dropZone.style.backgroundColor = '#e8f4fd';
            dropZone.style.borderColor = '#2980b9';
        }
    }

    function unhighlight() {
        if (dropZone) {
            dropZone.style.backgroundColor = '#f8f9fa';
            dropZone.style.borderColor = '#3498db';
        }
    }

    function handleDrop(e) {
        preventDefaults(e);
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    }

    function handleFile(file) {
        if (!file) {
            alert('No se pudo leer el archivo');
            return;
        }
        
        const fileName_full = file.name;
        const fileExt = '.' + fileName_full.split('.').pop().toLowerCase();
        
        if (fileExt === '.xlsx' || fileExt === '.xls') {
            if (file.size <= 10 * 1024 * 1024) {
                const dataTransfer = new DataTransfer();
                dataTransfer.items.add(file);
                if (fileInput) {
                    fileInput.files = dataTransfer.files;
                }
                displayFileInfo(file);
            } else {
                alert('El archivo no debe superar los 10MB');
            }
        } else {
            alert('Por favor, selecciona un archivo Excel válido (.xlsx o .xls)');
        }
    }

    function displayFileInfo(file) {
        let fileSizeText = file.size;
        let unit = 'bytes';
        
        if (fileSizeText > 1024) {
            fileSizeText /= 1024;
            unit = 'KB';
        }
        if (fileSizeText > 1024) {
            fileSizeText /= 1024;
            unit = 'MB';
        }
        
        fileSizeText = fileSizeText.toFixed(2);
        
        if (fileName) fileName.textContent = file.name;
        if (fileSize) fileSize.textContent = 'Tamaño: ' + fileSizeText + ' ' + unit;
        
        if (dropZoneContent) dropZoneContent.style.display = 'none';
        if (fileInfo) fileInfo.style.display = 'block';
    }

    function resetFileInput() {
        if (fileInput) {
            fileInput.value = '';
        }
        if (dropZoneContent) dropZoneContent.style.display = 'block';
        if (fileInfo) fileInfo.style.display = 'none';
    }

    if (dropZone) {
        dropZone.addEventListener('dragenter', preventDefaults, false);
        dropZone.addEventListener('dragover', preventDefaults, false);
        dropZone.addEventListener('dragleave', preventDefaults, false);
        dropZone.addEventListener('drop', preventDefaults, false);
        
        dropZone.addEventListener('dragenter', highlight, false);
        dropZone.addEventListener('dragover', highlight, false);
        dropZone.addEventListener('dragleave', unhighlight, false);
        dropZone.addEventListener('drop', unhighlight, false);
        
        dropZone.addEventListener('drop', handleDrop, false);
        
        dropZone.style.cursor = 'pointer';
        dropZone.addEventListener('click', function(e) {
            if (e.target.id !== 'browseButton' && e.target.id !== 'changeFileButton') {
                if (fileInput) fileInput.click();
            }
        });
    }

    if (browseButton) {
        browseButton.addEventListener('click', function(e) {
            e.stopPropagation();
            if (fileInput) fileInput.click();
        });
    }

    if (fileInput) {
        fileInput.addEventListener('change', function() {
            if (this.files.length > 0) {
                handleFile(this.files[0]);
            }
        });
    }

    if (changeFileButton) {
        changeFileButton.addEventListener('click', function(e) {
            e.stopPropagation();
            resetFileInput();
            if (fileInput) fileInput.click();
        });
    }

    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            if (!fileInput || !fileInput.files.length) {
                e.preventDefault();
                alert('Por favor, selecciona un archivo para subir.');
            } else {
                if (loadingOverlay) {
                    loadingOverlay.style.display = 'flex';
                }
                var submitBtn = this.querySelector('button[type="submit"]');
                if (submitBtn) {
                    submitBtn.disabled = true;
                }
            }
        });
    }
});
document.addEventListener('DOMContentLoaded', () => {
    // Core elements
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const fileList = document.getElementById('file-list');
    const formatOptions = document.querySelectorAll('.format-option');
    const convertBtn = document.getElementById('convert-btn');
    const statusCard = document.getElementById('status-card');
    const resultCard = document.getElementById('result-card');
    const batchResults = document.getElementById('batch-results');
    const previewContainer = document.getElementById('preview-container');
    const markdownPreview = document.getElementById('markdown-preview');
    const saveBtn = document.getElementById('save-btn');
    const savePath = document.getElementById('save-path');
    const saveStatus = document.getElementById('save-status');
    const newConvBtn = document.getElementById('new-conv-btn');
    
    // History elements
    const historySection = document.getElementById('history-section');
    const historyList = document.getElementById('history-list');
    const clearHistoryBtn = document.getElementById('clear-history-btn');

    let selectedFiles = [];
    let selectedFormat = null;
    let currentResults = [];
    let isCloud = false;

    // Initialization
    async function init() {
        try {
            const response = await fetch('/config');
            const config = await response.json();
            isCloud = config.is_cloud;
            
            if (isCloud) {
                document.querySelector('.save-locally-section')?.classList.add('hidden');
                document.querySelector('.subtitle').textContent += ' (Cloud Edition)';
            }
        } catch (err) {
            console.error('Failed to load config', err);
        }
        loadHistory();
    }
    
    init();

    // File Selection Logic
    const handleFiles = (files) => {
        if (files.length > 0) {
            const newFiles = Array.from(files);
            // Append unique files
            newFiles.forEach(nf => {
                if (!selectedFiles.find(sf => sf.name === nf.name && sf.size === nf.size)) {
                    selectedFiles.push(nf);
                }
            });
            renderFileList();
            if (selectedFiles.length > 0) {
                suggestFormat(selectedFiles[0].name);
            }
            checkReady();
        }
    };

    const renderFileList = () => {
        if (selectedFiles.length === 0) {
            fileList.classList.add('hidden');
            return;
        }

        fileList.classList.remove('hidden');
        fileList.innerHTML = '';

        selectedFiles.forEach((file, index) => {
            const div = document.createElement('div');
            div.className = 'file-item';
            div.innerHTML = `
                <span class="file-item-name">${file.name}</span>
                <button class="file-item-remove" title="Remove">&times;</button>
            `;
            div.querySelector('.file-item-remove').onclick = (e) => {
                e.stopPropagation();
                selectedFiles.splice(index, 1);
                renderFileList();
                checkReady();
            };
            fileList.appendChild(div);
        });
    };

    const suggestFormat = (filename) => {
        const ext = filename.split('.').pop().toLowerCase();
        formatOptions.forEach(opt => {
            opt.classList.remove('suggested');
            const format = opt.dataset.format;
            const matches = (
                (ext === 'pptx' && (format === 'pptx-to-md' || format === 'pptx-to-pdf')) ||
                (ext === 'pdf' && (format === 'pdf-to-md' || format === 'pdf-to-pptx')) ||
                (ext === 'docx' && format === 'docx-to-md') ||
                (ext === 'md' && format === 'md-to-docx')
            );
            if (matches) {
                opt.classList.add('suggested');
            }
        });
    };

    fileInput.addEventListener('change', (e) => handleFiles(e.target.files));

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    ['dragleave', 'dragend'].forEach(type => {
        dropZone.addEventListener(type, () => dropZone.classList.remove('dragover'));
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        handleFiles(e.dataTransfer.files);
    });

    // Format Selection
    formatOptions.forEach(opt => {
        opt.addEventListener('click', () => {
            formatOptions.forEach(o => o.classList.remove('active'));
            opt.classList.add('active');
            selectedFormat = opt.dataset.format;
            checkReady();
        });
    });

    const checkReady = () => {
        convertBtn.disabled = !(selectedFiles.length > 0 && selectedFormat);
    };

    // Conversion Process
    convertBtn.addEventListener('click', async () => {
        if (selectedFiles.length === 0 || !selectedFormat) return;

        // UI Feedback
        statusCard.classList.remove('hidden');
        resultCard.classList.add('hidden');
        convertBtn.disabled = true;

        const formData = new FormData();
        selectedFiles.forEach(file => {
            formData.append('files', file);
        });
        formData.append('format', selectedFormat);

        try {
            const response = await fetch('/convert', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.results) {
                currentResults = data.results;
                renderBatchResults(data.results);
                
                // Show results
                resultCard.classList.remove('hidden');
                resultCard.scrollIntoView({ behavior: 'smooth' });

                // Add to history
                data.results.forEach(res => {
                    if (res.success) {
                        addToHistory({
                            id: res.file_id,
                            name: res.filename,
                            format: selectedFormat,
                            date: new Date().toLocaleString(),
                            savePath: null // Not saved yet
                        });
                    }
                });
            } else {
                alert(`Error: ${data.detail || 'Unknown error'}`);
            }
        } catch (err) {
            alert(`An error occurred: ${err.message}`);
        } finally {
            statusCard.classList.add('hidden');
            convertBtn.disabled = false;
        }
    });

    const renderBatchResults = (results) => {
        batchResults.innerHTML = '';
        previewContainer.classList.add('hidden');

        results.forEach(res => {
            const div = document.createElement('div');
            div.className = 'batch-item';
            
            if (res.success) {
                div.innerHTML = `
                    <div class="batch-item-info">
                        <span class="batch-item-name">${res.filename}</span>
                        <span class="batch-item-meta" style="color: var(--accent); font-size: 0.8rem;">Ready</span>
                    </div>
                    <div class="batch-item-actions">
                        ${res.preview ? `<button class="btn btn-secondary btn-small view-btn" data-id="${res.file_id}">Preview</button>` : ''}
                        <a href="/download/${res.file_id}/${res.filename}" class="btn btn-primary btn-small" download>Download</a>
                    </div>
                `;

                if (res.preview) {
                    div.querySelector('.view-btn').onclick = () => showPreview(res.preview);
                }
            } else {
                div.innerHTML = `
                    <div class="batch-item-info">
                        <span class="batch-item-name">${res.filename}</span>
                        <span class="batch-item-meta" style="color: var(--error); font-size: 0.8rem;">Failed: ${res.detail}</span>
                    </div>
                `;
            }
            batchResults.appendChild(div);
        });
    };

    const showPreview = (text) => {
        if (typeof marked !== 'undefined' && typeof DOMPurify !== 'undefined') {
            const html = marked.parse(text);
            markdownPreview.innerHTML = DOMPurify.sanitize(html);
            markdownPreview.className = "markdown-body";
        } else {
            markdownPreview.textContent = text;
        }
        previewContainer.classList.remove('hidden');
        previewContainer.scrollIntoView({ behavior: 'smooth' });
    };

    // UI Actions
    newConvBtn.addEventListener('click', () => resetApp());

    const resetApp = () => {
        selectedFiles = [];
        selectedFormat = null;
        fileInput.value = '';
        renderFileList();
        resultCard.classList.add('hidden');
        previewContainer.classList.add('hidden');
        formatOptions.forEach(opt => opt.classList.remove('active'));
        checkReady();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    // Local Storage History
    function loadHistory() {
        const history = JSON.parse(localStorage.getItem('conv_history') || '[]');
        renderHistoryList(history);
    }

    function addToHistory(item) {
        let history = JSON.parse(localStorage.getItem('conv_history') || '[]');
        // Avoid duplicates by ID
        if (!history.find(h => h.id === item.id)) {
            history.unshift(item);
            history = history.slice(0, 20); // Keep last 20
            localStorage.setItem('conv_history', JSON.stringify(history));
            renderHistoryList(history);
        }
    }

    function updateHistoryItem(id, savePath) {
        let history = JSON.parse(localStorage.getItem('conv_history') || '[]');
        const item = history.find(h => h.id === id);
        if (item) {
            item.savePath = savePath;
            localStorage.setItem('conv_history', JSON.stringify(history));
            renderHistoryList(history);
        }
    }

    function renderHistoryList(history) {
        if (history.length === 0) {
            historySection.classList.add('hidden');
            return;
        }

        historySection.classList.remove('hidden');
        historyList.innerHTML = '';

        history.forEach(item => {
            const div = document.createElement('div');
            div.className = 'history-item';
            div.innerHTML = `
                <div class="history-item-info">
                    <span class="history-item-name">${item.name}</span>
                    <span class="history-item-meta">${item.format} • ${item.date}</span>
                </div>
                <div class="history-item-actions">
                    ${(item.savePath && !isCloud) ? `<button class="btn btn-secondary btn-small btn-open" data-path="${item.savePath}">Open Folder</button>` : ''}
                    <a href="/download/${item.id}/${item.name}" class="btn btn-secondary btn-small" download>Download</a>
                </div>
            `;

            if (item.savePath) {
                div.querySelector('.btn-open').onclick = () => openFolder(item.savePath);
            }

            historyList.appendChild(div);
        });
    }

    async function openFolder(path) {
        try {
            const response = await fetch('/open-folder', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ path })
            });
            const data = await response.json();
            if (!data.success) alert(`Error opening folder: ${data.detail}`);
        } catch (err) {
            alert(`Error: ${err.message}`);
        }
    }

    clearHistoryBtn.addEventListener('click', () => {
        localStorage.removeItem('conv_history');
        renderHistoryList([]);
    });

    // Save Locally logic
    saveBtn.addEventListener('click', async () => {
        const path = savePath.value.trim();
        if (!path) {
            saveStatus.textContent = 'Please enter a path.';
            saveStatus.style.color = 'var(--error)';
            return;
        }

        saveBtn.disabled = true;
        saveStatus.textContent = 'Saving batch...';
        
        let successCount = 0;
        let lastError = null;

        // Save each successful conversion in the current batch
        for (const res of currentResults) {
            if (!res.success) continue;

            try {
                const response = await fetch('/save-local', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        file_id: res.file_id,
                        target_path: path,
                        original_name: res.filename
                    })
                });

                const data = await response.json();
                if (data.success) {
                    successCount++;
                    updateHistoryItem(res.file_id, path);
                } else {
                    lastError = data.detail;
                }
            } catch (err) {
                lastError = err.message;
            }
        }

        if (successCount > 0) {
            saveStatus.textContent = `Successfully saved ${successCount} files!`;
            saveStatus.style.color = 'var(--accent)';
        } else if (lastError) {
            saveStatus.textContent = `Error: ${lastError}`;
            saveStatus.style.color = 'var(--error)';
        }
        
        saveBtn.disabled = false;
    });
});

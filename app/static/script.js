document.addEventListener('DOMContentLoaded', () => {
    // Core elements
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const filenameDisplay = document.getElementById('selected-filename');
    const fileInfoDisplay = document.getElementById('file-info-display');
    const formatOptions = document.querySelectorAll('.format-option');
    const convertBtn = document.getElementById('convert-btn');
    const statusCard = document.getElementById('status-card');
    const resultCard = document.getElementById('result-card');
    const downloadLink = document.getElementById('download-link');
    const markdownPreview = document.getElementById('markdown-preview');
    const previewContainer = document.getElementById('preview-container');
    const copyBtn = document.getElementById('copy-btn');
    const saveBtn = document.getElementById('save-btn');
    const savePath = document.getElementById('save-path');
    const saveStatus = document.getElementById('save-status');
    const newConvBtn = document.getElementById('new-conv-btn');
    
    // History elements
    const historySection = document.getElementById('history-section');
    const historyList = document.getElementById('history-list');
    const clearHistoryBtn = document.getElementById('clear-history-btn');

    let selectedFile = null;
    let selectedFormat = null;
    let currentFileId = null;
    let currentOutputFilename = null;
    let rawMarkdown = "";

    // Initialization
    loadHistory();

    // File Selection Logic
    const handleFiles = (files) => {
        if (files.length > 0) {
            selectedFile = files[0];
            filenameDisplay.textContent = selectedFile.name;
            fileInfoDisplay.classList.remove('hidden');
            
            // Auto-suggestion based on extension
            suggestFormat(selectedFile.name);
            checkReady();
        }
    };

    const suggestFormat = (filename) => {
        const ext = filename.split('.').pop().toLowerCase();
        formatOptions.forEach(opt => {
            opt.classList.remove('active');
            const format = opt.dataset.format;
            if (ext === 'pptx' && (format === 'pptx-to-md' || format === 'pptx-to-pdf')) {
                opt.style.borderColor = 'var(--primary)';
            } else if (ext === 'pdf' && (format === 'pdf-to-md' || format === 'pdf-to-pptx')) {
                opt.style.borderColor = 'var(--primary)';
            } else {
                opt.style.borderColor = '';
            }
        });
    };

    dropZone.addEventListener('click', () => fileInput.click());
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
        convertBtn.disabled = !(selectedFile && selectedFormat);
    };

    // Conversion Process
    convertBtn.addEventListener('click', async () => {
        if (!selectedFile || !selectedFormat) return;

        // UI Feedback
        statusCard.classList.remove('hidden');
        resultCard.classList.add('hidden');
        convertBtn.disabled = true;

        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('format', selectedFormat);

        try {
            const response = await fetch('/convert', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                currentFileId = data.file_id;
                currentOutputFilename = data.filename;
                
                // Set Download
                downloadLink.href = `/download/${data.file_id}/${data.filename}`;
                
                // Handle Preview
                if (data.preview) {
                    rawMarkdown = data.preview;
                    renderMarkdown(data.preview);
                    previewContainer.classList.remove('hidden');
                    copyBtn.classList.remove('hidden');
                } else {
                    previewContainer.classList.add('hidden');
                    copyBtn.classList.add('hidden');
                }

                // Show results
                resultCard.classList.remove('hidden');
                resultCard.scrollIntoView({ behavior: 'smooth' });

                // Add to history
                addToHistory({
                    id: data.file_id,
                    name: data.filename,
                    format: selectedFormat,
                    date: new Date().toLocaleString()
                });
            } else {
                alert(`Error: ${data.detail}`);
            }
        } catch (err) {
            alert(`An error occurred: ${err.message}`);
        } finally {
            statusCard.classList.add('hidden');
            convertBtn.disabled = false;
        }
    });

    const renderMarkdown = (text) => {
        if (typeof marked !== 'undefined' && typeof DOMPurify !== 'undefined') {
            const html = marked.parse(text);
            markdownPreview.innerHTML = DOMPurify.sanitize(html);
            markdownPreview.className = "markdown-body"; // Ensure class for styling
        } else {
            markdownPreview.textContent = text;
        }
    };

    // UI Actions
    newConvBtn.addEventListener('click', () => {
        resetApp();
    });

    const resetApp = () => {
        selectedFile = null;
        selectedFormat = null;
        fileInput.value = '';
        fileInfoDisplay.classList.add('hidden');
        resultCard.classList.add('hidden');
        formatOptions.forEach(opt => opt.classList.remove('active'));
        checkReady();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    copyBtn.addEventListener('click', () => {
        navigator.clipboard.writeText(rawMarkdown).then(() => {
            const originalText = copyBtn.textContent;
            copyBtn.textContent = 'Copied!';
            copyBtn.classList.add('btn-accent');
            setTimeout(() => {
                copyBtn.textContent = originalText;
                copyBtn.classList.remove('btn-accent');
            }, 2000);
        });
    });

    // Local Storage History
    function loadHistory() {
        const history = JSON.parse(localStorage.getItem('conv_history') || '[]');
        renderHistoryList(history);
    }

    function addToHistory(item) {
        let history = JSON.parse(localStorage.getItem('conv_history') || '[]');
        // Keep only last 10
        history.unshift(item);
        history = history.slice(0, 10);
        localStorage.setItem('conv_history', JSON.stringify(history));
        renderHistoryList(history);
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
                    <a href="/download/${item.id}/${item.name}" class="btn btn-secondary btn-small" download>Download</a>
                </div>
            `;
            historyList.appendChild(div);
        });
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
        saveStatus.textContent = 'Saving...';
        
        try {
            const response = await fetch('/save-local', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    file_id: currentFileId,
                    target_path: path,
                    original_name: selectedFile ? selectedFile.name : currentOutputFilename
                })
            });

            const data = await response.json();
            if (data.success) {
                saveStatus.textContent = 'Saved successfully!';
                saveStatus.style.color = 'var(--accent)';
            } else {
                saveStatus.textContent = `Error: ${data.detail}`;
                saveStatus.style.color = 'var(--error)';
            }
        } catch (err) {
            saveStatus.textContent = `Error: ${err.message}`;
            saveStatus.style.color = 'var(--error)';
        } finally {
            saveBtn.disabled = false;
        }
    });
});

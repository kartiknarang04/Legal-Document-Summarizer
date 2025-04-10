document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');
    const fileInfo = document.getElementById('file-info');
    const fileName = document.getElementById('file-name');
    const changeFileBtn = document.getElementById('change-file');
    const submitButton = document.getElementById('submit-button');
    const loading = document.getElementById('loading');
    const uploadContainer = document.getElementById('upload-container');
    const resultSection = document.getElementById('result-section');
    const resultFilename = document.getElementById('result-filename');
    const summaryContent = document.getElementById('summary-content');
    const newUploadBtn = document.getElementById('new-upload');
    const historyList = document.getElementById('history-list');
    const modelInfo = document.getElementById('model-info');

    // File handling
    let selectedFile = null;

    // Fetch model info
    async function fetchModelInfo() {
        try {
            const response = await fetch('/model-info');
            const data = await response.json();
            
            // Update model badge
            const modelBadge = document.createElement('span');
            modelBadge.className = 'model-badge';
            modelBadge.textContent = data.fine_tuned 
                ? `Fine-tuned ${data.model_name.split('/').pop()}` 
                : data.model_name.split('/').pop();
            
            modelInfo.innerHTML = '';
            modelInfo.appendChild(modelBadge);
        } catch (error) {
            console.error('Error fetching model info:', error);
        }
    }

    // Event Listeners
    uploadArea.addEventListener('click', () => fileInput.click());
    
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('active');
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('active');
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('active');
        
        if (e.dataTransfer.files.length) {
            handleFile(e.dataTransfer.files[0]);
        }
    });
    
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length) {
            handleFile(e.target.files[0]);
        }
    });
    
    changeFileBtn.addEventListener('click', () => {
        resetFileSelection();
    });
    
    submitButton.addEventListener('click', uploadFile);
    
    newUploadBtn.addEventListener('click', () => {
        resultSection.style.display = 'none';
        uploadContainer.style.display = 'flex';
        resetFileSelection();
    });

    // Functions
    function handleFile(file) {
        if (file.type !== 'application/pdf') {
            alert('Please select a PDF file');
            return;
        }
        
        selectedFile = file;
        fileName.textContent = file.name;
        uploadArea.style.display = 'none';
        fileInfo.style.display = 'flex';
        submitButton.disabled = false;
    }
    
    function resetFileSelection() {
        selectedFile = null;
        fileInput.value = '';
        uploadArea.style.display = 'flex';
        fileInfo.style.display = 'none';
        submitButton.disabled = true;
    }
    
    async function uploadFile() {
        if (!selectedFile) return;
        
        const formData = new FormData();
        formData.append('file', selectedFile);
        
        uploadContainer.style.display = 'none';
        loading.style.display = 'flex';
        
        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.success) {
                displayResult(data);
                loadSummaryHistory();
            } else {
                alert(data.error || 'An error occurred during processing');
                uploadContainer.style.display = 'flex';
            }
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred. Please try again.');
            uploadContainer.style.display = 'flex';
        } finally {
            loading.style.display = 'none';
        }
    }
    
    function displayResult(data) {
        resultFilename.textContent = data.filename;
        summaryContent.textContent = data.summary;
        resultSection.style.display = 'block';
    }
    
    async function loadSummaryHistory() {
        try {
            const response = await fetch('/summaries');
            const summaries = await response.json();
            
            if (summaries.length === 0) {
                historyList.innerHTML = '<p>No previous summaries found.</p>';
                return;
            }
            
            historyList.innerHTML = '';
            
            summaries.forEach(summary => {
                const date = new Date(summary.upload_date);
                const formattedDate = date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
                
                const summaryPreview = summary.summary.length > 150 
                    ? summary.summary.substring(0, 150) + '...' 
                    : summary.summary;
                
                const historyItem = document.createElement('div');
                historyItem.className = 'history-item';
                historyItem.dataset.id = summary._id;
                historyItem.innerHTML = `
                    <h3>${summary.original_filename}</h3>
                    <p>${formattedDate}</p>
                    <div class="summary-preview">${summaryPreview}</div>
                `;
                
                historyItem.addEventListener('click', () => viewSummary(summary._id));
                
                historyList.appendChild(historyItem);
            });
        } catch (error) {
            console.error('Error loading history:', error);
            historyList.innerHTML = '<p>Error loading summary history.</p>';
        }
    }
    
    async function viewSummary(id) {
        try {
            const response = await fetch(`/summary/${id}`);
            const data = await response.json();
            
            resultFilename.textContent = data.original_filename;
            summaryContent.textContent = data.summary;
            
            uploadContainer.style.display = 'none';
            resultSection.style.display = 'block';
            
            // Scroll to result section
            resultSection.scrollIntoView({ behavior: 'smooth' });
        } catch (error) {
            console.error('Error viewing summary:', error);
            alert('Error loading summary. Please try again.');
        }
    }
    
    // Load model info and summary history on page load
    fetchModelInfo();
    loadSummaryHistory();
});

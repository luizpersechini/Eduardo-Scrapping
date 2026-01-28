// ANBIMA Scraper Web Application - Main JavaScript

// Global variables
let socket;
let currentJobId = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Initialize Socket.IO
    socket = io();
    
    // Setup Socket.IO event listeners
    setupSocketListeners();
    
    // Setup form handlers
    setupFormHandlers();
    
    // Load initial data
    loadStats();
    loadJobs();
    
    // Auto-refresh every 30 seconds
    setInterval(() => {
        if (!currentJobId) {
            loadStats();
            loadJobs();
        }
    }, 30000);
}

// Socket.IO Event Listeners
function setupSocketListeners() {
    socket.on('connect', () => {
        console.log('Connected to server');
        showToast('Conectado ao servidor', 'success');
    });
    
    socket.on('disconnect', () => {
        console.log('Disconnected from server');
        showToast('Desconectado do servidor', 'warning');
    });
    
    socket.on('job_update', (data) => {
        console.log('Job update:', data);
        updateActiveJob(data);
        loadStats();
    });
    
    socket.on('cnpj_update', (data) => {
        console.log('CNPJ update:', data);
        addLogEntry(data);
    });
}

// Form Handlers
function setupFormHandlers() {
    // File input
    const fileInput = document.getElementById('fileInput');
    const fileInfo = document.getElementById('fileInfo');
    
    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            fileInfo.textContent = `📄 ${file.name} (${(file.size / 1024).toFixed(2)} KB)`;
            fileInfo.classList.add('active');
        }
    });
    
    // Workers slider
    const workersInput = document.getElementById('workersInput');
    const workersValue = document.getElementById('workersValue');
    
    workersInput.addEventListener('input', (e) => {
        workersValue.textContent = e.target.value;
    });
    
    // Upload form
    const uploadForm = document.getElementById('uploadForm');
    uploadForm.addEventListener('submit', handleUpload);
}

// Handle file upload
async function handleUpload(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const submitButton = e.target.querySelector('button[type="submit"]');
    
    // Debug: Log form data
    console.log('FormData contents:');
    for (let [key, value] of formData.entries()) {
        console.log(`  ${key}: ${value}`);
    }
    
    // Disable button
    submitButton.disabled = true;
    submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processando...';
    
    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Check if stealth is enabled
            const stealthEnabled = formData.get('use_stealth') === 'on';
            
            showToast(`Job criado com sucesso! (${result.total_cnpjs} CNPJs)` + 
                (stealthEnabled ? ' - Modo Stealth ATIVO ✓' : ' - STEALTH DESATIVADO ⚠️'), 
                stealthEnabled ? 'success' : 'warning');
            
            // Ask user if they want to start immediately
            if (confirm(`Job ${result.job_id} criado com ${result.total_cnpjs} CNPJs.\n\n` +
                (stealthEnabled ? 
                    '✅ Modo Stealth: ATIVO\n' : 
                    '⚠️ Modo Stealth: DESATIVADO (pode bloquear!)\n') +
                `\nDeseja iniciar agora?`)) {
                await startJob(result.job_id);
            }
            
            // Reset form
            e.target.reset();
            document.getElementById('fileInfo').classList.remove('active');
            
            // Reload jobs
            loadJobs();
        } else {
            showToast(`Erro: ${result.error}`, 'error');
        }
    } catch (error) {
        console.error('Upload error:', error);
        showToast('Erro ao fazer upload', 'error');
    } finally {
        // Re-enable button
        submitButton.disabled = false;
        submitButton.innerHTML = '<i class="fas fa-upload"></i> Upload e Criar Job';
    }
}

// Start a job
async function startJob(jobId) {
    try {
        const response = await fetch(`/api/jobs/${jobId}/start`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            currentJobId = jobId;
            showActiveJob(jobId);
            showToast('Job iniciado!', 'success');
        } else {
            showToast(`Erro: ${result.error}`, 'error');
        }
    } catch (error) {
        console.error('Start job error:', error);
        showToast('Erro ao iniciar job', 'error');
    }
}

// Stop current job
async function stopCurrentJob() {
    if (!currentJobId) {
        showToast('Nenhum job ativo', 'warning');
        return;
    }
    
    if (!confirm('Tem certeza que deseja parar o job atual? Os CNPJs em progresso serão perdidos.')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/jobs/${currentJobId}/stop`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast('Job parado com sucesso', 'success');
            document.getElementById('activeJobSection').style.display = 'none';
            document.getElementById('stopJobBtn').style.display = 'none';
            currentJobId = null;
            loadJobs();
            loadStats();
        } else {
            showToast(`Erro: ${result.error}`, 'error');
        }
    } catch (error) {
        console.error('Stop job error:', error);
        showToast('Erro ao parar job', 'error');
    }
}

// Retry failed CNPJs
async function retryJob(jobId) {
    if (!confirm('Deseja tentar novamente os CNPJs que falharam?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/jobs/${jobId}/retry`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            currentJobId = jobId;
            showActiveJob(jobId);
            showToast(result.message, 'success');
        } else {
            showToast(`Erro: ${result.error}`, 'error');
        }
    } catch (error) {
        console.error('Retry job error:', error);
        showToast('Erro ao tentar novamente', 'error');
    }
}

// Fix stuck jobs
async function fixStuckJobs() {
    if (!confirm('Isso irá corrigir jobs que estão travados em "Em Andamento". Continuar?')) {
        return;
    }
    
    try {
        const response = await fetch('/api/jobs/fix-stuck', {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            if (result.fixed_jobs.length > 0) {
                showToast(`${result.fixed_jobs.length} job(s) corrigido(s)`, 'success');
            } else {
                showToast('Nenhum job travado encontrado', 'info');
            }
            loadJobs();
            loadStats();
        } else {
            showToast(`Erro: ${result.error}`, 'error');
        }
    } catch (error) {
        console.error('Fix stuck jobs error:', error);
        showToast('Erro ao corrigir jobs', 'error');
    }
}

// Download results
function downloadResults(jobId) {
    window.location.href = `/api/jobs/${jobId}/download`;
}

// Load statistics
async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const result = await response.json();
        
        if (result.success) {
            document.getElementById('totalJobs').textContent = result.stats.total_jobs;
            document.getElementById('completedJobs').textContent = result.stats.completed_jobs;
            document.getElementById('runningJobs').textContent = result.stats.running_jobs;
            document.getElementById('totalCNPJs').textContent = result.stats.total_cnpjs_scraped;
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Load jobs list
async function loadJobs() {
    try {
        const response = await fetch('/api/jobs');
        const result = await response.json();
        
        if (result.success) {
            displayJobs(result.jobs);
        }
    } catch (error) {
        console.error('Error loading jobs:', error);
    }
}

// Display jobs in the list
function displayJobs(jobs) {
    const jobsList = document.getElementById('jobsList');
    
    if (jobs.length === 0) {
        jobsList.innerHTML = `
            <div class="no-jobs">
                <i class="fas fa-inbox"></i>
                <p>Nenhum job encontrado. Faça upload de um arquivo Excel para começar!</p>
            </div>
        `;
        return;
    }
    
    jobsList.innerHTML = jobs.map(job => `
        <div class="job-item" onclick="viewJobDetails(${job.id})">
            <div class="job-item-header">
                <div class="job-item-title">
                    Job #${job.id} - ${job.filename}
                </div>
                <div class="job-item-status status-${job.status}">
                    ${getStatusText(job.status)}
                </div>
            </div>
            <div class="job-item-info">
                <div><i class="fas fa-list"></i> Total: ${job.total_cnpjs} CNPJs</div>
                <div><i class="fas fa-check"></i> Sucesso: ${job.successful_cnpjs}</div>
                <div><i class="fas fa-times"></i> Falhas: ${job.failed_cnpjs}</div>
                <div><i class="fas fa-percentage"></i> Progresso: ${job.progress_percentage}%</div>
                <div><i class="fas fa-cogs"></i> Workers: ${job.workers}</div>
                <div><i class="fas fa-clock"></i> Criado: ${formatDate(job.created_at)}</div>
            </div>
            <div class="job-item-actions" onclick="event.stopPropagation()">
                ${getJobActions(job)}
            </div>
        </div>
    `).join('');
}

// Get status text
function getStatusText(status) {
    const statusMap = {
        'pending': 'Pendente',
        'running': 'Em Andamento',
        'completed': 'Completo',
        'failed': 'Falhou',
        'cancelled': 'Cancelado'
    };
    return statusMap[status] || status;
}

// Get job actions buttons
function getJobActions(job) {
    let actions = '';
    
    if (job.status === 'pending') {
        actions += `<button class="btn btn-primary btn-sm" onclick="startJob(${job.id})">
            <i class="fas fa-play"></i> Iniciar
        </button>`;
    }
    
    if (job.status === 'completed' && job.output_file) {
        actions += `<button class="btn btn-success btn-sm" onclick="downloadResults(${job.id})">
            <i class="fas fa-download"></i> Download
        </button>`;
    }
    
    if ((job.status === 'completed' || job.status === 'failed') && job.failed_cnpjs > 0) {
        actions += `<button class="btn btn-danger btn-sm" onclick="retryJob(${job.id})">
            <i class="fas fa-redo"></i> Tentar Novamente (${job.failed_cnpjs})
        </button>`;
    }
    
    return actions;
}

// Show active job section
function showActiveJob(jobId) {
    const section = document.getElementById('activeJobSection');
    section.style.display = 'block';
    
    document.getElementById('activeJobId').textContent = jobId;
    document.getElementById('logContent').innerHTML = '';
    
    // Show stop button
    document.getElementById('stopJobBtn').style.display = 'inline-block';
    
    // Scroll to active job
    section.scrollIntoView({ behavior: 'smooth' });
}

// Update active job with real-time data
function updateActiveJob(data) {
    if (data.job_id !== currentJobId) return;
    
    // Update message
    if (data.message) {
        document.getElementById('activeJobMessage').textContent = data.message;
    }
    
    // Update progress
    if (data.progress !== undefined) {
        const progress = Math.round(data.progress);
        document.getElementById('activeJobProgress').textContent = `${progress}%`;
        document.getElementById('activeJobProgressBar').style.width = `${progress}%`;
    }
    
    // Update stats
    if (data.successful !== undefined) {
        document.getElementById('activeJobSuccess').textContent = data.successful;
    }
    if (data.failed !== undefined) {
        document.getElementById('activeJobFailed').textContent = data.failed;
    }
    
    // Update status
    if (data.status) {
        const badge = document.getElementById('activeJobStatus');
        badge.textContent = getStatusText(data.status);
        badge.className = `job-badge status-${data.status}`;
        
        // If completed, hide active section after 5 seconds and reload
        if (data.status === 'completed') {
            showToast('Job completado com sucesso!', 'success');
            document.getElementById('stopJobBtn').style.display = 'none';
            setTimeout(() => {
                document.getElementById('activeJobSection').style.display = 'none';
                currentJobId = null;
                loadJobs();
                loadStats();
            }, 5000);
        }
        
        if (data.status === 'failed') {
            showToast('Job falhou!', 'error');
            document.getElementById('stopJobBtn').style.display = 'none';
        }
        
        if (data.status === 'cancelled') {
            showToast('Job foi cancelado', 'warning');
            document.getElementById('stopJobBtn').style.display = 'none';
        }
    }
    
    // Add log entry for phase changes
    if (data.phase) {
        addLogEntry({
            cnpj: 'SYSTEM',
            status: data.phase,
            timestamp: data.timestamp
        });
    }
}

// Add entry to live log
function addLogEntry(data) {
    const logContent = document.getElementById('logContent');
    const timestamp = new Date(data.timestamp).toLocaleTimeString();
    
    const entry = document.createElement('div');
    entry.className = 'log-entry';
    
    let icon = '';
    let message = '';
    
    if (data.cnpj === 'SYSTEM') {
        icon = '<i class="fas fa-info-circle"></i>';
        message = data.status;
    } else {
        switch(data.status) {
            case 'processing':
                icon = '<i class="fas fa-spinner fa-spin"></i>';
                message = `${data.cnpj}`;
                if (data.detail) {
                    message += ` - ${data.detail}`;
                } else {
                    message = `Processando: ${message}`;
                }
                break;
            case 'success':
                icon = '<i class="fas fa-check" style="color: #10b981;"></i>';
                message = `✓ ${data.cnpj} - Sucesso`;
                if (data.detail) {
                    message += ` (${data.detail})`;
                }
                break;
            case 'failed':
                icon = '<i class="fas fa-times" style="color: #ef4444;"></i>';
                message = `✗ ${data.cnpj} - Falhou`;
                if (data.detail) {
                    message += ` (${data.detail})`;
                }
                break;
            case 'not_found':
                icon = '<i class="fas fa-question" style="color: #f59e0b;"></i>';
                message = `? ${data.cnpj} - Não encontrado`;
                break;
        }
    }
    
    entry.innerHTML = `
        <span class="timestamp">${timestamp}</span>
        ${icon}
        ${message}
    `;
    
    logContent.appendChild(entry);
    logContent.scrollTop = logContent.scrollHeight;
    
    // Keep only last 100 entries
    while (logContent.children.length > 100) {
        logContent.removeChild(logContent.firstChild);
    }
}

// View job details in modal
async function viewJobDetails(jobId) {
    try {
        const response = await fetch(`/api/jobs/${jobId}`);
        const result = await response.json();
        
        if (result.success) {
            displayJobDetailsModal(result.job, result.cnpjs);
        }
    } catch (error) {
        console.error('Error loading job details:', error);
        showToast('Erro ao carregar detalhes', 'error');
    }
}

// Display job details in modal
function displayJobDetailsModal(job, cnpjs) {
    const modal = document.getElementById('jobModal');
    const title = document.getElementById('modalJobTitle');
    const body = document.getElementById('modalJobDetails');
    
    title.textContent = `Job #${job.id} - Detalhes`;
    
    // Group CNPJs by status
    const success = cnpjs.filter(c => c.status === 'success');
    const failed = cnpjs.filter(c => c.status === 'failed');
    const notFound = cnpjs.filter(c => c.status === 'not_found');
    const pending = cnpjs.filter(c => c.status === 'pending');
    
    body.innerHTML = `
        <div>
            <h3>Informações do Job</h3>
            <p><strong>Arquivo:</strong> ${job.filename}</p>
            <p><strong>Status:</strong> <span class="status-${job.status}">${getStatusText(job.status)}</span></p>
            <p><strong>Workers:</strong> ${job.workers}</p>
            <p><strong>Total de CNPJs:</strong> ${job.total_cnpjs}</p>
            <p><strong>Sucesso:</strong> ${job.successful_cnpjs}</p>
            <p><strong>Falhas:</strong> ${job.failed_cnpjs}</p>
            <p><strong>Criado em:</strong> ${formatDate(job.created_at)}</p>
            ${job.completed_at ? `<p><strong>Completado em:</strong> ${formatDate(job.completed_at)}</p>` : ''}
        </div>
        
        ${success.length > 0 ? `
            <div style="margin-top: 30px;">
                <h3 style="color: #10b981;">✓ CNPJs com Sucesso (${success.length})</h3>
                <ul style="list-style: none; padding: 0;">
                    ${success.slice(0, 20).map(c => `
                        <li style="padding: 8px; border-bottom: 1px solid #e5e7eb;">
                            <strong>${c.cnpj}</strong> - ${c.fund_name || 'N/A'} 
                            <small>(${c.data_count} registros)</small>
                        </li>
                    `).join('')}
                    ${success.length > 20 ? `<li style="padding: 8px; font-style: italic;">... e mais ${success.length - 20}</li>` : ''}
                </ul>
            </div>
        ` : ''}
        
        ${failed.length > 0 ? `
            <div style="margin-top: 30px;">
                <h3 style="color: #ef4444;">✗ CNPJs com Falha (${failed.length})</h3>
                <ul style="list-style: none; padding: 0;">
                    ${failed.map(c => `
                        <li style="padding: 8px; border-bottom: 1px solid #e5e7eb;">
                            <strong>${c.cnpj}</strong>
                            ${c.error_message ? `<br><small style="color: #6b7280;">${c.error_message}</small>` : ''}
                        </li>
                    `).join('')}
                </ul>
            </div>
        ` : ''}
        
        ${notFound.length > 0 ? `
            <div style="margin-top: 30px;">
                <h3 style="color: #f59e0b;">? CNPJs Não Encontrados (${notFound.length})</h3>
                <ul style="list-style: none; padding: 0;">
                    ${notFound.map(c => `<li style="padding: 8px; border-bottom: 1px solid #e5e7eb;">${c.cnpj}</li>`).join('')}
                </ul>
            </div>
        ` : ''}
    `;
    
    modal.classList.add('active');
}

// Close modal
function closeModal() {
    document.getElementById('jobModal').classList.remove('active');
}

// Format date
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString('pt-BR');
}

// Show toast notification
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };
    
    toast.innerHTML = `
        <i class="fas ${icons[type] || icons.info}"></i>
        <span>${message}</span>
    `;
    
    container.appendChild(toast);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}



// Slideon - 主JavaScript文件

// 大纲生成对话框控制
function openOutlineModal() {
    const modal = document.getElementById('outlineModal');
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeOutlineModal() {
    const modal = document.getElementById('outlineModal');
    modal.classList.remove('active');
    document.body.style.overflow = '';
}

// 生成大纲
function generateOutline() {
    // 显示加载状态
    const btn = document.querySelector('.modal-footer .btn-primary');
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 生成中...';
    btn.disabled = true;
    
    // 模拟生成过程
    setTimeout(() => {
        btn.innerHTML = originalText;
        btn.disabled = false;
        closeOutlineModal();
        
        // 跳转到编辑器页面
        window.location.href = 'pages/editor.html';
    }, 2000);
}

// 页数滑块控制
document.addEventListener('DOMContentLoaded', function() {
    const pageSlider = document.getElementById('pageSlider');
    const pageCount = document.getElementById('pageCount');
    
    if (pageSlider && pageCount) {
        pageSlider.addEventListener('input', function() {
            pageCount.textContent = this.value;
        });
    }
    
    // 风格选择
    const styleCards = document.querySelectorAll('.style-card');
    styleCards.forEach(card => {
        card.addEventListener('click', function() {
            styleCards.forEach(c => c.classList.remove('active'));
            this.classList.add('active');
        });
    });
    
    // 字符计数
    const textarea = document.querySelector('.modal-body textarea');
    const charCount = document.querySelector('.char-count');
    
    if (textarea && charCount) {
        textarea.addEventListener('input', function() {
            const count = this.value.length;
            charCount.textContent = `${count}/500`;
            
            if (count > 500) {
                charCount.style.color = 'var(--error-500)';
            } else {
                charCount.style.color = 'var(--gray-400)';
            }
        });
    }
    
    // 文件上传区域
    const uploadArea = document.querySelector('.upload-area');
    if (uploadArea) {
        uploadArea.addEventListener('click', function() {
            // 创建隐藏的文件输入
            const fileInput = document.createElement('input');
            fileInput.type = 'file';
            fileInput.accept = '.pdf,.docx,.txt,.md';
            fileInput.onchange = function(e) {
                if (e.target.files.length > 0) {
                    const file = e.target.files[0];
                    showToast(`已选择文件: ${file.name}`);
                }
            };
            fileInput.click();
        });
        
        // 拖拽效果
        uploadArea.addEventListener('dragover', function(e) {
            e.preventDefault();
            this.style.borderColor = 'var(--primary-400)';
            this.style.background = 'var(--primary-50)';
        });
        
        uploadArea.addEventListener('dragleave', function(e) {
            e.preventDefault();
            this.style.borderColor = '';
            this.style.background = '';
        });
        
        uploadArea.addEventListener('drop', function(e) {
            e.preventDefault();
            this.style.borderColor = '';
            this.style.background = '';
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                const file = files[0];
                showToast(`已上传文件: ${file.name}`);
            }
        });
    }
    
    // Tab切换
    const tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            tabBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
        });
    });
    
    // 项目卡片点击
    const projectCards = document.querySelectorAll('.project-card:not(.project-card-new)');
    projectCards.forEach(card => {
        card.addEventListener('click', function(e) {
            // 如果点击的是编辑按钮，不跳转
            if (e.target.closest('.btn')) {
                e.stopPropagation();
                window.location.href = 'pages/editor.html';
                return;
            }
            // 否则显示预览或详情
            showToast('正在打开项目...');
        });
    });
    
    // 模板卡片点击
    const templateCards = document.querySelectorAll('.template-card');
    templateCards.forEach(card => {
        card.addEventListener('click', function() {
            showToast('正在应用模板...');
            setTimeout(() => {
                window.location.href = 'pages/editor.html';
            }, 1000);
        });
    });
});

// Toast提示
function showToast(message, duration = 3000) {
    // 移除现有的toast
    const existingToast = document.querySelector('.toast-message');
    if (existingToast) {
        existingToast.remove();
    }
    
    // 创建新的toast
    const toast = document.createElement('div');
    toast.className = 'toast-message';
    toast.innerHTML = `
        <div class="toast-content">
            <i class="fas fa-info-circle"></i>
            <span>${message}</span>
        </div>
    `;
    
    // 添加样式
    toast.style.cssText = `
        position: fixed;
        top: 80px;
        left: 50%;
        transform: translateX(-50%) translateY(-20px);
        background: var(--gray-800);
        color: white;
        padding: 12px 24px;
        border-radius: 8px;
        box-shadow: 0 10px 15px rgba(0,0,0,0.1);
        opacity: 0;
        transition: all 0.3s ease;
        z-index: 9999;
    `;
    
    document.body.appendChild(toast);
    
    // 显示动画
    requestAnimationFrame(() => {
        toast.style.opacity = '1';
        toast.style.transform = 'translateX(-50%) translateY(0)';
    });
    
    // 自动隐藏
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(-50%) translateY(-20px)';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// 搜索功能
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.querySelector('.search-input');
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                const query = this.value.trim();
                if (query) {
                    showToast(`搜索: ${query}`);
                }
            }
        });
    }
    
    // Hero搜索框
    const heroSearchInput = document.querySelector('.search-input-large input');
    if (heroSearchInput) {
        heroSearchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                const query = this.value.trim();
                if (query) {
                    openOutlineModal();
                }
            }
        });
    }
});

// ESC键关闭模态框
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeOutlineModal();
    }
});

// 导航链接高亮
document.addEventListener('DOMContentLoaded', function() {
    const currentPage = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (currentPage.includes(href) && href !== 'index.html') {
            link.classList.add('active');
        } else if (currentPage.endsWith('/') || currentPage.endsWith('index.html')) {
            if (href === 'index.html') {
                link.classList.add('active');
            }
        }
    });
});

// 平滑滚动
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// 滚动时Header阴影
document.addEventListener('DOMContentLoaded', function() {
    const header = document.querySelector('.header');
    if (header) {
        window.addEventListener('scroll', function() {
            if (window.scrollY > 10) {
                header.style.boxShadow = 'var(--shadow-md)';
            } else {
                header.style.boxShadow = 'var(--shadow-sm)';
            }
        });
    }
});

// 文件上传管理
let uploadedFiles = [];

// 初始化文件上传功能
document.addEventListener('DOMContentLoaded', function() {
    const fileUploadArea = document.getElementById('fileUploadArea');
    const fileInput = document.getElementById('fileInput');
    
    if (fileUploadArea && fileInput) {
        // 点击上传区域触发文件选择
        fileUploadArea.addEventListener('click', function(e) {
            if (e.target !== fileInput) {
                fileInput.click();
            }
        });
        
        // 文件选择处理
        fileInput.addEventListener('change', function(e) {
            handleFiles(e.target.files);
        });
        
        // 拖拽效果
        fileUploadArea.addEventListener('dragover', function(e) {
            e.preventDefault();
            e.stopPropagation();
            this.classList.add('dragover');
        });
        
        fileUploadArea.addEventListener('dragleave', function(e) {
            e.preventDefault();
            e.stopPropagation();
            this.classList.remove('dragover');
        });
        
        fileUploadArea.addEventListener('drop', function(e) {
            e.preventDefault();
            e.stopPropagation();
            this.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                handleFiles(files);
            }
        });
    }
});

// 处理文件
function handleFiles(files) {
    const validTypes = ['.pdf', '.docx', '.txt', '.md', '.doc', '.pptx'];
    const maxSize = 20 * 1024 * 1024; // 20MB
    
    Array.from(files).forEach(file => {
        const extension = '.' + file.name.split('.').pop().toLowerCase();
        
        // 验证文件类型
        if (!validTypes.includes(extension)) {
            showToast(`不支持的文件格式: ${file.name}`, 3000);
            return;
        }
        
        // 验证文件大小
        if (file.size > maxSize) {
            showToast(`文件过大: ${file.name} (最大20MB)`, 3000);
            return;
        }
        
        // 检查是否已存在
        if (uploadedFiles.some(f => f.name === file.name && f.size === file.size)) {
            showToast(`文件已存在: ${file.name}`, 3000);
            return;
        }
        
        // 添加到上传列表
        const fileData = {
            id: Date.now() + Math.random(),
            name: file.name,
            size: file.size,
            type: extension,
            file: file,
            status: 'uploading'
        };
        
        uploadedFiles.push(fileData);
        addFileToList(fileData);
        
        // 模拟上传过程
        simulateUpload(fileData);
    });
    
    updateFilesDisplay();
}

// 模拟上传过程
function simulateUpload(fileData) {
    const fileItem = document.querySelector(`[data-file-id="${fileData.id}"]`);
    if (!fileItem) return;
    
    const progressBar = fileItem.querySelector('.upload-progress-bar');
    const statusEl = fileItem.querySelector('.file-status');
    
    let progress = 0;
    const interval = setInterval(() => {
        progress += Math.random() * 30;
        if (progress >= 100) {
            progress = 100;
            clearInterval(interval);
            
            // 上传完成
            fileData.status = 'success';
            if (progressBar) {
                progressBar.style.width = '100%';
            }
            if (statusEl) {
                statusEl.innerHTML = '<i class="fas fa-check-circle"></i> 上传成功';
                statusEl.className = 'file-status success';
            }
            
            // 2秒后隐藏进度条
            setTimeout(() => {
                const progressContainer = fileItem.querySelector('.upload-progress');
                if (progressContainer) {
                    progressContainer.style.display = 'none';
                }
            }, 1000);
            
            showToast(`文件上传成功: ${fileData.name}`);
        } else {
            if (progressBar) {
                progressBar.style.width = progress + '%';
            }
        }
    }, 200);
}

// 添加文件到列表
function addFileToList(fileData) {
    const filesList = document.getElementById('filesList');
    if (!filesList) return;
    
    const fileIcon = getFileIcon(fileData.type);
    const fileSize = formatFileSize(fileData.size);
    
    const fileItem = document.createElement('div');
    fileItem.className = 'file-item';
    fileItem.setAttribute('data-file-id', fileData.id);
    fileItem.innerHTML = `
        <div class="file-icon ${fileData.type.replace('.', '')}">
            <i class="${fileIcon}"></i>
        </div>
        <div class="file-info">
            <div class="file-name">${escapeHtml(fileData.name)}</div>
            <div class="file-meta">
                <span class="file-size">${fileSize}</span>
                <span class="file-status uploading">
                    <i class="fas fa-spinner fa-spin"></i> 上传中...
                </span>
            </div>
            <div class="upload-progress">
                <div class="upload-progress-bar" style="width: 0%"></div>
            </div>
        </div>
        <button class="file-remove" onclick="removeFile(${fileData.id})" title="删除文件">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    filesList.appendChild(fileItem);
}

// 获取文件图标
function getFileIcon(type) {
    const iconMap = {
        '.pdf': 'fas fa-file-pdf',
        '.docx': 'fas fa-file-word',
        '.doc': 'fas fa-file-word',
        '.txt': 'fas fa-file-alt',
        '.md': 'fas fa-file-code',
        '.pptx': 'fas fa-file-powerpoint'
    };
    return iconMap[type] || 'fas fa-file';
}

// 格式化文件大小
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

// 删除文件
function removeFile(fileId) {
    const fileItem = document.querySelector(`[data-file-id="${fileId}"]`);
    if (fileItem) {
        fileItem.style.opacity = '0';
        fileItem.style.transform = 'translateX(20px)';
        setTimeout(() => {
            fileItem.remove();
            uploadedFiles = uploadedFiles.filter(f => f.id !== fileId);
            updateFilesDisplay();
        }, 300);
    }
}

// 清空所有文件
function clearAllFiles() {
    if (uploadedFiles.length === 0) return;
    
    const filesList = document.getElementById('filesList');
    if (filesList) {
        const fileItems = filesList.querySelectorAll('.file-item');
        fileItems.forEach((item, index) => {
            setTimeout(() => {
                item.style.opacity = '0';
                item.style.transform = 'translateX(20px)';
            }, index * 50);
        });
        
        setTimeout(() => {
            filesList.innerHTML = '';
            uploadedFiles = [];
            updateFilesDisplay();
            showToast('已清空所有文件');
        }, fileItems.length * 50 + 300);
    }
}

// 更新文件显示
function updateFilesDisplay() {
    const uploadedFilesContainer = document.getElementById('uploadedFiles');
    const filesCount = document.getElementById('filesCount');
    
    if (uploadedFilesContainer && filesCount) {
        if (uploadedFiles.length > 0) {
            uploadedFilesContainer.style.display = 'block';
            filesCount.textContent = `${uploadedFiles.length} 个文件`;
            
            // 添加动画效果
            uploadedFilesContainer.style.opacity = '0';
            uploadedFilesContainer.style.transform = 'translateY(10px)';
            setTimeout(() => {
                uploadedFilesContainer.style.transition = 'all 0.3s ease';
                uploadedFilesContainer.style.opacity = '1';
                uploadedFilesContainer.style.transform = 'translateY(0)';
            }, 10);
        } else {
            uploadedFilesContainer.style.display = 'none';
        }
    }
}

// HTML转义
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 动画观察器
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('animate-visible');
        }
    });
}, observerOptions);

document.addEventListener('DOMContentLoaded', function() {
    // 观察需要动画的元素
    const animateElements = document.querySelectorAll('.feature-card, .project-card, .template-card');
    animateElements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
        observer.observe(el);
    });
});

// 添加动画类样式
const style = document.createElement('style');
style.textContent = `
    .animate-visible {
        opacity: 1 !important;
        transform: translateY(0) !important;
    }
`;
document.head.appendChild(style);

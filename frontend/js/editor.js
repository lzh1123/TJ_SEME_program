// Slideon 编辑器 - JavaScript文件

// 侧边栏Tab切换
document.addEventListener('DOMContentLoaded', function() {
    const sidebarTabs = document.querySelectorAll('.sidebar-tab');
    const sidebarContents = document.querySelectorAll('.sidebar-content');
    
    sidebarTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const targetTab = this.dataset.tab;
            
            // 切换Tab样式
            sidebarTabs.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            
            // 切换内容
            sidebarContents.forEach(content => {
                content.classList.remove('active');
            });
            
            if (targetTab === 'outline') {
                document.getElementById('outlinePanel').classList.add('active');
            } else if (targetTab === 'slides') {
                document.getElementById('slidesPanel').classList.add('active');
            }
        });
    });
    
    // 大纲展开/折叠
    const outlineItems = document.querySelectorAll('.outline-item');
    outlineItems.forEach(item => {
        const header = item.querySelector('.outline-header');
        if (header) {
            header.addEventListener('click', function() {
                item.classList.toggle('expanded');
                const icon = this.querySelector('.toggle-icon');
                if (icon) {
                    if (item.classList.contains('expanded')) {
                        icon.classList.remove('fa-chevron-right');
                        icon.classList.add('fa-chevron-down');
                    } else {
                        icon.classList.remove('fa-chevron-down');
                        icon.classList.add('fa-chevron-right');
                    }
                }
            });
        }
    });
    
    // 页面选择
    const outlinePages = document.querySelectorAll('.outline-item-page');
    const slideThumbs = document.querySelectorAll('.slide-thumb');
    
    function selectPage(index) {
        // 更新大纲选中状态
        outlinePages.forEach((page, i) => {
            page.classList.toggle('active', i === index);
        });
        
        // 更新缩略图选中状态
        slideThumbs.forEach((thumb, i) => {
            thumb.classList.toggle('active', i === index);
        });
        
        // 更新页码指示器
        const pageIndicator = document.querySelector('.page-indicator');
        if (pageIndicator) {
            pageIndicator.textContent = `${index + 1} / 10`;
        }
    }
    
    outlinePages.forEach((page, index) => {
        page.addEventListener('click', () => selectPage(index));
    });
    
    slideThumbs.forEach((thumb, index) => {
        thumb.addEventListener('click', () => selectPage(index));
    });
    
    // 添加页面按钮
    const addPageBtn = document.querySelector('.add-page-btn');
    if (addPageBtn) {
        addPageBtn.addEventListener('click', function() {
            showToast('正在添加新页面...');
            // 这里可以添加实际的页面添加逻辑
        });
    }
});

// AI聊天功能
let chatHistory = [];

function sendMessage() {
    const input = document.querySelector('.ai-input');
    const message = input.value.trim();
    
    if (!message) return;
    
    // 添加用户消息
    addMessage(message, 'user');
    
    // 清空输入框
    input.value = '';
    input.style.height = 'auto';
    
    // 显示AI正在输入
    showGeneratingToast();
    
    // 模拟AI回复
    setTimeout(() => {
        hideGeneratingToast();
        const response = generateAIResponse(message);
        addMessage(response, 'ai');
    }, 1500);
}

function sendQuickMessage(message) {
    const input = document.querySelector('.ai-input');
    input.value = message;
    sendMessage();
}

function addMessage(content, type) {
    const chatContainer = document.getElementById('chatMessages');
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    
    if (type === 'user') {
        messageDiv.innerHTML = `
            <div class="message-content">
                <p>${escapeHtml(content)}</p>
            </div>
        `;
    } else {
        messageDiv.innerHTML = `
            <div class="ai-avatar-small">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message-content">
                <p>${content}</p>
            </div>
        `;
    }
    
    chatContainer.appendChild(messageDiv);
    
    // 滚动到底部
    const chatWrapper = document.querySelector('.ai-chat-container');
    chatWrapper.scrollTop = chatWrapper.scrollHeight;
    
    // 保存到历史
    chatHistory.push({ type, content });
}

function generateAIResponse(userMessage) {
    const responses = {
        '优化': '我已经为您优化了当前页面的内容，使其更加简洁有力。主要改进包括：\n\n1. 标题更加醒目\n2. 要点更加精炼\n3. 添加了数据支撑',
        '图片': '根据您的内容，我建议使用以下配图：\n\n1. 产品展示图 - 突出核心功能\n2. 数据图表 - 展示增长趋势\n3. 场景图 - 展示应用场景',
        '风格': '我为您准备了3种风格方案：\n\n1. 商务蓝 - 专业稳重\n2. 科技紫 - 创新前卫\n3. 简约白 - 清爽现代\n\n您喜欢哪一种？',
        '数据': '我为您补充了以下数据：\n\n• 市场规模：预计2025年达到1000亿\n• 增长率：年复合增长率25%\n• 用户满意度：95%的用户给予好评',
        'default': '我理解您的需求。让我为您处理这个问题。请稍等片刻，我正在分析最佳方案...'
    };
    
    for (const key in responses) {
        if (userMessage.includes(key)) {
            return responses[key];
        }
    }
    
    return responses['default'];
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 输入框自动调整高度
document.addEventListener('DOMContentLoaded', function() {
    const aiInput = document.querySelector('.ai-input');
    if (aiInput) {
        aiInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 100) + 'px';
        });
        
        aiInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }
});

// Toast提示
function showToast(message) {
    // 创建toast元素
    const toast = document.createElement('div');
    toast.className = 'editor-toast';
    toast.innerHTML = `
        <i class="fas fa-check-circle"></i>
        <span>${message}</span>
    `;
    
    toast.style.cssText = `
        position: fixed;
        bottom: 48px;
        left: 50%;
        transform: translateX(-50%);
        background: var(--gray-800);
        color: white;
        padding: 12px 24px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 14px;
        box-shadow: 0 10px 15px rgba(0,0,0,0.2);
        z-index: 9999;
        opacity: 0;
        transition: opacity 0.3s ease;
    `;
    
    document.body.appendChild(toast);
    
    requestAnimationFrame(() => {
        toast.style.opacity = '1';
    });
    
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// 生成中提示
function showGeneratingToast() {
    const toast = document.getElementById('generatingToast');
    if (toast) {
        toast.classList.add('show');
    }
}

function hideGeneratingToast() {
    const toast = document.getElementById('generatingToast');
    if (toast) {
        toast.classList.remove('show');
    }
}

// 缩放控制
document.addEventListener('DOMContentLoaded', function() {
    let currentZoom = 100;
    const zoomLevel = document.querySelector('.zoom-level');
    const canvas = document.querySelector('.slide-canvas');
    
    const zoomOutBtn = document.querySelector('.toolbar-btn[title="缩小"]');
    const zoomInBtn = document.querySelector('.toolbar-btn[title="放大"]');
    
    if (zoomOutBtn) {
        zoomOutBtn.addEventListener('click', function() {
            if (currentZoom > 50) {
                currentZoom -= 10;
                updateZoom();
            }
        });
    }
    
    if (zoomInBtn) {
        zoomInBtn.addEventListener('click', function() {
            if (currentZoom < 200) {
                currentZoom += 10;
                updateZoom();
            }
        });
    }
    
    function updateZoom() {
        zoomLevel.textContent = `${currentZoom}%`;
        canvas.style.transform = `scale(${currentZoom / 100})`;
        canvas.style.transformOrigin = 'center center';
    }
});

// 工具栏按钮
document.addEventListener('DOMContentLoaded', function() {
    // 撤销/重做
    const undoBtn = document.querySelector('.toolbar-btn[title="撤销"]');
    const redoBtn = document.querySelector('.toolbar-btn[title="重做"]');
    
    if (undoBtn) {
        undoBtn.addEventListener('click', () => showToast('已撤销'));
    }
    
    if (redoBtn) {
        redoBtn.addEventListener('click', () => showToast('已重做'));
    }
    
    // 播放按钮
    const playBtn = document.querySelector('.toolbar-btn[title="播放"]');
    if (playBtn) {
        playBtn.addEventListener('click', () => {
            showToast('开始演示模式');
        });
    }
    
    // 插入、布局、主题下拉菜单
    const dropdownBtns = document.querySelectorAll('.toolbar-btn');
    dropdownBtns.forEach(btn => {
        const title = btn.getAttribute('title');
        if (title && ['插入', '布局', '主题'].includes(title)) {
            btn.addEventListener('click', function() {
                showToast(`打开${title}菜单`);
            });
        }
    });
});

// 项目标题编辑
document.addEventListener('DOMContentLoaded', function() {
    const titleInput = document.querySelector('.project-title-input');
    if (titleInput) {
        titleInput.addEventListener('blur', function() {
            if (this.value.trim()) {
                showToast('标题已保存');
            }
        });
        
        titleInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                this.blur();
            }
        });
    }
});

// 保存功能
document.addEventListener('DOMContentLoaded', function() {
    const saveBtn = document.querySelector('.header-right .btn-secondary');
    if (saveBtn) {
        saveBtn.addEventListener('click', function() {
            showToast('保存成功');
            
            // 更新保存状态
            const status = document.querySelector('.project-status');
            if (status) {
                status.innerHTML = '<i class="fas fa-check"></i> 已保存';
                status.classList.add('saved');
            }
        });
    }
    
    // 自动保存（每30秒）
    setInterval(() => {
        const status = document.querySelector('.project-status');
        if (status && !status.classList.contains('saved')) {
            status.innerHTML = '<i class="fas fa-sync fa-spin"></i> 保存中...';
            
            setTimeout(() => {
                status.innerHTML = '<i class="fas fa-check"></i> 已保存';
                status.classList.add('saved');
            }, 1000);
        }
    }, 30000);
});

// 键盘快捷键
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + S 保存
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        const saveBtn = document.querySelector('.header-right .btn-secondary');
        if (saveBtn) saveBtn.click();
    }
    
    // Ctrl/Cmd + Z 撤销
    if ((e.ctrlKey || e.metaKey) && e.key === 'z') {
        e.preventDefault();
        const undoBtn = document.querySelector('.toolbar-btn[title="撤销"]');
        if (undoBtn) undoBtn.click();
    }
    
    // Ctrl/Cmd + Shift + Z 重做
    if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'z') {
        e.preventDefault();
        const redoBtn = document.querySelector('.toolbar-btn[title="重做"]');
        if (redoBtn) redoBtn.click();
    }
});

// 导出功能
document.addEventListener('DOMContentLoaded', function() {
    const exportBtn = document.querySelector('.dropdown .btn-primary');
    if (exportBtn) {
        exportBtn.addEventListener('click', function() {
            showToast('正在准备导出选项...');
        });
    }
});

// 分享功能
document.addEventListener('DOMContentLoaded', function() {
    const shareBtn = document.querySelector('.header-right .btn-secondary:nth-child(2)');
    if (shareBtn) {
        shareBtn.addEventListener('click', function() {
            showToast('分享链接已复制到剪贴板');
        });
    }
});

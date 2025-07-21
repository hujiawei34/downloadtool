// modal.js - 弹窗功能模块

/**
 * 显示一个居中弹窗
 * @param {string} title - 弹窗标题
 * @param {string} message - 弹窗内容
 * @param {function} onClose - 关闭弹窗后的回调函数
 */
export function showModal(title, message, onClose = null) {
  // 确保消息正确编码
  try {
    // 尝试解码可能是转义的Unicode字符串
    if (message && typeof message === 'string') {
      // 处理Unicode转义序列
      message = decodeURIComponent(JSON.parse(`"${message.replace(/"/g, '\\"')}"`));
    }
  } catch (e) {
    console.warn('消息解码失败，使用原始消息', e);
    // 如果解码失败，使用原始消息
  }
  
  // 创建弹窗元素
  const modal = document.createElement('div');
  modal.className = 'modal-overlay';
  
  modal.innerHTML = `
    <div class="modal-container">
      <div class="modal-header">
        <div class="modal-title">${title}</div>
        <div class="modal-close">&times;</div>
      </div>
      <div class="modal-body">
        ${message}
      </div>
      <div class="modal-footer">
        <button class="modal-button">确定</button>
      </div>
    </div>
  `;
  
  // 添加到页面
  document.body.appendChild(modal);
  
  // 绑定事件
  const closeBtn = modal.querySelector('.modal-close');
  const confirmBtn = modal.querySelector('.modal-button');
  
  function closeModal() {
    document.body.removeChild(modal);
    if (onClose && typeof onClose === 'function') {
      onClose();
    }
  }
  
  closeBtn.addEventListener('click', closeModal);
  confirmBtn.addEventListener('click', closeModal);
  
  // 也允许点击背景关闭弹窗
  modal.addEventListener('click', function(e) {
    if (e.target === modal) {
      closeModal();
    }
  });
  
  // 添加 ESC 键关闭弹窗功能
  function handleEsc(e) {
    if (e.key === 'Escape') {
      closeModal();
      document.removeEventListener('keydown', handleEsc);
    }
  }
  
  document.addEventListener('keydown', handleEsc);
}

/**
 * 显示错误弹窗
 * @param {string} error - 错误信息
 * @param {function} onClose - 关闭后的回调
 */
export function showErrorModal(error, onClose = null) {
  showModal('错误', error, onClose);
} 
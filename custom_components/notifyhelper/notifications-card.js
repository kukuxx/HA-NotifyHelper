class NotificationCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this.previousNotifications = [];
    this._handleImageClick = this._handleImageClick.bind(this);
    this._handleFullscreenClick = this._handleFullscreenClick.bind(this);
    this._eventSubscription = null;
    this._isFirstRender = true;
  }

  setConfig(config) {
    if (!config.person_name) {
      throw new Error("person_name configuration is required");
    }

    // 配置基本參數
    this.config = {
      font_size: this._validateConfig(config.font_size, '16px', /^\d+(\.\d+)?(px|rem|em)$/),
      line_height: parseFloat(config.line_height) > 0 ? config.line_height : 1,
      ...config
    };

    // 設置媒體尺寸
    if (config.media_width) {
      this.style.setProperty('--media-width',
        this._validateConfig(config.media_width, '100%', /^\d+(\.\d+)?(px|%)$/, 'auto'));
    }
    if (config.media_height) {
      this.style.setProperty('--media-height',
        this._validateConfig(config.media_height, 'auto', /^\d+(\.\d+)?(px|%)$/, 'auto'));
    }
  }

  _validateConfig(value, defaultValue, regex, extraValue = null) {
    if (typeof value !== 'string') return defaultValue;
    return (regex.test(value) || value === extraValue) ? value : defaultValue;
  }

  set hass(hass) {
    if (!this.config) return;
    this._hass = hass;

    const stateObj = hass.states[`person.${this.config.person_name}`];
    if (!stateObj) {
      this._renderError(`Person not found: ${this.config.person_name}`);
      return;
    }

    this.previousNotifications = JSON.parse(localStorage.getItem(`savedNotifications_${this.config.person_name}`) || "[]")

    // 首次渲染通知
    if (this._isFirstRender) {
      this._render(hass, this.previousNotifications);
      this._subscribeToEvents(hass);
      this._isFirstRender = false;
    }

    // 設置事件監聽
    const container = this.shadowRoot.querySelector('.notifications-container');
    const fullscreenContainer = this.shadowRoot.querySelector('.fullscreen-container');

    container.addEventListener('click', this._handleImageClick);
    fullscreenContainer.addEventListener('click', this._handleFullscreenClick);
  }

  // 訂閱通知更新事件
  _subscribeToEvents(hass) {
    try {
      this.unsubscribe = hass.connection.subscribeMessage((event) => {

        // console.log("收到事件:", event);
        if (event.event_type === "update" &&
          event.person.includes(this.config.person_name)) {

          const newNotifications = event.notifications || [];
          // 只有當通知變更時才重新渲染
          if (this._notificationsChanged(newNotifications)) {
            this._render(hass, newNotifications);
            this.previousNotifications = [...newNotifications];
            localStorage.setItem(
              `savedNotifications_${this.config.person_name}`,
              JSON.stringify(this.previousNotifications)
            );
          }
        }
      }, { type: `notifyhelper/${this.config.person_name}` });

      this._eventSubscription = this.unsubscribe;
    } catch (error) {
      console.error("Unexpected error in subscription:", error);
      this._eventSubscription = null;
    }
  }

  _notificationsChanged(newNotifications) {
    if (newNotifications.length !== this.previousNotifications.length) return true;
    return newNotifications.some((n, i) => n !== this.previousNotifications[i]);
  }

  _handleImageClick(event) {
    if (event.target.tagName.toLowerCase() === 'img') {
      const fullscreenContainer = this.shadowRoot.querySelector('.fullscreen-container');
      const fullscreenImage = this.shadowRoot.querySelector('.fullscreen-image');
      fullscreenImage.src = event.target.src;
      fullscreenContainer.classList.add('active');
    }
  }

  _handleFullscreenClick(event) {
    if (event.target.classList.contains('fullscreen-container')) {
      event.target.classList.remove('active');
    }
  }

  _render(hass, notifications) {
    notifications = notifications.length > 0 ? notifications : ["No notifications available."];
    const theme = hass.themes?.darkMode ? "dark" : "light";
    const styles = this._getStyles(theme);
    const notificationsHTML = notifications.map(
      n => `<div class="bubble">${this._processContent(n)}</div>`
    ).join('');

    // 渲染到 shadow DOM
    this.shadowRoot.innerHTML = `
      <style>${styles}</style>
      <div class="notifications-container">${notificationsHTML}</div>
      <div class="fullscreen-container">
        <img class="fullscreen-image" src="" alt="Fullscreen Image">
      </div>
    `;
  }

  _getStyles(theme) {
    const isDark = theme === "dark";
    const backgroundColor = isDark ? "#444" : "#f1f1f1";
    const textColor = isDark ? "#fff" : "#333";

    return `
      .notifications-container { padding: 10px; }
      .bubble {
        background-color: ${backgroundColor};
        color: ${textColor};
        font-size: ${this.config.font_size};
        line-height: ${parseFloat(this.config.font_size) * this.config.line_height}px;
        border-radius: 25px;
        padding: 10px 15px;
        margin: 20px;
        width: 60%;
        word-wrap: break-word;
        word-break: break-word;
        opacity: 0;
        animation: fadeIn 0.3s forwards;
      }
      .bubble video, .bubble img {
        max-width: var(--media-width, 100%);
        height: var(--media-height, auto);  
        border-radius: 15px;
        display: block;
        cursor: pointer;
        transition: transform 0.3s ease;
      }
      .bubble img:hover { transform: scale(1.05); }
      .fullscreen-container {
        display: none;
        position: fixed;
        top: 0; left: 0;
        width: 100%; height: 100%;
        background-color: rgba(0, 0, 0, 0.9);
        z-index: 1000;
        justify-content: center;
        align-items: center;
        cursor: pointer;
      }
      .fullscreen-container.active { display: flex; }
      .fullscreen-image {
        max-width: 90%;
        max-height: 90%;
        object-fit: contain;
      }
      @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
      }
      @media (max-width: 768px) {
        .bubble { width: auto; margin: 10px; }
      }
      @media (min-width: 1024px) {
        .bubble { width: 77%; } 
        .bubble video, .bubble img { max-width: var(--media-width, 35%); }
      }
    `;
  }

  _processContent(content) {
    const temp = document.createElement('div');
    temp.innerHTML = content;

    // 驗證訊息
    this._sanitizeContent(temp);
    return temp.innerHTML;
  }

  _sanitizeContent(node) {
    const ALLOWED_TAGS = new Set([
      'ha-alert', 'blockquote', 'font', 'img', 'video', 'source',
      'strong', 'b', 'i', 'br', 'a', 'div', 'span',
    ]);
    const ALLOWED_ATTRS = new Set([
      'alert-type', 'color', 'src', 'controls', 'preload', 'type',
      'class', 'style', 'href',
    ]);

    Array.from(node.children).forEach(child => {
      if (child.nodeType === 1) {
        const tagName = child.tagName.toLowerCase();

        // 移除不允許的標籤
        if (!ALLOWED_TAGS.has(tagName)) {
          node.replaceChild(document.createTextNode(child.textContent), child);
          return;
        }

        // 移除不允許的屬性
        Array.from(child.attributes).forEach(attr => {
          if (!ALLOWED_ATTRS.has(attr.name) || attr.name.startsWith('on')) {
            child.removeAttribute(attr.name);
          }
        });

        this._sanitizeContent(child);
      }
    });
  }

  _renderError(message) {
    const div = document.createElement('div');
    div.textContent = message;

    this.shadowRoot.innerHTML = `
      <div style="color: red; padding: 16px;">
        ${div.innerHTML}
      </div>
    `;
  }

  disconnectedCallback() {
    // 移除事件監聽
    const container = this.shadowRoot.querySelector('.notifications-container');
    const fullscreenContainer = this.shadowRoot.querySelector('.fullscreen-container');
    if (container) container.removeEventListener('click', this._handleImageClick);
    if (fullscreenContainer) fullscreenContainer.removeEventListener('click', this._handleFullscreenClick);

    // 移除事件訂閱
    if (this._eventSubscription && typeof this._eventSubscription === 'function') {
      try {
        this._eventSubscription();
      } catch (error) {
        console.error("Error unsubscribing from events:", error);
      }
    }
    this._eventSubscription = null;
  }

  getCardSize() {
    return this.previousNotifications.length || 1;
  }
}

console.info(
  `%c  NOTIFICATIONS-CARD  \n%c   Version:  V2.6.0   `,
  'color: orchid; font-weight: bold; background: dimgray;',
  'color: orange; font-weight: bold; background: white;'
);

customElements.define("notifications-card", NotificationCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "notifications-card",
  name: "Notifications Card",
  description: "A card that displays notifications.",
  preview: false,
});
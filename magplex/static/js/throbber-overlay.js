class ThrobberOverlay extends HTMLElement {
    constructor() {
        super();
        this.messageTitle = null;
        this.messageDescription = null;
        this.renderTimeout = null;
    }

    connectedCallback() {
        this.messageTitle = this.getAttribute('message-title');
        this.messageDescription = this.getAttribute('message-description');
        document.querySelector('body').classList.add('modal-visible');

        // Delay rendering by 0.5s
        this.renderTimeout = setTimeout(() => {
            this.innerHTML = `
                <div class="throbber-container">
                    <img src="/static/assets/icons/throbber.svg" alt="Throbber"/>
                </div>
                <div class="message-container">
                    ${this.messageTitle ? `<h2 class="message-title">${this.messageTitle}</h2>` : ''}
                    ${this.messageDescription ? `<h4 class="message-title">${this.messageDescription}</h4>` : ''}
                </div>
            `;
            this.setAttribute('visible', '');
        }, 250);
    }

    disconnectedCallback() {
        clearTimeout(this.renderTimeout);
    }
}

customElements.define('throbber-overlay', ThrobberOverlay);
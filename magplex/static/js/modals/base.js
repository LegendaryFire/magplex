class Modal extends HTMLElement {
    constructor() {
        super();
    }

    connectedCallback() {
        this.innerHTML = `
            <div class="modal-overlay">
                <div class="modal-container">
                    <nav>
                        <ul>
                            <li class="title">${this.modalTitle}</li>
                            <li class="align-right">
                                <span class="close-btn material-symbols-outlined">close</span>
                            </li>
                        </ul>
                    </nav>
                    ${this.innerHTML}
                </div>
            </div>
        `

        this.querySelector('nav .close-btn').addEventListener('click', () => this.closeModal());
    }

    closeModal() {
        this.remove();
    }
}
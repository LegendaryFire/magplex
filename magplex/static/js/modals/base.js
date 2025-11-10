class Modal extends HTMLElement {
    constructor() {
        super();
    }

    connectedCallback() {
        document.querySelector('body').classList.add('modal-visible');
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

        this.querySelector('nav .close-btn').addEventListener('click', () => {
            document.querySelector('body').classList.remove('modal-visible');
            this.closeModal();
        });
    }

    closeModal() {
        this.remove();
    }
}
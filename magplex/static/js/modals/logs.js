class LogsModal extends Modal {
    async connectedCallback() {
        this.modalTitle = "Logs";
        this.eventSource = null;
        this.buffer = [];
        this.scheduled = false;
        this.maxLines = 1000;
        this.autoScroll = true;

        this.innerHTML = `
            <div class="content-wrapper">
                <div class="content-group">
                    <textarea id="logs" readonly></textarea>
                </div>
            </div>
        `;
        super.connectedCallback();

        const textElem = this.querySelector('#logs');
        textElem.addEventListener('scroll', () => {
            const distanceFromBottom = textElem.scrollHeight - textElem.scrollTop - textElem.clientHeight;
            this.autoScroll = distanceFromBottom < 50;  // Auto scroll when 50px away from bottom.
        });

        this.eventSource = new EventSource("/logs");

        this.eventSource.onmessage = (event) => {
            this.buffer.push(event.data);

            if (!this.scheduled) {
                this.scheduled = true;

                requestAnimationFrame(() => {
                    this.scheduled = false;
                    textElem.value += this.buffer.join("\n") + "\n";
                    this.buffer.length = 0;
                    let lines = textElem.value.split("\n");
                    if (lines.length > this.maxLines) {
                        textElem.value = lines.slice(-this.maxLines).join("\n");
                    }
                    if (this.autoScroll) {
                        textElem.scrollTop = textElem.scrollHeight;
                    }
                });
            }
        };
    }

    disconnectedCallback() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
    }
}
customElements.define('logs-modal', LogsModal);

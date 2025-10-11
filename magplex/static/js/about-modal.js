class AboutModal extends Modal {
    async connectedCallback() {
        const aboutInfo = await this.getInfo();

        this.modalTitle = "About";
        this.innerHTML = `
            <h1>Magplex</h1>
            <h4>by LegendaryFire</h4>
            <p>Version ${aboutInfo.version}</p>
        `
        super.connectedCallback();
    }

    async getInfo() {
        try {
            const response = await fetch('/api/about');
            return await response.json();
        } catch (error) {
            console.log(error);
            return null;
        }
    }
}

customElements.define('about-modal', AboutModal);
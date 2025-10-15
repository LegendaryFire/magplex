class AboutModal extends Modal {
    async connectedCallback() {
        const aboutInfo = await this.getInfo();

        this.modalTitle = "About";
        this.innerHTML = `
            <h1>Magplex</h1>
            <h4>by LegendaryFire</h4>
            <p class="version">Version ${aboutInfo.version}</p>
            <p class="build-date">Build ${aboutInfo.build_date}</p>
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
class ChannelListMode {
    static PLAYER = 'player'
    static FILTER = 'filter'
}

class ChannelList extends HTMLElement {
    constructor() {
        super();
        this.listMode = null;
        this.deviceProfile = null;
        this.genreList = []
        this.channelList = [];
    }

    initializeVariables() {
        this.getGenresUrl = new URL(`/api/devices/${this.deviceProfile.device_uid}/genres`, window.location.origin);
        this.getChannelsUrl = new URL(`/api/devices/${this.deviceProfile.device_uid}/channels`, window.location.origin);

        if (this.listMode === ChannelListMode.PLAYER) {
            this.getGenresUrl.searchParams.set('channel_stale', 'false');
            this.getGenresUrl.searchParams.set('channel_enabled', 'true');
            this.getChannelsUrl.searchParams.set('channel_stale', 'false');
            this.getChannelsUrl.searchParams.set('channel_enabled', 'true');
        } else if (this.listMode === ChannelListMode.FILTER) {
            this.getGenresUrl.searchParams.set('channel_stale', 'false');
            this.getChannelsUrl.searchParams.set('channel_stale', 'false');
        }
    }


    async connectedCallback() {
        this.deviceProfile = await getDeviceProfile();
        if (this.deviceProfile === null) {
            this.renderNotConfigured();
            return;
        }
        this.listMode = this.getAttribute("list-mode");
        this.initializeVariables();

        this.innerHTML = `
            <div class="message-container">
                <h2>Loading Channels</h2>
                <h3>Please wait...</h3>
            </div>
        `
        this.channelList = await this.getChannelList();
        this.genreList = await this.getGenreList();
        const selectMode = this.listMode !== ChannelListMode.PLAYER ? 'select' : '';
        this.innerHTML = `
            <div class="search-container"></div>
            <ul class="channel-list" ${selectMode}></ul>
        `;

        if (this.channelList === null) {
            this.appendChild(this.getConfigureElement());
            return;
        }

        this.renderSearch();
        this.renderSearchGenres();
        this.renderChannelList();
        this.registerChannelListEvents();
    }

    async getGenreList() {
        try {
            const response = await fetch(this.getGenresUrl);
            const genres = await response.json();
            return genres.sort((a, b) => a.genre_number - b.genre_number);
        } catch (error) {
            return null;
        }
    }

    async getChannelList(q=null, genreId=null, enabledOnly=null) {
        try {
            const getChannelsUrl = new URL(this.getChannelsUrl);
            if (q != null) {
                q = q.trim();
                if (q !== "") {
                    getChannelsUrl.searchParams.set("q", q);
                }
            }
            if (genreId != null) {
                genreId = genreId.trim();
                if (genreId !== "") {
                    getChannelsUrl.searchParams.set("genre_id", genreId);
                }
            }
            if (enabledOnly != null) {
                getChannelsUrl.searchParams.set("channel_enabled", enabledOnly);
            }

            const response = await fetch(getChannelsUrl);
            return await response.json();
        } catch (error) {
            return null;
        }
    }

    getConfigureElement() {
        const configureDeviceElem = document.createElement('div');
        configureDeviceElem.classList.add('message-container')
        configureDeviceElem.innerHTML = `
            <h2>Unable to get channel list.</h2>
            <h3>Ensure device is configured in the about page, and try again.</h3>
        `;
        return configureDeviceElem;
    }

    renderSearch() {
        const template = document.createElement('template');
        template.innerHTML = `
            <input id="search-input" type="text" name='search' placeholder='Search...'>
            <select id="genre-select" name='genre'></select>
        `;
        const searchContainerElem = this.querySelector('div.search-container');
        searchContainerElem.appendChild(template.content.cloneNode(true));

        const searchInputElem = searchContainerElem.querySelector('input[name=search]');
        const genreSelectElem = searchContainerElem.querySelector('select[name=genre]');

        const debouncedSearch = debounceFn(this.searchChannelList.bind(this), 300);
        searchInputElem.addEventListener('input', () => {
            debouncedSearch()
        });

        genreSelectElem.addEventListener('change', async () => {
            await this.searchChannelList();
        });

        return searchContainerElem;
    }

    renderSearchGenres() {
        const searchContainerElem = this.querySelector('div.search-container');
        const genreSelectElem = searchContainerElem.querySelector('select[name=genre]');
        genreSelectElem.innerHTML = '';

        const allGenresElem = document.createElement('option');
        allGenresElem.innerText = 'All';
        genreSelectElem.appendChild(allGenresElem);

        if (this.listMode === ChannelListMode.FILTER) {
            const allSelectedElem = document.createElement('option');
            allSelectedElem.value = 'selected';
            allSelectedElem.innerText = 'Selected';
            genreSelectElem.appendChild(allSelectedElem);
        }

        for (const genre of this.genreList) {
            const genreElem = document.createElement('option');
            genreElem.value = genre.genre_id;
            genreElem.textContent = genre.genre_name;
            genreSelectElem.appendChild(genreElem);
        }
    }

    async searchChannelList() {
        const searchElem = this.querySelector('.search-container [name=search]');
        const genreElem = this.querySelector('.search-container [name=genre]');
        const searchValue = searchElem.value;
        const genreValue = genreElem.value !== 'selected' ? genreElem.value : null;
        const enabledOnly =  genreElem.value === 'selected' ? true : null;
        this.channelList = await this.getChannelList(searchValue, genreValue, enabledOnly);
        this.renderChannelList();
    }

    renderChannelList() {
        /** Renders the channels in the channel list container. */
        const channelListContainer = this.querySelector('ul.channel-list');
        channelListContainer.innerHTML = '';

        if (this.listMode === ChannelListMode.PLAYER) {
            for (const channel of this.channelList) {
                this.renderButtonChannel(channelListContainer, channel);
            }
        } else if (this.listMode === ChannelListMode.FILTER) {
           for (const channel of this.channelList) {
                this.renderSelectChannel(channelListContainer, channel);
            }
        }
    }

    registerChannelListEvents() {
        const channelListContainer = this.querySelector('ul.channel-list');
        channelListContainer.addEventListener('click', async (e) => {
            const channelElem = e.target.closest('.channel');
            if (!channelElem) return;
            if (this.listMode === ChannelListMode.FILTER) {
                const channelState = channelElem.hasAttribute('selected');
                channelElem.toggleAttribute('selected', !channelState);
                if (typeof this.channelToggleCallback === 'function') {
                    const channelId = channelElem.dataset.channelId;
                    await this.channelToggleCallback(channelId, !channelState);
                    await this.searchChannelList();
                }
            } else if (this.listMode === ChannelListMode.PLAYER) {
                if (typeof this.channelClickCallback === 'function') {
                    const channelId = channelElem.dataset.channelId;
                    const channelName = channelElem.querySelector('.channel-name').textContent;
                    await this.channelClickCallback(channelId, channelName);
                }
            }
        });
    }

    renderSelectChannel(containerElement, channel) {
        let template = document.createElement('template');
        const genre = this.genreList.find((g) => g.genre_id === channel.genre_id);
        template.innerHTML = `
            <li class="channel" data-channel-id="${channel.channel_id}" ${channel.channel_enabled ? 'selected' : ''}>
                <div class="channel-left">
                    <span class="material-symbols-outlined">live_tv</span>
                </div>
                <div class="channel-details">
                    <span class="channel-name">${channel.channel_name}</span>
                    <span class="channel-group">${genre.genre_name}</span>
                </div>
                <div class="channel-right">
                    <span class="material-symbols-outlined">hd</span>
                    <span class="channel-number">${channel.channel_id}</span>
                </div>
            </li>
        `
        template = template.content.querySelector('.channel');
        containerElement.appendChild(template);
    }

    renderButtonChannel(containerElement, channel) {
        let template = document.createElement('template');
        const genre = this.genreList.find((g) => g.genre_id === channel.genre_id);
        template.innerHTML = `
            <li class="channel" data-channel-id="${channel.channel_id}">
                <div class="channel-left">
                    <span class="material-symbols-outlined">live_tv</span>
                </div>
                <div class="channel-details">
                    <span class="channel-name">${channel.channel_name}</span>
                    <span class="channel-group">${genre.genre_name}</span>
                </div>
                <div class="channel-right">
                    <span class="material-symbols-outlined">hd</span>
                    <span class="channel-number">${channel.channel_id}</span>
                </div>
            </li>
        `
        template = template.content.querySelector('.channel');
        containerElement.appendChild(template);
    }

    renderNotConfigured() {
        let template = document.createElement('template');
        template.innerHTML = `
            <div class="message-container">
                <h2>Device not configured</h2>
                <h4>Configure your device under settings before continuing</h4>
            </div>
        `;
        template = template.content.querySelector('div');
        this.appendChild(template);
    }
}

customElements.define('channel-list', ChannelList);
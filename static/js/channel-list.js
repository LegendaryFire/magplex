class ChannelList extends HTMLElement {
    constructor() {
        super();
        this.channelList = null;
    }

    async connectedCallback() {
        this.innerHTML = `
            <input name="channel-search" placeholder="Search..."/>
            <table class="channel-list">
              <colgroup>
                <col style="width: 80px">
                <col style="width: 65%">
                <col>
              </colgroup>
                <thead>
                    <tr>
                        <th class="channel-number">Number</th>
                        <th>Channel Name</th>
                        <th>Group</th>
                    </tr>
                </thead>
                <tbody></tbody>
            </table>
        `;

        await this.updateChannelList();
        this.renderChannelList();

        const searchElem = this.querySelector('input[name=channel-search]');
        searchElem.addEventListener('keyup', (event) => {
            this.renderChannelList(event.currentTarget.value);
        });
    }

    async updateChannelList() {
        try {
            const response = await fetch('/api/channels/list', {headers: {'Accept': 'application/json'}});
            this.channelList = await response.json();
        } catch (error) {
            this.channelList = null;
            console.log(error);
        }
    }

    renderChannelList(q=null) {
        if (this.channelList === null) {
            console.log("Unable to render channel list. Channel list is null.");
            return;
        }

        // Get the table content and clear it.
        const tableContent = this.querySelector('tbody');
        tableContent.innerHTML = '';

        let filteredChannels = this.channelList;

        // Filter channels if a search query was provided and is valid.
        if (q !== null && typeof(q) === 'string' && q.trim() !== '') {
            q = q.toLowerCase();
            filteredChannels = this.channelList.filter((channel) => {
                return channel.name.toLowerCase().includes(q) || channel.genre.name.toLowerCase().includes(q);
            });
        }

        // Create the row elements and render them to the table.
        for (const channel of filteredChannels) {
            const rowElement = document.createElement('tr');
            rowElement.dataset['streamId'] = channel.stream_id;
            rowElement.dataset['channelName'] = channel.name;
            rowElement.dataset['genre'] = channel.genre.name;
            rowElement.innerHTML = `
                <td class="channel-number">${channel.stream_id}</td>
                <td class="channel-name">${channel.name}</td>
                <td class="genre">${channel.genre.name}</td>
            `;
            tableContent.appendChild(rowElement);
            rowElement.addEventListener('click', () => {
                if (typeof channelClickCallback === 'function') {
                    channelClickCallback(channel.stream_id, channel.name);
                }
            })
        }
    }
}

customElements.define('channel-list', ChannelList);
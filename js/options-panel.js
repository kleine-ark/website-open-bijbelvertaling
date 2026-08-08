/* Open Vertaling — gedrag van het modale optiespaneel. */

const OptionsPanel = {
    dialog: null,
    lastTrigger: null,
    activeTab: 'lezen',
    sessionKey: 'ov_options_tab',

    init() {
        this.dialog = document.getElementById('sidebar-right');
        const openButton = document.getElementById('sidebar-right-open');
        const closeButton = document.getElementById('sidebar-right-toggle');
        if (!this.dialog || !openButton || !closeButton) return;

        openButton.style.display = 'block';
        openButton.setAttribute('aria-controls', 'sidebar-right');
        openButton.setAttribute('aria-expanded', 'false');
        openButton.addEventListener('click', () => this.open(openButton));
        closeButton.addEventListener('click', () => this.close());

        const savedTab = sessionStorage.getItem(this.sessionKey);
        if (['lezen', 'vergelijken', 'onderzoeken'].includes(savedTab)) {
            this.activeTab = savedTab;
        }
        this.activateTab(this.activeTab);

        this.dialog.querySelectorAll('[role="tab"]').forEach(tab => {
            tab.addEventListener('click', () => this.activateTab(tab.dataset.optionsTab));
        });
        this.dialog.querySelector('.options-tabs').addEventListener('keydown', event => {
            this.handleTabKeydown(event);
        });

        this.dialog.addEventListener('click', event => {
            if (event.target !== this.dialog) return;
            const rect = this.dialog.getBoundingClientRect();
            const outside = event.clientX < rect.left || event.clientX > rect.right ||
                event.clientY < rect.top || event.clientY > rect.bottom;
            if (outside) this.close();
        });
        this.dialog.addEventListener('close', () => {
            openButton.setAttribute('aria-expanded', 'false');
            document.body.classList.remove('options-open');
            if (this.lastTrigger && this.lastTrigger.isConnected) this.lastTrigger.focus();
        });
    },

    open(trigger) {
        if (!this.dialog) return;
        this.lastTrigger = trigger || document.activeElement;
        if (window.Sidebar && Sidebar._closeLeft) Sidebar._closeLeft();
        if (!this.dialog.open) this.dialog.showModal();
        document.body.classList.add('options-open');
        const opener = document.getElementById('sidebar-right-open');
        if (opener) opener.setAttribute('aria-expanded', 'true');
        const closeButton = document.getElementById('sidebar-right-toggle');
        if (closeButton) closeButton.focus();
    },

    close() {
        if (this.dialog && this.dialog.open) this.dialog.close();
    },

    activateTab(name, focus = false) {
        if (!['lezen', 'vergelijken', 'onderzoeken'].includes(name)) return;
        this.activeTab = name;
        sessionStorage.setItem(this.sessionKey, name);
        this.dialog.querySelectorAll('[role="tab"]').forEach(tab => {
            const selected = tab.dataset.optionsTab === name;
            tab.setAttribute('aria-selected', selected ? 'true' : 'false');
            tab.tabIndex = selected ? 0 : -1;
            if (selected && focus) tab.focus();
        });
        this.dialog.querySelectorAll('[role="tabpanel"]').forEach(panel => {
            panel.hidden = panel.id !== `options-panel-${name}`;
        });
    },

    handleTabKeydown(event) {
        const tabs = Array.from(this.dialog.querySelectorAll('[role="tab"]'));
        const current = tabs.indexOf(document.activeElement);
        if (current < 0) return;
        let target = null;
        if (event.key === 'ArrowRight') target = (current + 1) % tabs.length;
        if (event.key === 'ArrowLeft') target = (current - 1 + tabs.length) % tabs.length;
        if (event.key === 'Home') target = 0;
        if (event.key === 'End') target = tabs.length - 1;
        if (target === null) return;
        event.preventDefault();
        this.activateTab(tabs[target].dataset.optionsTab, true);
    },
};

window.OptionsPanel = OptionsPanel;
document.addEventListener('DOMContentLoaded', () => OptionsPanel.init());

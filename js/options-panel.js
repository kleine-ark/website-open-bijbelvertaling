/* Open Vertaling — gedrag van het modale optiespaneel. */

const OptionsPanel = {
    dialog: null,
    lastTrigger: null,
    activeTab: 'lezen',
    sessionKey: 'ov_options_tab',
    positionKey: 'ov_options_panel_position',
    dragState: null,

    init() {
        this.dialog = document.getElementById('sidebar-right');
        const openButton = document.getElementById('sidebar-right-open');
        const closeButton = document.getElementById('sidebar-right-toggle');
        if (!this.dialog || !openButton || !closeButton) return;

        openButton.hidden = false;
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
        this.dialog.addEventListener('change', () => this.syncOptionSummaries());

        this.setupDesktopDragging();
        window.addEventListener('resize', () => this.handleViewportChange());

        this.setupZoom();
    },

    open(trigger) {
        if (!this.dialog) return;
        this.lastTrigger = trigger || document.activeElement;
        if (window.Sidebar && Sidebar._closeLeft) Sidebar._closeLeft();
        if (!this.dialog.open) this.dialog.showModal();
        this.restoreDesktopPosition();
        this.syncOptionSummaries();
        document.body.classList.add('options-open');
        const opener = document.getElementById('sidebar-right-open');
        if (opener) opener.setAttribute('aria-expanded', 'true');
        const closeButton = document.getElementById('sidebar-right-toggle');
        if (closeButton) closeButton.focus();
    },

    close() {
        if (this.dialog && this.dialog.open) this.dialog.close();
    },

    isDesktop() {
        return window.matchMedia('(min-width: 769px)').matches;
    },

    setupDesktopDragging() {
        const header = document.getElementById('sidebar-right-header');
        if (!header) return;

        header.addEventListener('pointerdown', event => {
            if (!this.isDesktop() || event.button !== 0) return;
            if (event.target.closest('button, input, select, textarea, a, [role="tab"]')) return;

            const rect = this.dialog.getBoundingClientRect();
            this.dragState = {
                pointerId: event.pointerId,
                offsetX: event.clientX - rect.left,
                offsetY: event.clientY - rect.top,
            };
            this.dialog.classList.add('is-dragging');
            header.setPointerCapture(event.pointerId);
            event.preventDefault();
        });

        header.addEventListener('pointermove', event => {
            if (!this.dragState || event.pointerId !== this.dragState.pointerId) return;
            this.setDesktopPosition(
                event.clientX - this.dragState.offsetX,
                event.clientY - this.dragState.offsetY,
            );
        });

        const finishDrag = event => {
            if (!this.dragState || event.pointerId !== this.dragState.pointerId) return;
            if (header.hasPointerCapture(event.pointerId)) header.releasePointerCapture(event.pointerId);
            this.dragState = null;
            this.dialog.classList.remove('is-dragging');
            this.saveDesktopPosition();
        };
        header.addEventListener('pointerup', finishDrag);
        header.addEventListener('pointercancel', finishDrag);
    },

    clampDesktopPosition(x, y) {
        const rect = this.dialog.getBoundingClientRect();
        const padding = 16;
        const maxX = Math.max(padding, window.innerWidth - rect.width - padding);
        const maxY = Math.max(padding, window.innerHeight - rect.height - padding);
        return {
            x: Math.min(Math.max(x, padding), maxX),
            y: Math.min(Math.max(y, padding), maxY),
        };
    },

    setDesktopPosition(x, y) {
        if (!this.isDesktop()) return;
        this.dialog.classList.add('has-custom-position');
        const position = this.clampDesktopPosition(x, y);
        Object.assign(this.dialog.style, {
            left: `${position.x}px`,
            top: `${position.y}px`,
            right: 'auto',
            bottom: 'auto',
        });
    },

    saveDesktopPosition() {
        if (!this.isDesktop()) return;
        const rect = this.dialog.getBoundingClientRect();
        const position = this.clampDesktopPosition(rect.left, rect.top);
        localStorage.setItem(this.positionKey, JSON.stringify(position));
    },

    readDesktopPosition() {
        try {
            const position = JSON.parse(localStorage.getItem(this.positionKey));
            if (!position || !Number.isFinite(position.x) || !Number.isFinite(position.y)) return null;
            return position;
        } catch (_error) {
            return null;
        }
    },

    restoreDesktopPosition() {
        if (!this.isDesktop()) {
            this.clearInlinePosition();
            return;
        }
        const position = this.readDesktopPosition();
        if (position) this.setDesktopPosition(position.x, position.y);
    },

    clearInlinePosition() {
        this.dialog.classList.remove('has-custom-position');
        this.dialog.style.removeProperty('left');
        this.dialog.style.removeProperty('top');
        this.dialog.style.removeProperty('right');
        this.dialog.style.removeProperty('bottom');
    },

    handleViewportChange() {
        if (!this.dialog || !this.dialog.open) return;
        if (!this.isDesktop()) {
            this.clearInlinePosition();
            return;
        }
        const position = this.readDesktopPosition();
        if (position) this.setDesktopPosition(position.x, position.y);
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

    setupZoom() {
        const bind = () => {
            if (!window.OVZoom || this.dialog.dataset.zoomBound === 'true') return;
            const out = document.getElementById('options-zoom-out');
            const value = document.getElementById('options-zoom-value');
            const input = document.getElementById('options-zoom-in');
            if (!out || !value || !input) return;
            this.dialog.dataset.zoomBound = 'true';
            out.addEventListener('click', () => OVZoom.step(-1));
            input.addEventListener('click', () => OVZoom.step(1));
            value.addEventListener('click', () => OVZoom.reset());
            OVZoom.subscribe(zoom => {
                value.textContent = `${Math.round(zoom * 100)}%`;
            });
        };
        bind();
        window.addEventListener('ovzoomready', bind, { once: true });
    },

    syncOptionSummaries() {
        if (!this.dialog) return;
        this.dialog.querySelectorAll('[data-option-summary]').forEach(group => {
            const option = group.dataset.optionSummary;
            const checked = group.querySelector(`[data-optie="${option}"]:checked`);
            const current = group.querySelector('.option-current');
            if (!checked || !current) return;
            const label = checked.closest('label');
            current.textContent = label ? label.textContent.trim() : checked.value;
        });
    },
};

window.OptionsPanel = OptionsPanel;
document.addEventListener('DOMContentLoaded', () => OptionsPanel.init());

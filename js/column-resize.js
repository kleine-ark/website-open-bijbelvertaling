/* Open Vertaling — Kolombreedte aanpassen door slepen */

const ColumnResize = {
    isResizing: false,
    currentCol: null,
    startX: 0,
    startWidth: 0,
    customWidths: {},

    init() {
        this.loadWidths();
        this.addResizeHandles();
        this.applyWidths();
    },

    loadWidths() {
        const saved = localStorage.getItem('sv2026_columnWidths');
        if (saved) {
            try {
                this.customWidths = JSON.parse(saved);
            } catch(e) {}
        }
    },

    saveWidths() {
        localStorage.setItem('sv2026_columnWidths', JSON.stringify(this.customWidths));
    },

    addResizeHandles() {
        const headerRow = document.querySelector('.column-headers');
        if (!headerRow) return;

        headerRow.querySelectorAll('[data-col]').forEach(header => {
            if (header.dataset.col === 'num') return;
            if (header.querySelector('.col-resize-handle')) return;

            header.style.position = 'relative';

            const handle = document.createElement('div');
            handle.className = 'col-resize-handle';
            handle.addEventListener('mousedown', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.startResize(e, header.dataset.col, header);
            });
            header.appendChild(handle);
        });
    },

    startResize(e, col, headerEl) {
        this.isResizing = true;
        this.currentCol = col;
        this.startX = e.clientX;
        this.startWidth = headerEl.getBoundingClientRect().width;

        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none';

        const onMove = (e) => {
            if (!this.isResizing) return;
            const diff = e.clientX - this.startX;
            const newWidth = Math.max(60, this.startWidth + diff);
            this.customWidths[this.currentCol] = newWidth + 'px';
            this.applyWidths();
        };

        const onUp = () => {
            this.isResizing = false;
            this.currentCol = null;
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
            document.removeEventListener('mousemove', onMove);
            document.removeEventListener('mouseup', onUp);
            this.saveWidths();
        };

        document.addEventListener('mousemove', onMove);
        document.addEventListener('mouseup', onUp);
    },

    applyWidths() {
        // Overschrijf App.COL_WIDTHS met custom waarden
        const parts = ['40px'];
        App.ALL_COLS.forEach(col => {
            const cb = document.querySelector(`[data-toggle-col="${col}"]`);
            if (cb && cb.checked) {
                parts.push(this.customWidths[col] || App.COL_WIDTHS[col] || '1fr');
            }
        });
        const template = parts.join(' ');

        const headers = document.querySelector('.column-headers');
        if (headers) headers.style.gridTemplateColumns = template;

        document.querySelectorAll('.verse-row').forEach(row => {
            row.style.gridTemplateColumns = template;
        });
    },

    // Dubbel-klik op handle: reset naar standaard
    resetColumn(col) {
        delete this.customWidths[col];
        this.saveWidths();
        this.applyWidths();
    }
};

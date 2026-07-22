/* Open Vertaling — Kolom drag-and-drop herordening */

const ColumnReorder = {
    draggedCol: null,
    savedOrder: null,

    init() {
        this.loadOrder();
        this.applyOrder();
        this.makeHeadersDraggable();
    },

    loadOrder() {
        const saved = localStorage.getItem('sv2026_columnOrder');
        if (saved) {
            try {
                this.savedOrder = JSON.parse(saved);
            } catch (e) {
                this.savedOrder = null;
            }
        }
    },

    saveOrder() {
        localStorage.setItem('sv2026_columnOrder', JSON.stringify(App.ALL_COLS));
    },

    applyOrder() {
        if (!this.savedOrder) return;

        // Alleen kolommen die nog bestaan meenemen, nieuwe kolommen aan het eind
        const existing = new Set(App.ALL_COLS);
        const newOrder = [];
        this.savedOrder.forEach(col => {
            if (existing.has(col)) newOrder.push(col);
        });
        // Voeg eventuele nieuwe kolommen toe die niet in de opgeslagen volgorde staan
        App.ALL_COLS.forEach(col => {
            if (!newOrder.includes(col)) newOrder.push(col);
        });

        App.ALL_COLS.length = 0;
        newOrder.forEach(col => App.ALL_COLS.push(col));
    },

    makeHeadersDraggable() {
        const headerRow = document.querySelector('.column-headers');
        if (!headerRow) return;

        // Maak elke kolomheader (behalve num) draggable
        headerRow.querySelectorAll('[data-col]').forEach(header => {
            if (header.dataset.col === 'num') return;

            header.draggable = true;
            header.style.cursor = 'grab';

            header.addEventListener('dragstart', (e) => {
                this.draggedCol = header.dataset.col;
                header.style.opacity = '0.4';
                e.dataTransfer.effectAllowed = 'move';
                e.dataTransfer.setData('text/plain', header.dataset.col);
            });

            header.addEventListener('dragend', () => {
                header.style.opacity = '1';
                this.draggedCol = null;
                // Verwijder alle drop-indicators
                headerRow.querySelectorAll('[data-col]').forEach(h => {
                    h.classList.remove('drag-over-left', 'drag-over-right');
                });
            });

            header.addEventListener('dragover', (e) => {
                e.preventDefault();
                e.dataTransfer.dropEffect = 'move';

                if (header.dataset.col === this.draggedCol) return;

                // Bepaal of we links of rechts droppen
                const rect = header.getBoundingClientRect();
                const midX = rect.left + rect.width / 2;
                const isLeft = e.clientX < midX;

                header.classList.toggle('drag-over-left', isLeft);
                header.classList.toggle('drag-over-right', !isLeft);
            });

            header.addEventListener('dragleave', () => {
                header.classList.remove('drag-over-left', 'drag-over-right');
            });

            header.addEventListener('drop', (e) => {
                e.preventDefault();
                header.classList.remove('drag-over-left', 'drag-over-right');

                const fromCol = e.dataTransfer.getData('text/plain');
                const toCol = header.dataset.col;
                if (fromCol === toCol) return;

                // Bepaal positie
                const rect = header.getBoundingClientRect();
                const midX = rect.left + rect.width / 2;
                const insertBefore = e.clientX < midX;

                // Herorden App.ALL_COLS
                const fromIdx = App.ALL_COLS.indexOf(fromCol);
                if (fromIdx === -1) return;

                // Verwijder uit oude positie
                App.ALL_COLS.splice(fromIdx, 1);

                // Voeg in op nieuwe positie
                let toIdx = App.ALL_COLS.indexOf(toCol);
                if (!insertBefore) toIdx++;
                App.ALL_COLS.splice(toIdx, 0, fromCol);

                // Sla op en pas toe
                this.saveOrder();
                this.reorderDOM();
                App.updateGrid();
            });
        });
    },

    reorderDOM() {
        const headerRow = document.querySelector('.column-headers');
        if (!headerRow) return;

        // Herorden kolomheaders
        const numHeader = headerRow.querySelector('[data-col="num"]');
        const headers = {};
        headerRow.querySelectorAll('[data-col]').forEach(h => {
            headers[h.dataset.col] = h;
        });

        // Leeg de header row en voeg in juiste volgorde toe
        while (headerRow.firstChild) headerRow.removeChild(headerRow.firstChild);
        headerRow.appendChild(numHeader);
        App.ALL_COLS.forEach(col => {
            if (headers[col]) headerRow.appendChild(headers[col]);
        });

        // Herorden elke verse-row
        document.querySelectorAll('.verse-row').forEach(row => {
            const numCell = row.querySelector('[data-col="num"]');
            const cells = {};
            row.querySelectorAll('[data-col]').forEach(c => {
                cells[c.dataset.col] = c;
            });

            while (row.firstChild) row.removeChild(row.firstChild);
            row.appendChild(numCell);
            App.ALL_COLS.forEach(col => {
                if (cells[col]) row.appendChild(cells[col]);
            });
        });

        // Maak nieuwe headers ook draggable
        this.makeHeadersDraggable();
    },

    // Herorden ook de column-toggles checkboxes in dezelfde volgorde
    reorderToggles() {
        const container = document.getElementById('column-toggles');
        if (!container) return;

        const labels = {};
        container.querySelectorAll('label').forEach(l => {
            const cb = l.querySelector('input[data-toggle-col]');
            if (cb) labels[cb.dataset.toggleCol] = l;
        });

        while (container.firstChild) container.removeChild(container.firstChild);
        App.ALL_COLS.forEach(col => {
            if (labels[col]) container.appendChild(labels[col]);
        });
    }
};

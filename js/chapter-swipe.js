/* Horizontaal vegen in de leestekst: hoofdstuk vooruit/terug. */
(function () {
    'use strict';

    const MIN_HORIZONTAL_DISTANCE = 88;
    const HORIZONTAL_DOMINANCE = 1.5;
    const MAX_GESTURE_DURATION = 750;
    const INTERACTIVE_SELECTOR = [
        'a', 'button', 'input', 'select', 'textarea', 'label', 'summary',
        '[contenteditable="true"]', '[role="button"]', '[data-swipe-ignore]'
    ].join(',');

    let gesture = null;

    function isInteractive(target) {
        return target instanceof Element && Boolean(target.closest(INTERACTIVE_SELECTOR));
    }

    function hasTextSelection() {
        const selection = window.getSelection();
        return Boolean(selection && selection.type === 'Range' && selection.toString().trim());
    }

    function resetGesture() {
        gesture = null;
    }

    function initialise() {
        const readingArea = document.getElementById('verses-container');
        if (!readingArea || readingArea.dataset.chapterSwipeBound === 'true') return;
        readingArea.dataset.chapterSwipeBound = 'true';

        readingArea.addEventListener('touchstart', event => {
            if (event.touches.length !== 1 || isInteractive(event.target)) {
                resetGesture();
                return;
            }
            const touch = event.touches[0];
            gesture = {
                x: touch.clientX,
                y: touch.clientY,
                startedAt: Date.now(),
            };
        }, { passive: true });

        readingArea.addEventListener('touchcancel', resetGesture, { passive: true });

        readingArea.addEventListener('touchend', event => {
            if (!gesture || event.changedTouches.length !== 1 || isInteractive(event.target)) {
                resetGesture();
                return;
            }

            const touch = event.changedTouches[0];
            const deltaX = touch.clientX - gesture.x;
            const deltaY = touch.clientY - gesture.y;
            const duration = Date.now() - gesture.startedAt;
            resetGesture();

            if (
                hasTextSelection() ||
                duration > MAX_GESTURE_DURATION ||
                Math.abs(deltaX) < MIN_HORIZONTAL_DISTANCE ||
                Math.abs(deltaX) < Math.abs(deltaY) * HORIZONTAL_DOMINANCE
            ) return;

            if (typeof Navigation !== 'undefined' && typeof Navigation.navigateRelative === 'function') {
                // Naar links is vooruit; naar rechts is terug.
                Navigation.navigateRelative(deltaX < 0 ? 1 : -1);
            }
        }, { passive: true });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initialise, { once: true });
    } else {
        initialise();
    }
}());

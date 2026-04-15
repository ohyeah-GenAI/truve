'use strict';

class MouseTracker {
    constructor() {
        this._events    = [];
        this._startTime = null;
        this._lastMove  = 0;
        this._element   = null;
        this._handlers  = null;
        this.THROTTLE   = 16; // ms
    }

    start(element) {
        this.stop();
        this._events    = [];
        this._startTime = Date.now();
        this._element   = element;

        const onMove  = (e) => {
            const now = Date.now();
            if (now - this._lastMove < this.THROTTLE) return;
            this._lastMove = now;
            this._record('mousemove', e);
        };
        const onDown  = (e) => this._record('mousedown', e);
        const onUp    = (e) => this._record('mouseup',   e);
        const onClick = (e) => this._record('click',     e);

        element.addEventListener('mousemove', onMove);
        element.addEventListener('mousedown', onDown);
        element.addEventListener('mouseup',   onUp);
        element.addEventListener('click',     onClick);

        this._handlers = { onMove, onDown, onUp, onClick };
    }

    stop() {
        if (!this._element || !this._handlers) return;
        const { onMove, onDown, onUp, onClick } = this._handlers;
        this._element.removeEventListener('mousemove', onMove);
        this._element.removeEventListener('mousedown', onDown);
        this._element.removeEventListener('mouseup',   onUp);
        this._element.removeEventListener('click',     onClick);
        this._element  = null;
        this._handlers = null;
    }

    getEvents()    { return this._events; }
    getStartTime() { return this._startTime; }

    _record(type, e) {
        const rect = this._element.getBoundingClientRect();
        this._events.push({
            type,
            x:         Math.round(e.clientX - rect.left),
            y:         Math.round(e.clientY - rect.top),
            timestamp: Date.now(),
            button:    e.button ?? 0,
        });
    }
}

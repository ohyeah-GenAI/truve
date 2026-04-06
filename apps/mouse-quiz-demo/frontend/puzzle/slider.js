'use strict';

/**
 * SliderPuzzle
 * 배경 이미지의 회색 빈칸 위치까지 조각을 드래그해 맞추는 퍼즐.
 *
 * render(container, config, tracker) - 퍼즐 렌더링 및 트래킹 시작
 * getAnswer()                        - { offset_x: number } 반환
 */
const SliderPuzzle = (() => {
    let _currentX = 0;  // 현재 조각의 x 오프셋 (px)
    let _maxX     = 0;  // 드래그 가능 최대 x

    function render(container, config, tracker) {
        const { background, piece, piece_width, image_width, image_height } = config;

        _currentX = 0;
        _maxX     = image_width - piece_width;

        // ── Wrapper ─────────────────────────────────────────────
        const wrapper = document.createElement('div');
        wrapper.className = 'slider-wrapper';
        wrapper.style.cssText = `width:${image_width}px;`;

        // ── 배경 이미지 ─────────────────────────────────────────
        const bgImg = document.createElement('img');
        bgImg.className = 'slider-bg-img';
        bgImg.src = 'data:image/png;base64,' + background;
        bgImg.style.cssText = `width:${image_width}px; height:${image_height}px;`;
        wrapper.appendChild(bgImg);

        // ── 드래그 조각 (배경 위에 오버레이) ────────────────────
        const pieceImg = document.createElement('img');
        pieceImg.className = 'slider-piece-overlay';
        pieceImg.src = 'data:image/png;base64,' + piece;
        pieceImg.style.cssText = `width:${piece_width}px; height:${image_height}px;`;
        wrapper.appendChild(pieceImg);

        // ── 트랙 바 ─────────────────────────────────────────────
        const track = document.createElement('div');
        track.className = 'slider-track-bar';
        track.style.width = image_width + 'px';

        const knob = document.createElement('div');
        knob.className = 'slider-knob';
        knob.textContent = '→';
        knob.style.width = piece_width + 'px';
        track.appendChild(knob);
        wrapper.appendChild(track);

        container.appendChild(wrapper);

        // ── 드래그 로직 ─────────────────────────────────────────
        let dragging    = false;
        let startClient = 0;
        let startX      = 0;

        function setX(x) {
            _currentX = Math.max(0, Math.min(Math.round(x), _maxX));
            pieceImg.style.left = _currentX + 'px';
            knob.style.left     = _currentX + 'px';
            // 트랙 채우기 진행률
            const pct = ((_currentX / _maxX) * 100).toFixed(1);
            track.style.background =
                `linear-gradient(to right, #4361ee ${pct}%, #e0e4ea ${pct}%)`;
        }

        function dragStart(e) {
            dragging    = true;
            startClient = e.touches ? e.touches[0].clientX : e.clientX;
            startX      = _currentX;
            e.preventDefault();
        }
        function dragMove(e) {
            if (!dragging) return;
            const cx = e.touches ? e.touches[0].clientX : e.clientX;
            setX(startX + (cx - startClient));
        }
        function dragEnd() { dragging = false; }

        // 마우스
        knob.addEventListener('mousedown',    dragStart);
        pieceImg.addEventListener('mousedown', dragStart);
        document.addEventListener('mousemove', dragMove);
        document.addEventListener('mouseup',   dragEnd);

        // 터치
        knob.addEventListener('touchstart',    dragStart, { passive: false });
        pieceImg.addEventListener('touchstart', dragStart, { passive: false });
        document.addEventListener('touchmove',  dragMove,  { passive: false });
        document.addEventListener('touchend',   dragEnd);

        tracker.start(wrapper);
    }

    function getAnswer() {
        return { offset_x: _currentX };
    }

    return { render, getAnswer };
})();
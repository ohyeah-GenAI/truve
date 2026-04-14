'use strict';

/**
 * PathTracePuzzleV2
 * v2: 백엔드에서 체크포인트 5개만 전달 (pathtrace_v2 타입) — 점이 적어 부담 없음.
 * 렌더링 로직은 pathtrace.js와 동일, export 이름만 PathTracePuzzleV2로 변경.
 */
const PathTracePuzzleV2 = (() => {
    let _points = [];

    function render(container, config, tracker) {
        const { width, height, path_points, checkpoints, stroke_width } = config;
        _points = [];

        const wrapper = document.createElement('div');
        wrapper.className = 'pathtrace-wrapper';
        wrapper.style.cssText = `width:${width}px;`;

        const canvas = document.createElement('canvas');
        canvas.className = 'pathtrace-canvas';
        canvas.width = width;
        canvas.height = height;
        wrapper.appendChild(canvas);

        const caption = document.createElement('div');
        caption.className = 'pathtrace-caption';
        caption.textContent = '🟢 시작점에서 🔴 끝점까지 경로를 따라 그려주세요.';
        wrapper.appendChild(caption);

        container.appendChild(wrapper);

        const ctx = canvas.getContext('2d');
        drawGuide(ctx, path_points, checkpoints, stroke_width);

        let drawing = false;

        function getPos(evt) {
            const rect = canvas.getBoundingClientRect();
            const src = evt.touches ? evt.touches[0] : evt;
            return {
                x: Math.round(src.clientX - rect.left),
                y: Math.round(src.clientY - rect.top),
            };
        }

        function beginDraw(evt) {
            drawing = true;
            const p = getPos(evt);
            _points.push(p);
            drawDot(ctx, p);
            evt.preventDefault();
        }

        function moveDraw(evt) {
            if (!drawing) return;
            const p = getPos(evt);
            const prev = _points[_points.length - 1];
            _points.push(p);
            drawStroke(ctx, prev, p);
            evt.preventDefault();
        }

        function endDraw() { drawing = false; }

        canvas.addEventListener('mousedown', beginDraw);
        canvas.addEventListener('mousemove', moveDraw);
        document.addEventListener('mouseup', endDraw);
        canvas.addEventListener('touchstart', beginDraw, { passive: false });
        canvas.addEventListener('touchmove', moveDraw, { passive: false });
        document.addEventListener('touchend', endDraw);

        tracker.start(canvas);
    }

    function drawGuide(ctx, pathPoints, checkpoints, strokeWidth) {
        ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);

        // 기준 경로
        ctx.lineJoin = 'round';
        ctx.lineCap = 'round';
        ctx.strokeStyle = '#d8dee9';
        ctx.lineWidth = strokeWidth;
        ctx.beginPath();
        pathPoints.forEach((p, idx) => {
            if (idx === 0) ctx.moveTo(p.x, p.y);
            else ctx.lineTo(p.x, p.y);
        });
        ctx.stroke();

        // 체크포인트 점 (5개)
        checkpoints.forEach((cp, idx) => {
            const isStart = idx === 0;
            const isEnd = idx === checkpoints.length - 1;
            const color = isStart ? '#2ec4b6' : isEnd ? '#e63946' : '#4361ee';
            const r = (isStart || isEnd) ? 7 : 5;

            ctx.beginPath();
            ctx.fillStyle = color;
            ctx.arc(cp.x, cp.y, r, 0, Math.PI * 2);
            ctx.fill();

            ctx.beginPath();
            ctx.strokeStyle = '#fff';
            ctx.lineWidth = 2;
            ctx.arc(cp.x, cp.y, r, 0, Math.PI * 2);
            ctx.stroke();
        });
    }

    function drawDot(ctx, p) {
        ctx.beginPath();
        ctx.fillStyle = '#4361ee';
        ctx.arc(p.x, p.y, 3, 0, Math.PI * 2);
        ctx.fill();
    }

    function drawStroke(ctx, from, to) {
        ctx.beginPath();
        ctx.strokeStyle = '#4361ee';
        ctx.lineWidth = 6;
        ctx.lineCap = 'round';
        ctx.moveTo(from.x, from.y);
        ctx.lineTo(to.x, to.y);
        ctx.stroke();
    }

    function getAnswer() {
        return { points: _points.slice(0, 800) };
    }

    return { render, getAnswer };
})();
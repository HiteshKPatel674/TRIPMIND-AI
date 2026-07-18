/**
 * cursor.js — TripMind Premium Custom Cursor
 * Soft glowing cursor with trailing motion. Desktop only.
 * Respects prefers-reduced-motion.
 */
(function () {
    'use strict';

    // Skip on touch devices and reduced-motion preference
    if ('ontouchstart' in window || navigator.maxTouchPoints > 0) return;
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    const cursor = document.createElement('div');
    cursor.className = 'tm-cursor';
    cursor.innerHTML = '<div class="tm-cursor-dot"></div><div class="tm-cursor-ring"></div>';
    document.body.appendChild(cursor);

    const cursorLabel = document.createElement('div');
    cursorLabel.className = 'tm-cursor-label';
    document.body.appendChild(cursorLabel);

    let mouseX = 0, mouseY = 0;
    let cursorX = 0, cursorY = 0;

    document.addEventListener('mousemove', (e) => {
        mouseX = e.clientX;
        mouseY = e.clientY;
    });

    function animate() {
        // Smooth trailing motion
        cursorX += (mouseX - cursorX) * 0.15;
        cursorY += (mouseY - cursorY) * 0.15;

        cursor.style.transform = `translate(${cursorX}px, ${cursorY}px)`;
        cursorLabel.style.transform = `translate(${mouseX + 20}px, ${mouseY + 20}px)`;

        requestAnimationFrame(animate);
    }
    animate();

    // Interactive element detection
    const interactiveSelectors = [
        { selector: 'a, button, .btn, [role="button"]', label: '' },
        { selector: '.hotel-book-btn, .btn-book', label: 'Book' },
        { selector: '.ac-action-map, .hotel-map-btn', label: 'Map' },
        { selector: '.hero-btn', label: 'Explore' },
        { selector: '.subnav-link, .sidebar-nav-item', label: 'Navigate' },
        { selector: '.gallery-card', label: 'View' },
        { selector: '.hotel-card', label: 'Details' },
    ];

    document.addEventListener('mouseover', (e) => {
        let matched = false;
        for (let i = interactiveSelectors.length - 1; i >= 0; i--) {
            const {selector, label} = interactiveSelectors[i];
            if (e.target.closest(selector)) {
                cursor.classList.add('tm-cursor-hover');
                if (label) {
                    cursorLabel.textContent = label;
                    cursorLabel.classList.add('tm-cursor-label-visible');
                }
                matched = true;
                break;
            }
        }
        if (!matched) {
            cursor.classList.remove('tm-cursor-hover');
            cursorLabel.classList.remove('tm-cursor-label-visible');
        }
    });

    // Inject cursor styles
    const style = document.createElement('style');
    style.textContent = `
        .tm-cursor {
            position: fixed;
            top: -10px;
            left: -10px;
            pointer-events: none;
            z-index: 99999;
            mix-blend-mode: screen;
        }
        .tm-cursor-dot {
            width: 6px;
            height: 6px;
            background: rgba(99, 179, 237, 0.9);
            border-radius: 50%;
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            transition: transform 0.15s ease, background 0.2s ease;
        }
        .tm-cursor-ring {
            width: 32px;
            height: 32px;
            border: 1.5px solid rgba(99, 179, 237, 0.3);
            border-radius: 50%;
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            transition: width 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94),
                        height 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94),
                        border-color 0.2s ease,
                        box-shadow 0.3s ease;
            box-shadow: 0 0 10px rgba(99, 179, 237, 0.08);
        }
        .tm-cursor-hover .tm-cursor-dot {
            transform: translate(-50%, -50%) scale(2);
            background: rgba(99, 179, 237, 1);
        }
        .tm-cursor-hover .tm-cursor-ring {
            width: 48px;
            height: 48px;
            border-color: rgba(99, 179, 237, 0.5);
            box-shadow: 0 0 20px rgba(99, 179, 237, 0.2);
        }
        .tm-cursor-label {
            position: fixed;
            top: 0;
            left: 0;
            pointer-events: none;
            z-index: 99998;
            font-size: 0.7rem;
            font-weight: 600;
            color: rgba(99, 179, 237, 0.9);
            letter-spacing: 0.5px;
            text-transform: uppercase;
            opacity: 0;
            transition: opacity 0.2s ease;
            font-family: 'Inter', sans-serif;
        }
        .tm-cursor-label-visible {
            opacity: 1;
        }
        /* Hide default cursor on interactive elements when custom cursor is active */
        body:has(.tm-cursor) * {
            cursor: none !important;
        }
    `;
    document.head.appendChild(style);
})();

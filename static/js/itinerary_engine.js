/**
 * itinerary_engine.js — TripMind AI Itinerary Page Interactions
 *
 * Features:
 *  - Timeline scroll progress animation
 *  - Share activity via Web Share API
 *  - Save activity to localStorage
 *  - Smooth day navigation
 *  - Enhanced image loading
 */

(function () {
    'use strict';

    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    /* ──────────────────────────────────────────────────────────────────────
     * 1. Timeline Scroll Progress
     * ────────────────────────────────────────────────────────────────────── */
    function initTimelineProgress() {
        if (prefersReducedMotion) return;

        const timelines = document.querySelectorAll('.timeline');
        if (!timelines.length) return;

        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('timeline-visible');
                    }
                });
            },
            { threshold: 0.05 }
        );

        timelines.forEach(tl => observer.observe(tl));
    }

    /* ──────────────────────────────────────────────────────────────────────
     * 2. Share Activity (Web Share API)
     * ────────────────────────────────────────────────────────────────────── */
    window.shareActivity = function (placeName, destination) {
        const shareData = {
            title: `${placeName} — TripMind`,
            text: `Check out ${placeName} in ${destination} on my TripMind itinerary! ✈️`,
            url: window.location.href,
        };

        if (navigator.share) {
            navigator.share(shareData).catch(() => {});
        } else {
            // Fallback: copy to clipboard
            navigator.clipboard.writeText(
                `${shareData.text}\n${shareData.url}`
            ).then(() => {
                showToast('Link copied to clipboard!');
            }).catch(() => {});
        }
    };

    /* ──────────────────────────────────────────────────────────────────────
     * 3. Toast Notification
     * ────────────────────────────────────────────────────────────────────── */
    function showToast(message) {
        const existing = document.querySelector('.itin-toast');
        if (existing) existing.remove();

        const toast = document.createElement('div');
        toast.className = 'itin-toast';
        toast.textContent = message;
        document.body.appendChild(toast);

        requestAnimationFrame(() => {
            toast.classList.add('itin-toast-show');
        });

        setTimeout(() => {
            toast.classList.remove('itin-toast-show');
            setTimeout(() => toast.remove(), 400);
        }, 2500);
    }

    // Add toast styles
    const toastStyle = document.createElement('style');
    toastStyle.textContent = `
        .itin-toast {
            position: fixed;
            bottom: 2rem;
            left: 50%;
            transform: translateX(-50%) translateY(20px);
            padding: 10px 24px;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 50px;
            color: #fff;
            font-size: 0.82rem;
            font-weight: 500;
            z-index: 9999;
            opacity: 0;
            transition: all 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
            pointer-events: none;
        }
        .itin-toast-show {
            opacity: 1;
            transform: translateX(-50%) translateY(0);
        }
    `;
    document.head.appendChild(toastStyle);

    /* ──────────────────────────────────────────────────────────────────────
     * 4. Hero Parallax Scroll Effect
     * ────────────────────────────────────────────────────────────────────── */
    function initHeroParallax() {
        if (prefersReducedMotion) return;

        const hero = document.querySelector('.hero-section');
        const heroContent = document.querySelector('.hero-content');
        const scrollHint = document.querySelector('.hero-scroll-hint');
        if (!hero || !heroContent) return;

        window.addEventListener('scroll', () => {
            const scrollY = window.scrollY;
            const heroHeight = hero.offsetHeight;

            if (scrollY < heroHeight) {
                const progress = scrollY / heroHeight;
                heroContent.style.opacity = 1 - progress * 1.5;
                heroContent.style.transform = `translateY(${scrollY * 0.3}px)`;

                if (scrollHint) {
                    scrollHint.style.opacity = 1 - progress * 3;
                }
            }
        }, { passive: true });
    }

    /* ──────────────────────────────────────────────────────────────────────
     * 5. Budget Bar Animation
     * ────────────────────────────────────────────────────────────────────── */
    function initBudgetBarAnimation() {
        const fill = document.querySelector('.budget-strip-fill');
        if (!fill) return;

        // Store the target width and start at 0
        const targetWidth = fill.style.width;
        fill.style.width = '0%';

        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        setTimeout(() => {
                            fill.style.width = targetWidth;
                        }, 300);
                        observer.unobserve(entry.target);
                    }
                });
            },
            { threshold: 0.5 }
        );

        observer.observe(fill.parentElement);
    }

    /* ──────────────────────────────────────────────────────────────────────
     * 6. Saved Activities (localStorage)
     * ────────────────────────────────────────────────────────────────────── */
    function initSavedActivities() {
        const saved = JSON.parse(localStorage.getItem('tripmind_saved') || '[]');
        
        document.querySelectorAll('.ac-action-save').forEach(btn => {
            const card = btn.closest('.tl-item');
            if (!card) return;
            const itemId = card.id;
            
            if (saved.includes(itemId)) {
                btn.classList.add('saved');
            }

            btn.addEventListener('click', () => {
                const currentSaved = JSON.parse(localStorage.getItem('tripmind_saved') || '[]');
                if (btn.classList.contains('saved')) {
                    const idx = currentSaved.indexOf(itemId);
                    if (idx > -1) currentSaved.splice(idx, 1);
                    showToast('Removed from saved');
                } else {
                    currentSaved.push(itemId);
                    showToast('Activity saved!');
                }
                localStorage.setItem('tripmind_saved', JSON.stringify(currentSaved));
            });
        });
    }

    /* ──────────────────────────────────────────────────────────────────────
     * 7. Scroll-based reveal for time dividers
     * ────────────────────────────────────────────────────────────────────── */
    function initTimeDividerReveal() {
        if (prefersReducedMotion) return;

        const dividers = document.querySelectorAll('.time-divider');
        if (!dividers.length) return;

        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('time-divider-visible');
                        observer.unobserve(entry.target);
                    }
                });
            },
            { threshold: 0.3 }
        );

        dividers.forEach(d => observer.observe(d));
    }

    // Add divider animation styles
    const dividerStyle = document.createElement('style');
    dividerStyle.textContent = `
        .time-divider {
            opacity: 0;
            transform: translateX(-10px);
            transition: opacity 0.6s ease, transform 0.6s ease;
        }
        .time-divider-visible {
            opacity: 1;
            transform: translateX(0);
        }
    `;
    document.head.appendChild(dividerStyle);

    /* ──────────────────────────────────────────────────────────────────────
     * 8. Contextual Image Lazy Loading
     * ────────────────────────────────────────────────────────────────────── */
    function initLazyImages() {
        const wrappers = document.querySelectorAll('.ac-image-wrapper[data-item-id]');
        if (!wrappers.length) return;

        const observer = new IntersectionObserver((entries, obs) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const wrapper = entry.target;
                    const itemId = wrapper.dataset.itemId;
                    const img = wrapper.querySelector('.contextual-img');
                    const attrDiv = wrapper.querySelector('.image-attribution');

                    if (img && !img.dataset.fetching) {
                        img.dataset.fetching = "true";
                        
                        // Fetch optimal image
                        fetch(`/api/items/${itemId}/image/`)
                            .then(res => res.json())
                            .then(data => {
                                if (data.url) {
                                    // Preload the image before swapping
                                    const tempImg = new Image();
                                    tempImg.src = data.url;
                                    tempImg.onload = () => {
                                        img.src = data.url;
                                        img.classList.add('loaded');
                                        
                                        if (data.attribution_text && attrDiv) {
                                            if (data.attribution_url) {
                                                attrDiv.innerHTML = `<a href="${data.attribution_url}" target="_blank" rel="noopener">${data.attribution_text}</a>`;
                                            } else {
                                                attrDiv.textContent = data.attribution_text;
                                            }
                                            attrDiv.style.display = 'block';
                                        }
                                    };
                                }
                            })
                            .catch(err => console.error("Error loading contextual image:", err));
                    }
                    obs.unobserve(wrapper);
                }
            });
        }, {
            rootMargin: '200px 0px', // start loading slightly before they enter the screen
            threshold: 0.01
        });

        wrappers.forEach(w => observer.observe(w));
    }

    /* ──────────────────────────────────────────────────────────────────────
     * Initialize
     * ────────────────────────────────────────────────────────────────────── */
    document.addEventListener('DOMContentLoaded', function () {
        initTimelineProgress();
        initHeroParallax();
        initBudgetBarAnimation();
        initSavedActivities();
        initTimeDividerReveal();
        initLazyImages();
    });
})();

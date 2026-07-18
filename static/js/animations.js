/**
 * animations.js — TripMind AI Global Animation Engine
 *
 * Features:
 *  - Intersection Observer scroll-triggered reveals
 *  - Ken Burns image cycling for hero backgrounds
 *  - Navbar transparency on scroll
 *  - Counter animation for stats
 *  - Reduced-motion support
 */

(function () {
    'use strict';

    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    /* ──────────────────────────────────────────────────────────────────────
     * 1. Scroll-triggered reveal animations
     * ────────────────────────────────────────────────────────────────────── */
    function initRevealAnimations() {
        const revealElements = document.querySelectorAll('.reveal');
        if (!revealElements.length) return;

        if (prefersReducedMotion) {
            revealElements.forEach(el => el.classList.add('revealed'));
            return;
        }

        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        const delay = entry.target.dataset.revealDelay || 0;
                        setTimeout(() => {
                            entry.target.classList.add('revealed');
                        }, parseInt(delay));
                        observer.unobserve(entry.target);
                    }
                });
            },
            { threshold: 0.12, rootMargin: '0px 0px -40px 0px' }
        );

        revealElements.forEach(el => observer.observe(el));
    }

    /* ──────────────────────────────────────────────────────────────────────
     * 2. Ken Burns hero image cycling
     * ────────────────────────────────────────────────────────────────────── */
    function initKenBurns() {
        const container = document.querySelector('.hero-ken-burns');
        if (!container) return;

        const slides = container.querySelectorAll('.kb-slide');
        if (slides.length < 2) return;

        let current = 0;
        const interval = 6000; // ms per slide

        function cycle() {
            const prev = current;
            current = (current + 1) % slides.length;

            slides[prev].classList.remove('kb-active');
            slides[prev].classList.add('kb-exit');

            slides[current].classList.add('kb-active');
            slides[current].classList.remove('kb-exit');

            // Clean exit class after transition
            setTimeout(() => {
                slides[prev].classList.remove('kb-exit');
            }, 1500);
        }

        // Start the first slide
        slides[0].classList.add('kb-active');

        if (!prefersReducedMotion) {
            setInterval(cycle, interval);
        }
    }

    /* ──────────────────────────────────────────────────────────────────────
     * 3. Navbar scroll effect
     * ────────────────────────────────────────────────────────────────────── */
    function initNavbarScroll() {
        const navbar = document.querySelector('.navbar');
        if (!navbar) return;

        // Check if this is a page with a dark hero (landing page)
        const isLandingPage = document.querySelector('.landing-page') !== null;

        function updateNavbar() {
            const scrolled = window.scrollY > 60;
            navbar.classList.toggle('navbar-scrolled', scrolled);

            if (isLandingPage) {
                navbar.classList.toggle('navbar-transparent', !scrolled);
            }
        }

        if (isLandingPage) {
            navbar.classList.add('navbar-transparent');
        }

        window.addEventListener('scroll', updateNavbar, { passive: true });
        updateNavbar();
    }

    /* ──────────────────────────────────────────────────────────────────────
     * 4. Counter animation
     * ────────────────────────────────────────────────────────────────────── */
    function initCounters() {
        const counters = document.querySelectorAll('[data-counter]');
        if (!counters.length) return;

        if (prefersReducedMotion) {
            counters.forEach(el => {
                el.textContent = el.dataset.counter;
            });
            return;
        }

        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        animateCounter(entry.target);
                        observer.unobserve(entry.target);
                    }
                });
            },
            { threshold: 0.5 }
        );

        counters.forEach(el => observer.observe(el));
    }

    function animateCounter(el) {
        const target = parseInt(el.dataset.counter, 10);
        const suffix = el.dataset.counterSuffix || '';
        const prefix = el.dataset.counterPrefix || '';
        const duration = 1800;
        const startTime = performance.now();

        function update(now) {
            const elapsed = now - startTime;
            const progress = Math.min(elapsed / duration, 1);
            // Ease out cubic
            const eased = 1 - Math.pow(1 - progress, 3);
            const current = Math.floor(eased * target);
            el.textContent = prefix + current.toLocaleString('en-IN') + suffix;

            if (progress < 1) {
                requestAnimationFrame(update);
            } else {
                el.textContent = prefix + target.toLocaleString('en-IN') + suffix;
            }
        }

        requestAnimationFrame(update);
    }

    /* ──────────────────────────────────────────────────────────────────────
     * 5. Smooth scroll for anchor links
     * ────────────────────────────────────────────────────────────────────── */
    function initSmoothScroll() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                const targetId = this.getAttribute('href');
                if (targetId === '#') return;
                const target = document.querySelector(targetId);
                if (target) {
                    e.preventDefault();
                    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            });
        });
    }

    /* ──────────────────────────────────────────────────────────────────────
     * 6. Stagger children animation
     * ────────────────────────────────────────────────────────────────────── */
    function initStaggerChildren() {
        const groups = document.querySelectorAll('[data-stagger]');
        if (!groups.length) return;

        if (prefersReducedMotion) {
            groups.forEach(g => {
                g.querySelectorAll('.stagger-child').forEach(c => c.classList.add('revealed'));
            });
            return;
        }

        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        const children = entry.target.querySelectorAll('.stagger-child');
                        const delay = parseInt(entry.target.dataset.stagger) || 100;
                        children.forEach((child, i) => {
                            setTimeout(() => {
                                child.classList.add('revealed');
                            }, i * delay);
                        });
                        observer.unobserve(entry.target);
                    }
                });
            },
            { threshold: 0.1 }
        );

        groups.forEach(g => observer.observe(g));
    }

    /* ──────────────────────────────────────────────────────────────────────
     * 7. Parallax effect (subtle)
     * ────────────────────────────────────────────────────────────────────── */
    function initParallax() {
        if (prefersReducedMotion) return;

        const parallaxElements = document.querySelectorAll('[data-parallax]');
        if (!parallaxElements.length) return;

        window.addEventListener('scroll', () => {
            const scrollY = window.scrollY;
            parallaxElements.forEach(el => {
                const speed = parseFloat(el.dataset.parallax) || 0.3;
                const rect = el.getBoundingClientRect();
                const offset = (rect.top + scrollY) * speed;
                el.style.transform = `translateY(${scrollY * speed - offset}px)`;
            });
        }, { passive: true });
    }

    /* ──────────────────────────────────────────────────────────────────────
     * Initialize everything on DOM ready
     * ────────────────────────────────────────────────────────────────────── */
    document.addEventListener('DOMContentLoaded', function () {
        initRevealAnimations();
        initKenBurns();
        initNavbarScroll();
        initCounters();
        initSmoothScroll();
        initStaggerChildren();
        initParallax();
    });
})();

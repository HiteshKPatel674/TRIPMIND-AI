/**
 * day_navigation.js — TripMind Day-by-Day Navigation
 * Hash-based routing for day panels with sidebar navigation.
 */
(function () {
    'use strict';

    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    function init() {
        const sidebar = document.getElementById('itin-sidebar');
        const dayPanels = document.querySelectorAll('.day-panel');
        const navItems = document.querySelectorAll('.sidebar-nav-item[data-target]');
        const prevBtns = document.querySelectorAll('.day-prev-btn');
        const nextBtns = document.querySelectorAll('.day-next-btn');

        if (!sidebar || !dayPanels.length) return;

        const panelIds = Array.from(dayPanels).map(p => p.id);

        // ── Show/hide panels ─────────────────────────────────
        function showPanel(targetId) {
            const transitionDuration = prefersReducedMotion ? 0 : 300;

            dayPanels.forEach(panel => {
                if (panel.id === targetId) {
                    panel.classList.add('day-panel-active');
                    panel.style.display = 'block';

                    if (!prefersReducedMotion) {
                        panel.style.opacity = '0';
                        panel.style.transform = 'translateX(12px)';
                        requestAnimationFrame(() => {
                            panel.style.transition = `opacity ${transitionDuration}ms ease, transform ${transitionDuration}ms ease`;
                            panel.style.opacity = '1';
                            panel.style.transform = 'translateX(0)';
                        });
                    }
                } else {
                    panel.classList.remove('day-panel-active');
                    panel.style.display = 'none';
                }
            });

            // Update active nav item
            navItems.forEach(item => {
                item.classList.toggle('active', item.dataset.target === targetId);
            });

            // Scroll sidebar active item into view
            const activeNav = sidebar.querySelector('.sidebar-nav-item.active');
            if (activeNav) {
                activeNav.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
            }

            // Update URL hash without scrolling
            if (targetId) {
                history.replaceState(null, '', '#' + targetId);
            }

            // Re-trigger reveal animations in the newly visible panel
            const panel = document.getElementById(targetId);
            if (panel) {
                const reveals = panel.querySelectorAll('.reveal:not(.revealed)');
                reveals.forEach((el, i) => {
                    setTimeout(() => el.classList.add('revealed'), i * 80);
                });

                const staggerGroups = panel.querySelectorAll('[data-stagger]');
                staggerGroups.forEach(group => {
                    const children = group.querySelectorAll('.stagger-child:not(.revealed)');
                    const delay = parseInt(group.dataset.stagger) || 100;
                    children.forEach((child, i) => {
                        setTimeout(() => child.classList.add('revealed'), i * delay);
                    });
                });
            }
        }

        // ── Click handlers ───────────────────────────────────
        navItems.forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const targetId = item.dataset.target;
                showPanel(targetId);
            });
        });

        // Prev/Next buttons
        prevBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const currentPanel = document.querySelector('.day-panel-active');
                if (!currentPanel) return;
                const currentIdx = panelIds.indexOf(currentPanel.id);
                if (currentIdx > 0) {
                    showPanel(panelIds[currentIdx - 1]);
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                }
            });
        });

        nextBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const currentPanel = document.querySelector('.day-panel-active');
                if (!currentPanel) return;
                const currentIdx = panelIds.indexOf(currentPanel.id);
                if (currentIdx < panelIds.length - 1) {
                    showPanel(panelIds[currentIdx + 1]);
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                }
            });
        });

        // ── Keyboard navigation ──────────────────────────────
        document.addEventListener('keydown', (e) => {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

            const currentPanel = document.querySelector('.day-panel-active');
            if (!currentPanel) return;
            const currentIdx = panelIds.indexOf(currentPanel.id);

            if (e.key === 'ArrowLeft' && currentIdx > 0) {
                e.preventDefault();
                showPanel(panelIds[currentIdx - 1]);
            } else if (e.key === 'ArrowRight' && currentIdx < panelIds.length - 1) {
                e.preventDefault();
                showPanel(panelIds[currentIdx + 1]);
            }
        });

        // ── Handle hash on load ──────────────────────────────
        const hash = window.location.hash.replace('#', '');
        if (hash && panelIds.includes(hash)) {
            showPanel(hash);
        } else if (panelIds.length > 0) {
            showPanel(panelIds[0]);
        }

        // ── Mobile sidebar toggle ────────────────────────────
        const sidebarToggle = document.getElementById('sidebar-toggle');
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', () => {
                sidebar.classList.toggle('sidebar-open');
            });

            // Close sidebar on nav item click (mobile)
            navItems.forEach(item => {
                item.addEventListener('click', () => {
                    if (window.innerWidth < 1024) {
                        sidebar.classList.remove('sidebar-open');
                    }
                });
            });
        }

        // ── Scroll progress indicator ────────────────────────
        const progressBar = document.getElementById('scroll-progress');
        if (progressBar) {
            window.addEventListener('scroll', () => {
                const scrollTop = window.scrollY;
                const docHeight = document.documentElement.scrollHeight - window.innerHeight;
                const progress = docHeight > 0 ? (scrollTop / docHeight) * 100 : 0;
                progressBar.style.width = progress + '%';
            }, { passive: true });
        }
    }

    document.addEventListener('DOMContentLoaded', init);
})();

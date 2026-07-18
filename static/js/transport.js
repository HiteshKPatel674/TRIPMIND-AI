/**
 * transport.js — TripMind AI Smart Booking Engine
 * Renders premium hotel cards, flight/train/bus listings with animations.
 */

function renderTransport(tripId) {
    const loadingEl = document.getElementById('transport-loading');
    const containerEl = document.getElementById('transport-container');

    // Animate loading steps
    const steps = loadingEl.querySelectorAll('.ai-thinking-step');
    steps.forEach((step, i) => {
        setTimeout(() => step.classList.add('step-active'), i * 800);
    });

    fetch(`/api/trips/${tripId}/transport/`)
        .then(res => res.json())
        .then(data => {
            loadingEl.style.display = 'none';
            containerEl.style.display = 'block';
            containerEl.classList.add('fade-in-up');

            const trans = data.transport;
            const hotels = data.hotels;

            // ── Top Recommendations ──────────────────────────────────
            if (trans && (trans.best_flight || trans.best_train)) {
                let html = `
                <div class="top-reco-card reveal">
                    <div class="top-reco-header">
                        <i class="bi bi-stars"></i>
                        <strong>Smart Transport Recommendations</strong>
                    </div>
                    <div class="top-reco-body"><div class="row">`;

                if (trans.best_flight) {
                    html += `
                    <div class="col-md-6 mb-3">
                        <div class="reco-option reco-flight">
                            <span class="reco-badge reco-badge-best">Best Flight</span>
                            <h5><i class="bi bi-airplane text-primary me-1"></i> ${trans.best_flight.airline}</h5>
                            <p class="reco-route">${trans.best_flight.departure_time} → ${trans.best_flight.arrival_time} (${trans.best_flight.duration_str})</p>
                            <h4 class="reco-price">₹${Number(trans.best_flight.price).toLocaleString('en-IN')}</h4>
                            ${trans.best_flight.recommendation_reason ? `<p class="reco-reason"><i class="bi bi-lightbulb"></i> ${trans.best_flight.recommendation_reason}</p>` : ''}
                            <a href="${trans.best_flight.book_url}" target="_blank" rel="noopener" class="btn-book btn-book-flight">
                                <i class="bi bi-airplane"></i> Book Flight
                            </a>
                        </div>
                    </div>`;
                }
                if (trans.best_train) {
                    let cHtml = '';
                    if (trans.best_train.classes) {
                        trans.best_train.classes.forEach(c => {
                            cHtml += `<span class="class-badge">${c.name} ₹${Number(c.price).toLocaleString('en-IN')}</span>`;
                        });
                    }

                    html += `
                    <div class="col-md-6 mb-3">
                        <div class="reco-option reco-train">
                            <span class="reco-badge reco-badge-ai">⭐ AI Recommended</span>
                            <div class="reco-train-header">
                                <div>
                                    <h5><i class="bi bi-train-front me-1"></i> ${trans.best_train.name} <small>(${trans.best_train.number || 'N/A'})</small></h5>
                                    <span class="train-type-badge">${trans.best_train.train_type || 'EXP'}</span>
                                    <span class="train-stops-badge">${trans.best_train.stops || 0} Stops</span>
                                </div>
                                <h4 class="reco-price">₹${Number(trans.best_train.cheapest_price).toLocaleString('en-IN')}</h4>
                            </div>

                            <div class="reco-train-schedule">
                                <div class="schedule-point">
                                    <div class="schedule-time">${trans.best_train.departure_time}</div>
                                    <div class="schedule-code">${trans.best_train.source_station_code || ''}</div>
                                </div>
                                <div class="schedule-arrow">
                                    <div class="schedule-duration">${trans.best_train.duration_str}</div>
                                    <div class="schedule-line"></div>
                                </div>
                                <div class="schedule-point">
                                    <div class="schedule-time">${trans.best_train.arrival_time}</div>
                                    <div class="schedule-code">${trans.best_train.dest_station_code || ''}</div>
                                </div>
                            </div>

                            <div class="class-badges-row">${cHtml}</div>

                            ${trans.best_train.recommendation_reason ? `<p class="reco-reason"><i class="bi bi-lightbulb"></i> ${trans.best_train.recommendation_reason}</p>` : ''}

                            <div class="reco-actions">
                                <a href="${trans.best_train.book_url}" target="_blank" rel="noopener" class="btn-book btn-book-train">Book on Ixigo</a>
                                <a href="https://www.irctc.co.in/nget/train-search" target="_blank" rel="noopener" class="btn-book btn-book-secondary">IRCTC</a>
                            </div>
                        </div>
                    </div>`;
                }
                html += `</div></div></div>`;
                document.getElementById('top-recommendations-container').innerHTML = html;
            }

            // ── Hotel Cards (Premium Design) ─────────────────────────
            renderHotels(hotels);

            // ── Flights ──────────────────────────────────────────────
            renderFlights(trans);

            // ── Trains ───────────────────────────────────────────────
            renderTrains(trans);

            // ── Buses ────────────────────────────────────────────────
            renderBuses(trans);
        })
        .catch(err => {
            console.error('Error fetching transport:', err);
            loadingEl.innerHTML = `
                <div class="booking-error">
                    <i class="bi bi-wifi-off"></i>
                    <h4>Unable to load recommendations</h4>
                    <p>Please check your connection and try refreshing the page.</p>
                    <button class="btn-book btn-book-flight" onclick="renderTransport('${tripId}')">
                        <i class="bi bi-arrow-clockwise"></i> Retry
                    </button>
                </div>`;
        });
}

// ── Hotel Cards ──────────────────────────────────────────────────────────
function renderHotels(hotels) {
    const container = document.getElementById('all-hotels-container');
    if (!hotels || hotels.length === 0) {
        container.innerHTML = `
            <div class="booking-empty">
                <i class="bi bi-building"></i>
                <p>No hotels found for this destination. Try adjusting your dates.</p>
            </div>`;
        return;
    }

    let html = '';
    hotels.forEach((h, idx) => {
        const stars = Array.from({length: 5}, (_, i) =>
            i < h.stars
                ? '<i class="bi bi-star-fill"></i>'
                : '<i class="bi bi-star"></i>'
        ).join('');

        const amenities = (h.amenities || []).map(a =>
            `<span class="hotel-amenity"><i class="bi bi-check-circle-fill"></i> ${a}</span>`
        ).join('');

        const priceFormatted = typeof h.price_per_night === 'number'
            ? '₹' + h.price_per_night.toLocaleString('en-IN')
            : h.price_per_night;

        html += `
        <div class="col-lg-4 col-md-6 mb-4">
            <div class="hotel-card stagger-child" style="animation-delay: ${idx * 100}ms" id="hotel-card-${idx}">
                <div class="hotel-card-image">
                    <img src="${h.image_placeholder}"
                         alt="${h.name}"
                         loading="lazy"
                         onerror="this.src='https://image.pollinations.ai/prompt/${encodeURIComponent('Luxury hotel exterior ' + h.name)}?width=600&height=400&nologo=true'">
                    <div class="hotel-card-overlay"></div>
                    <div class="hotel-stars-badge">${stars}</div>
                    ${h.recommendation_reason ? `<div class="hotel-reco-badge"><i class="bi bi-award-fill"></i> ${h.recommendation_reason}</div>` : ''}
                </div>
                <div class="hotel-card-body">
                    <div class="hotel-card-header">
                        <h5 class="hotel-name">${h.name}</h5>
                        <div class="hotel-rating">
                            <i class="bi bi-star-fill"></i>
                            <span>${h.rating}</span>
                            <small>(${h.reviews} reviews)</small>
                        </div>
                    </div>
                    <div class="hotel-amenities">${amenities}</div>
                    <div class="hotel-card-footer">
                        <div class="hotel-price">
                            <span class="hotel-price-amount">${priceFormatted}</span>
                            <span class="hotel-price-label">/night</span>
                        </div>
                        <div class="hotel-actions">
                            ${h.maps_url ? `<a href="${h.maps_url}" target="_blank" rel="noopener" class="hotel-action-btn hotel-map-btn" title="View on Map"><i class="bi bi-geo-alt"></i></a>` : ''}
                            <a href="${h.book_url}" target="_blank" rel="noopener" class="hotel-action-btn hotel-book-btn" id="hotel-book-${idx}">
                                <i class="bi bi-arrow-up-right"></i> Book
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>`;
    });

    container.innerHTML = html;
}

// ── Flights ──────────────────────────────────────────────────────────────
function renderFlights(trans) {
    const container = document.getElementById('all-flights-container');
    if (!trans || !trans.flights || trans.flights.length === 0) {
        container.innerHTML = `
            <div class="booking-empty">
                <i class="bi bi-airplane"></i>
                <p>No flights found. Try checking flight aggregators for more options.</p>
            </div>`;
        return;
    }

    let html = '<div class="transport-list">';
    trans.flights.forEach((f, idx) => {
        html += `
        <div class="transport-item stagger-child" style="animation-delay: ${idx * 80}ms">
            <div class="transport-item-main">
                <div class="transport-provider">
                    <strong>${f.airline}</strong>
                    <small>${f.id}</small>
                </div>
                <div class="transport-schedule">
                    <span class="transport-time">${f.departure_time}</span>
                    <div class="transport-route-line">
                        <span class="transport-duration">${f.duration_str}</span>
                        <div class="route-line-bar"></div>
                        <span class="transport-stops">${f.stops || 'Non-stop'}</span>
                    </div>
                    <span class="transport-time">${f.arrival_time}</span>
                </div>
                <div class="transport-price">₹${Number(f.price).toLocaleString('en-IN')}</div>
                <a href="${f.book_url}" target="_blank" rel="noopener" class="btn-book btn-book-sm">Book</a>
            </div>
        </div>`;
    });
    html += '</div>';
    container.innerHTML = html;
}

// ── Trains ───────────────────────────────────────────────────────────────
function renderTrains(trans) {
    const container = document.getElementById('all-trains-container');
    if (!trans || !trans.trains || trans.trains.length === 0) {
        container.innerHTML = `
            <div class="booking-empty">
                <i class="bi bi-train-front"></i>
                <p>No trains found for this route.</p>
            </div>`;
        return;
    }

    let html = '<div class="row g-3">';
    trans.trains.forEach((t, idx) => {
        let badges = '';
        if (trans.best_train && t.id === trans.best_train.id) {
            badges += '<span class="train-badge train-badge-ai">⭐ AI Pick</span>';
        }
        if (t.duration_hours < 8) badges += '<span class="train-badge train-badge-fast">⚡ Fast</span>';
        if (t.cheapest_price < 1000) badges += '<span class="train-badge train-badge-cheap">💰 Budget</span>';

        let cHtml = '';
        if (t.classes && t.classes.length > 0) {
            t.classes.forEach(c => {
                cHtml += `<span class="class-badge">${c.name}: ₹${Number(c.price).toLocaleString('en-IN')}</span>`;
            });
        }

        html += `
        <div class="col-md-6 mb-3">
            <div class="train-card stagger-child" style="animation-delay: ${idx * 80}ms">
                <div class="train-badges">${badges}</div>
                <div class="train-header">
                    <div>
                        <h6 class="train-name">${t.name} <small>(${t.number || t.id})</small></h6>
                        <span class="train-type">${t.train_type || 'Express'} · ${t.days_of_running || 'Daily'}</span>
                    </div>
                    <div class="train-price">₹${Number(t.cheapest_price || 0).toLocaleString('en-IN')}</div>
                </div>

                <div class="train-schedule">
                    <div class="schedule-point">
                        <div class="schedule-time">${t.departure_time || 'N/A'}</div>
                        <div class="schedule-code">${t.source_station_code || 'SRC'}</div>
                        <div class="schedule-station">${t.source_station_name || ''}</div>
                    </div>
                    <div class="schedule-arrow">
                        <div class="schedule-duration">${t.duration_str || 'N/A'}</div>
                        <div class="schedule-line"></div>
                        <div class="schedule-stops">${t.stops != null ? t.stops + ' Stops' : 'Direct'}</div>
                    </div>
                    <div class="schedule-point">
                        <div class="schedule-time">${t.arrival_time || 'N/A'}</div>
                        <div class="schedule-code">${t.dest_station_code || 'DST'}</div>
                        <div class="schedule-station">${t.dest_station_name || ''}</div>
                    </div>
                </div>

                <div class="class-badges-row">${cHtml}</div>

                <div class="train-footer">
                    <div class="train-meta">
                        <span><i class="bi bi-calendar"></i> ${t.departure_date}</span>
                        <span class="${t.availability && t.availability.includes('WL') ? 'avail-wl' : 'avail-ok'}">
                            <i class="bi bi-ticket-detailed"></i> ${t.availability || 'Check'}
                        </span>
                    </div>
                    <div class="train-actions">
                        <a href="${t.book_url || '#'}" target="_blank" rel="noopener" class="btn-book btn-book-train-sm">Ixigo</a>
                        <a href="https://www.irctc.co.in/nget/train-search" target="_blank" rel="noopener" class="btn-book btn-book-secondary-sm">IRCTC</a>
                    </div>
                </div>
            </div>
        </div>`;
    });
    html += '</div>';
    container.innerHTML = html;
}

// ── Buses ────────────────────────────────────────────────────────────────
function renderBuses(trans) {
    const container = document.getElementById('all-buses-container');
    if (!trans || !trans.buses || trans.buses.length === 0) {
        container.innerHTML = `
            <div class="booking-empty">
                <i class="bi bi-bus-front"></i>
                <p>No buses found for this route.</p>
            </div>`;
        return;
    }

    let html = '<div class="transport-list">';
    trans.buses.forEach((b, idx) => {
        html += `
        <div class="transport-item stagger-child" style="animation-delay: ${idx * 80}ms">
            <div class="transport-item-main">
                <div class="transport-provider">
                    <strong>${b.operator}</strong>
                    <small>${b.type}</small>
                </div>
                <div class="transport-schedule">
                    <span class="transport-time">${b.departure_time}</span>
                    <div class="transport-route-line">
                        <span class="transport-duration">${b.duration_str}</span>
                        <div class="route-line-bar"></div>
                    </div>
                    <span class="transport-time">${b.arrival_time}</span>
                </div>
                <div class="transport-price">₹${Number(b.price).toLocaleString('en-IN')}</div>
                <a href="${b.book_url}" target="_blank" rel="noopener" class="btn-book btn-book-sm">Book</a>
            </div>
        </div>`;
    });
    html += '</div>';
    container.innerHTML = html;
}

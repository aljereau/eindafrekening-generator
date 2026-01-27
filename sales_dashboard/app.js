let allProperties = [];
let allOwners = [];
let allTenants = [];
let allRelaties = [];
let currentSort = { column: null, asc: true };

document.addEventListener('DOMContentLoaded', init);

function init() {
    if (typeof SALES_DATA === 'undefined') {
        document.getElementById('lastUpdate').textContent = 'Fout: data.js niet gevonden';
        return;
    }

    allProperties = SALES_DATA.properties;
    allRelaties = SALES_DATA.relaties || [];
    buildOwnersList();
    buildTenantsList();

    // Update header
    const genDate = new Date(SALES_DATA.generated);
    document.getElementById('lastUpdate').textContent =
        `Data: ${genDate.toLocaleDateString('nl-NL')} ${genDate.toLocaleTimeString('nl-NL', { hour: '2-digit', minute: '2-digit' })}`;

    // Update KPIs
    document.getElementById('kpiTotal').textContent = SALES_DATA.stats.total;
    document.getElementById('kpiAvailable').textContent = SALES_DATA.stats.available;
    document.getElementById('kpiRented').textContent = SALES_DATA.stats.rented;
    document.getElementById('kpiLeegstand').textContent = SALES_DATA.stats.leegstand || 0;
    document.getElementById('kpiMarge').textContent = formatMoney(SALES_DATA.stats.total_marge_maand);
    document.getElementById('kpiMargeJaar').textContent = formatMoney(SALES_DATA.stats.total_marge_jaar);

    // Populate city filter
    const cities = [...new Set(allProperties.map(p => p.plaats).filter(Boolean))].sort();
    const citySelect = document.getElementById('filterStad');
    cities.forEach(c => {
        const opt = document.createElement('option');
        opt.value = c; opt.textContent = c;
        citySelect.appendChild(opt);
    });

    // Initial renders
    renderWoningen();
    renderBinnenkort();
    renderEigenaren();
    renderHuurders();
    renderFinancieel();

    // Setup tabs
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', function () {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
            this.classList.add('active');
            document.getElementById('panel-' + this.dataset.tab).classList.add('active');
        });
    });

    // Filters
    document.getElementById('searchWoningen').addEventListener('input', renderWoningen);
    document.getElementById('filterStatus').addEventListener('change', renderWoningen);
    document.getElementById('filterStad').addEventListener('change', renderWoningen);
    document.getElementById('searchBinnenkort').addEventListener('input', renderBinnenkort);
    document.getElementById('filterBinnenkortDays').addEventListener('change', renderBinnenkort);
    document.getElementById('searchEigenaren').addEventListener('input', renderEigenaren);
    document.getElementById('searchHuurders').addEventListener('input', renderHuurders);
    document.getElementById('searchFinancieel').addEventListener('input', renderFinancieel);
    document.getElementById('filterFinStatus').addEventListener('change', renderFinancieel);
    document.getElementById('sortFinancieel').addEventListener('change', renderFinancieel);

    // Overlay close
    document.getElementById('overlay').addEventListener('click', closePanel);
    document.addEventListener('keydown', e => { if (e.key === 'Escape') closePanel(); });
}

function formatMoney(amount) {
    if (amount == null || isNaN(amount)) return '-';
    return '€ ' + Math.round(amount).toLocaleString('nl-NL');
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function buildOwnersList() {
    const map = {};
    allProperties.forEach(p => {
        if (!p.eigenaar_naam) return;
        if (!map[p.eigenaar_naam]) {
            map[p.eigenaar_naam] = {
                naam: p.eigenaar_naam,
                email: p.eigenaar_email,
                telefoon: p.eigenaar_telefoon,
                adres: p.eigenaar_adres,
                postcode: p.eigenaar_postcode,
                plaats: p.eigenaar_plaats,
                iban: p.eigenaar_iban,
                properties: [],
                totalInhuur: 0
            };
        }
        map[p.eigenaar_naam].properties.push(p);
        map[p.eigenaar_naam].totalInhuur += (p.inhuur_totaal_excl_btw || 0);
    });
    allOwners = Object.values(map).sort((a, b) => b.properties.length - a.properties.length);
}

function buildTenantsList() {
    const map = {};
    allProperties.forEach(p => {
        if (!p.huurder_naam) return;
        if (!map[p.huurder_naam]) {
            map[p.huurder_naam] = {
                naam: p.huurder_naam,
                type: p.huurder_type,
                email: p.huurder_email,
                telefoon: p.huurder_telefoon,
                adres: p.huurder_adres,
                plaats: p.huurder_plaats,
                properties: [],
                totalVerhuur: 0
            };
        }
        map[p.huurder_naam].properties.push(p);
        map[p.huurder_naam].totalVerhuur += (p.verhuur_totaal_excl_btw || 0);
    });
    allTenants = Object.values(map).sort((a, b) => b.properties.length - a.properties.length);
}

function getStatusBadge(status) {
    const cls = status === 'Beschikbaar' ? 'available' :
        status === 'Leegstand' ? 'leegstand' : 'rented';
    return `<span class="status-badge ${cls}">${status || '-'}</span>`;
}

function getMoneyClass(val) {
    if (val == null) return 'money';
    return val >= 0 ? 'money positive' : 'money negative';
}

// ========== WONINGEN ==========
function renderWoningen() {
    const search = document.getElementById('searchWoningen').value.toLowerCase();
    const statusFilter = document.getElementById('filterStatus').value;
    const stadFilter = document.getElementById('filterStad').value;

    let filtered = allProperties.filter(p => {
        const matchSearch = !search ||
            (p.adres || '').toLowerCase().includes(search) ||
            (p.plaats || '').toLowerCase().includes(search) ||
            (p.eigenaar_naam || '').toLowerCase().includes(search) ||
            (p.huurder_naam || '').toLowerCase().includes(search) ||
            (p.object_id || '').toLowerCase().includes(search);
        const matchStatus = !statusFilter || (p.beschikbaarheid_status || '').includes(statusFilter);
        const matchStad = !stadFilter || p.plaats === stadFilter;
        return matchSearch && matchStatus && matchStad;
    });

    document.getElementById('resultsCount').textContent = `${filtered.length} woningen`;

    const tbody = document.querySelector('#woningenTable tbody');
    tbody.innerHTML = filtered.map(p => `
        <tr onclick="showPropertyDetail('${p.object_id}')">
            <td>${p.object_id}</td>
            <td>${p.adres || '-'}</td>
            <td>${p.plaats || '-'}</td>
            <td>${p.eigenaar_naam || '-'}</td>
            <td>${p.huurder_naam || '-'}</td>
            <td class="${getMoneyClass(p.marge_maand_excl_btw)}">${formatMoney(p.marge_maand_excl_btw)}</td>
            <td>${getStatusBadge(p.beschikbaarheid_status)}</td>
        </tr>
    `).join('');
}

// ========== BINNENKORT BESCHIKBAAR ==========
function renderBinnenkort() {
    const maxDays = parseInt(document.getElementById('filterBinnenkortDays').value) || 90;
    const search = document.getElementById('searchBinnenkort').value.toLowerCase();
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    // Filter properties with verhuur_eind in the future and within maxDays
    let filtered = allProperties.filter(p => {
        if (!p.verhuur_eind) return false;
        const endDate = new Date(p.verhuur_eind);
        if (isNaN(endDate.getTime())) return false;
        const daysUntil = Math.ceil((endDate - today) / (1000 * 60 * 60 * 24));
        if (daysUntil < 0 || daysUntil > maxDays) return false;

        const matchSearch = !search ||
            (p.adres || '').toLowerCase().includes(search) ||
            (p.plaats || '').toLowerCase().includes(search) ||
            (p.huurder_naam || '').toLowerCase().includes(search) ||
            (p.object_id || '').toLowerCase().includes(search);
        return matchSearch;
    });

    // Sort by days until expiry (most urgent first)
    filtered.sort((a, b) => {
        const daysA = Math.ceil((new Date(a.verhuur_eind) - today) / (1000 * 60 * 60 * 24));
        const daysB = Math.ceil((new Date(b.verhuur_eind) - today) / (1000 * 60 * 60 * 24));
        return daysA - daysB;
    });

    document.getElementById('binnenkortCount').textContent = `${filtered.length} woningen binnenkort beschikbaar`;

    const tbody = document.querySelector('#binnenkortTable tbody');
    tbody.innerHTML = filtered.map(p => {
        const endDate = new Date(p.verhuur_eind);
        const daysUntil = Math.ceil((endDate - today) / (1000 * 60 * 60 * 24));

        // Color code the days badge
        let daysBadgeClass = '';
        if (daysUntil <= 14) daysBadgeClass = 'badge-danger';
        else if (daysUntil <= 30) daysBadgeClass = 'badge-warning';
        else daysBadgeClass = 'badge-info';

        const formattedDate = endDate.toLocaleDateString('nl-NL', { day: '2-digit', month: 'short', year: 'numeric' });

        return `
            <tr onclick="showPropertyDetail('${p.object_id}')" style="cursor:pointer;">
                <td>${p.object_id}</td>
                <td>${p.adres || '-'}</td>
                <td>${p.plaats || '-'}</td>
                <td>${p.huurder_naam || '-'}</td>
                <td>${formattedDate}</td>
                <td><span class="status-badge ${daysBadgeClass}">${daysUntil}d</span></td>
                <td class="${getMoneyClass(p.marge_maand_excl_btw)}">${formatMoney(p.marge_maand_excl_btw)}</td>
                <td>${getStatusBadge(p.beschikbaarheid_status)}</td>
            </tr>
        `;
    }).join('');
}

// ========== EIGENAREN ==========
function renderEigenaren() {
    const search = document.getElementById('searchEigenaren').value.toLowerCase();
    let filtered = allOwners.filter(o => !search || o.naam.toLowerCase().includes(search));

    document.getElementById('eigenarenCount').textContent = `${filtered.length} eigenaren`;

    const tbody = document.querySelector('#eigenarenTable tbody');
    tbody.innerHTML = filtered.map((o, idx) => `
        <tr data-owner-idx="${idx}" style="cursor:pointer">
            <td><strong>${escapeHtml(o.naam)}</strong></td>
            <td>${escapeHtml(o.email || '-')}</td>
            <td>${escapeHtml(o.telefoon || '-')}</td>
            <td>${escapeHtml(o.plaats || '-')}</td>
            <td>${o.properties.length}</td>
            <td class="money">${formatMoney(o.totalInhuur)}/m</td>
        </tr>
    `).join('');

    // Add click handlers
    tbody.querySelectorAll('tr[data-owner-idx]').forEach(tr => {
        tr.addEventListener('click', () => {
            const idx = parseInt(tr.dataset.ownerIdx);
            showOwnerDetail(filtered[idx].naam);
        });
    });
}

function showOwnerDetail(naam) {
    const owner = allOwners.find(o => o.naam === naam);
    if (!owner) return;

    document.getElementById('panelTitle').textContent = `👤 ${owner.naam}`;

    const propsHtml = owner.properties.map(p => `
        <div class="property-mini" onclick="showPropertyDetail('${p.object_id}')">
            <div class="addr">${p.object_id} - ${p.adres}</div>
            <div class="meta">
                ${p.plaats || ''} | 
                Inhuur: ${formatMoney(p.inhuur_totaal_excl_btw)} | 
                Huurder: ${p.huurder_naam || 'Leeg'} |
                GWE: ${formatMoney(p.inhuur_voorschot_gwe || p.voorschot_gwe_standaard)}
            </div>
        </div>
    `).join('');

    document.getElementById('panelBody').innerHTML = `
        <div class="detail-section">
            <h3>Contact</h3>
            <div class="detail-grid">
                <div class="detail-item"><span class="label">Email:</span><span class="value">${owner.email ? `<a href="mailto:${owner.email}">${owner.email}</a>` : '-'}</span></div>
                <div class="detail-item"><span class="label">Telefoon:</span><span class="value">${owner.telefoon ? `<a href="tel:${owner.telefoon}">${owner.telefoon}</a>` : '-'}</span></div>
                <div class="detail-item"><span class="label">Adres:</span><span class="value">${owner.adres || '-'}</span></div>
                <div class="detail-item"><span class="label">Postcode:</span><span class="value">${owner.postcode || '-'}</span></div>
                <div class="detail-item"><span class="label">Plaats:</span><span class="value">${owner.plaats || '-'}</span></div>
                <div class="detail-item"><span class="label">IBAN:</span><span class="value">${owner.iban || '-'}</span></div>
            </div>
        </div>
        <div class="detail-section">
            <h3>Samenvatting</h3>
            <div class="detail-grid">
                <div class="detail-item"><span class="label">Woningen:</span><span class="value">${owner.properties.length}</span></div>
                <div class="detail-item"><span class="label">Tot. Inhuur:</span><span class="value money">${formatMoney(owner.totalInhuur)}/maand</span></div>
            </div>
        </div>
        <div class="detail-section">
            <h3>Woningen (${owner.properties.length})</h3>
            <div class="property-list">${propsHtml}</div>
        </div>
        <button class="btn" style="margin-top:1rem" onclick="window.print()">🖨️ Print</button>
    `;

    openPanel('owner', naam);
}

// ========== HUURDERS ==========
function renderHuurders() {
    const search = document.getElementById('searchHuurders').value.toLowerCase();
    let filtered = allTenants.filter(t => !search || t.naam.toLowerCase().includes(search));

    document.getElementById('huurdersCount').textContent = `${filtered.length} huurders`;

    const tbody = document.querySelector('#huurdersTable tbody');
    tbody.innerHTML = filtered.map((t, idx) => `
        <tr data-tenant-idx="${idx}" style="cursor:pointer">
            <td><strong>${escapeHtml(t.naam)}</strong></td>
            <td>${escapeHtml(t.type || '-')}</td>
            <td>${escapeHtml(t.email || '-')}</td>
            <td>${escapeHtml(t.telefoon || '-')}</td>
            <td>${t.properties.length}</td>
            <td class="money">${formatMoney(t.totalVerhuur)}/m</td>
        </tr>
    `).join('');

    // Add click handlers
    tbody.querySelectorAll('tr[data-tenant-idx]').forEach(tr => {
        tr.addEventListener('click', () => {
            const idx = parseInt(tr.dataset.tenantIdx);
            showTenantDetail(filtered[idx].naam);
        });
    });
}

function showTenantDetail(naam) {
    const tenant = allTenants.find(t => t.naam === naam);
    if (!tenant) return;

    document.getElementById('panelTitle').textContent = `👥 ${tenant.naam}`;

    const propsHtml = tenant.properties.map(p => `
        <div class="property-mini" onclick="showPropertyDetail('${p.object_id}')">
            <div class="addr">${p.object_id} - ${p.adres}</div>
            <div class="meta">
                ${p.plaats || ''} | 
                Verhuur: ${formatMoney(p.verhuur_totaal_excl_btw)} | 
                Eigenaar: ${p.eigenaar_naam || '-'} |
                GWE: ${formatMoney(p.verhuur_voorschot_gwe)}
            </div>
        </div>
    `).join('');

    document.getElementById('panelBody').innerHTML = `
        <div class="detail-section">
            <h3>Contact</h3>
            <div class="detail-grid">
                <div class="detail-item"><span class="label">Type:</span><span class="value">${tenant.type || '-'}</span></div>
                <div class="detail-item"><span class="label">Email:</span><span class="value">${tenant.email ? `<a href="mailto:${tenant.email}">${tenant.email}</a>` : '-'}</span></div>
                <div class="detail-item"><span class="label">Telefoon:</span><span class="value">${tenant.telefoon ? `<a href="tel:${tenant.telefoon}">${tenant.telefoon}</a>` : '-'}</span></div>
                <div class="detail-item"><span class="label">Adres:</span><span class="value">${tenant.adres || '-'}</span></div>
                <div class="detail-item"><span class="label">Plaats:</span><span class="value">${tenant.plaats || '-'}</span></div>
            </div>
        </div>
        <div class="detail-section">
            <h3>Samenvatting</h3>
            <div class="detail-grid">
                <div class="detail-item"><span class="label">Woningen:</span><span class="value">${tenant.properties.length}</span></div>
                <div class="detail-item"><span class="label">Tot. Verhuur:</span><span class="value money">${formatMoney(tenant.totalVerhuur)}/maand</span></div>
            </div>
        </div>
        <div class="detail-section">
            <h3>Gehuurde Woningen (${tenant.properties.length})</h3>
            <div class="property-list">${propsHtml}</div>
        </div>
        <button class="btn" style="margin-top:1rem" onclick="window.print()">🖨️ Print</button>
    `;

    openPanel('tenant', naam);
}

// ========== FINANCIEEL ==========
function renderFinancieel() {
    const search = document.getElementById('searchFinancieel').value.toLowerCase();
    const statusFilter = document.getElementById('filterFinStatus').value;
    const sortMode = document.getElementById('sortFinancieel').value;

    let filtered = allProperties.filter(p => {
        const matchSearch = !search ||
            (p.adres || '').toLowerCase().includes(search) ||
            (p.object_id || '').toLowerCase().includes(search);
        const matchStatus = !statusFilter || (p.beschikbaarheid_status || '').includes(statusFilter);
        return matchSearch && matchStatus;
    });

    // Sort
    filtered.sort((a, b) => {
        switch (sortMode) {
            case 'marge_desc': return (b.marge_maand_excl_btw || 0) - (a.marge_maand_excl_btw || 0);
            case 'marge_asc': return (a.marge_maand_excl_btw || 0) - (b.marge_maand_excl_btw || 0);
            case 'inhuur_desc': return (b.inhuur_totaal_excl_btw || 0) - (a.inhuur_totaal_excl_btw || 0);
            case 'verhuur_desc': return (b.verhuur_totaal_excl_btw || 0) - (a.verhuur_totaal_excl_btw || 0);
            default: return 0;
        }
    });

    const tbody = document.querySelector('#financieelTable tbody');
    tbody.innerHTML = filtered.map(p => `
        <tr onclick="showPropertyDetail('${p.object_id}')">
            <td>${p.object_id}</td>
            <td>${p.adres || '-'}</td>
            <td>${p.plaats || '-'}</td>
            <td class="money">${formatMoney(p.inhuur_totaal_excl_btw)}</td>
            <td class="money">${formatMoney(p.verhuur_totaal_excl_btw)}</td>
            <td class="${getMoneyClass(p.marge_maand_excl_btw)}">${formatMoney(p.marge_maand_excl_btw)}</td>
            <td>${p.marge_percentage ? p.marge_percentage.toFixed(1) + '%' : '-'}</td>
            <td>${getStatusBadge(p.beschikbaarheid_status)}</td>
        </tr>
    `).join('');
}

// ========== PROPERTY DETAIL ==========
function showPropertyDetail(objectId) {
    const p = allProperties.find(prop => prop.object_id === objectId);
    if (!p) return;

    document.getElementById('panelTitle').textContent = `🏠 ${p.object_id} - ${p.adres}`;

    document.getElementById('panelBody').innerHTML = `
        <div class="detail-section">
            <h3>Woning</h3>
            <div class="detail-grid">
                <div class="detail-item"><span class="label">Object:</span><span class="value">${p.object_id}</span></div>
                <div class="detail-item"><span class="label">Adres:</span><span class="value">${p.adres || '-'}</span></div>
                <div class="detail-item"><span class="label">Postcode:</span><span class="value">${p.postcode || '-'}</span></div>
                <div class="detail-item"><span class="label">Plaats:</span><span class="value">${p.plaats || '-'}</span></div>
                <div class="detail-item"><span class="label">Type:</span><span class="value">${p.woning_type || '-'}</span></div>
                <div class="detail-item"><span class="label">Opp.:</span><span class="value">${p.oppervlakte_m2 ? p.oppervlakte_m2 + ' m²' : '-'}</span></div>
                <div class="detail-item"><span class="label">Slaapk.:</span><span class="value">${p.aantal_slaapkamers || '-'}</span></div>
                <div class="detail-item"><span class="label">Capaciteit:</span><span class="value">${p.capaciteit_personen || '-'}</span></div>
                <div class="detail-item"><span class="label">Status:</span><span class="value">${getStatusBadge(p.beschikbaarheid_status)}</span></div>
                <div class="detail-item"><span class="label">Kluis 1:</span><span class="value">${p.kluis_code_1 || '-'}</span></div>
                <div class="detail-item"><span class="label">Kluis 2:</span><span class="value">${p.kluis_code_2 || '-'}</span></div>
            </div>
        </div>

        <div class="detail-section">
            <h3>👤 Eigenaar</h3>
            <div class="detail-grid">
                <div class="detail-item"><span class="label">Naam:</span><span class="value">${p.eigenaar_naam || '-'}</span></div>
                <div class="detail-item"><span class="label">Email:</span><span class="value">${p.eigenaar_email ? `<a href="mailto:${p.eigenaar_email}">${p.eigenaar_email}</a>` : '-'}</span></div>
                <div class="detail-item"><span class="label">Telefoon:</span><span class="value">${p.eigenaar_telefoon ? `<a href="tel:${p.eigenaar_telefoon}">${p.eigenaar_telefoon}</a>` : '-'}</span></div>
                <div class="detail-item"><span class="label">IBAN:</span><span class="value">${p.eigenaar_iban || '-'}</span></div>
            </div>
        </div>

        <div class="detail-section">
            <h3>👥 Huurder</h3>
            <div class="detail-grid">
                <div class="detail-item"><span class="label">Naam:</span><span class="value">${p.huurder_naam || '-'}</span></div>
                <div class="detail-item"><span class="label">Type:</span><span class="value">${p.huurder_type || '-'}</span></div>
                <div class="detail-item"><span class="label">Email:</span><span class="value">${p.huurder_email ? `<a href="mailto:${p.huurder_email}">${p.huurder_email}</a>` : '-'}</span></div>
                <div class="detail-item"><span class="label">Telefoon:</span><span class="value">${p.huurder_telefoon ? `<a href="tel:${p.huurder_telefoon}">${p.huurder_telefoon}</a>` : '-'}</span></div>
            </div>
        </div>

        <div class="detail-section">
            <h3>💰 Inhuur (van eigenaar)</h3>
            <div class="detail-grid">
                <div class="detail-item"><span class="label">Bedrag:</span><span class="value money">${formatMoney(p.inhuur_totaal_excl_btw)}/m</span></div>
                <div class="detail-item"><span class="label">Borg:</span><span class="value">${formatMoney(p.inhuur_borg)}</span></div>
                <div class="detail-item"><span class="label">GWE:</span><span class="value">${formatMoney(p.inhuur_voorschot_gwe)}</span></div>
                <div class="detail-item"><span class="label">Start:</span><span class="value">${p.inhuur_start || '-'}</span></div>
                <div class="detail-item"><span class="label">Eind:</span><span class="value">${p.inhuur_eind || '-'}</span></div>
            </div>
        </div>

        <div class="detail-section">
            <h3>💵 Verhuur (aan huurder)</h3>
            <div class="detail-grid">
                <div class="detail-item"><span class="label">Bedrag:</span><span class="value money">${formatMoney(p.verhuur_totaal_excl_btw)}/m</span></div>
                <div class="detail-item"><span class="label">Borg:</span><span class="value">${formatMoney(p.verhuur_borg)}</span></div>
                <div class="detail-item"><span class="label">GWE:</span><span class="value">${formatMoney(p.verhuur_voorschot_gwe)}</span></div>
                <div class="detail-item"><span class="label">Start:</span><span class="value">${p.verhuur_start || '-'}</span></div>
                <div class="detail-item"><span class="label">Eind:</span><span class="value">${p.verhuur_eind || '-'}</span></div>
            </div>
        </div>

        <div class="detail-section">
            <h3>📊 Marge</h3>
            <div class="detail-grid">
                <div class="detail-item"><span class="label">Maand:</span><span class="value ${getMoneyClass(p.marge_maand_excl_btw)}">${formatMoney(p.marge_maand_excl_btw)}</span></div>
                <div class="detail-item"><span class="label">Jaar:</span><span class="value ${getMoneyClass(p.marge_jaar_excl_btw)}">${formatMoney(p.marge_jaar_excl_btw)}</span></div>
                <div class="detail-item"><span class="label">Percentage:</span><span class="value">${p.marge_percentage ? p.marge_percentage.toFixed(1) + '%' : '-'}</span></div>
            </div>
        </div>

        <div class="detail-section">
            <h3>📁 Documenten</h3>
            <div class="detail-grid">
                ${p.sharepoint_folder ? `<div class="detail-item"><span class="label">Folder:</span><span class="value"><a href="${p.sharepoint_folder}" target="_blank">📂 Open</a></span></div>` : ''}
                ${p.sharepoint_inhuur ? `<div class="detail-item"><span class="label">Inhuur:</span><span class="value"><a href="${p.sharepoint_inhuur}" target="_blank">📂 Open</a></span></div>` : ''}
                ${p.sharepoint_verhuur ? `<div class="detail-item"><span class="label">Verhuur:</span><span class="value"><a href="${p.sharepoint_verhuur}" target="_blank">📂 Open</a></span></div>` : ''}
            </div>
        </div>

        <button class="btn" style="margin-top:1rem" onclick="window.print()">🖨️ Print</button>
    `;

    openPanel('property', objectId);
}

function openPanel(viewType, id) {
    // Track history for back button
    if (viewType && id) {
        panelHistory.push({ type: viewType, id: id });
    }
    document.getElementById('detailPanel').classList.add('open');
    document.getElementById('overlay').classList.add('active');
    updateBackButton();
}

function closePanel() {
    document.getElementById('detailPanel').classList.remove('open');
    document.getElementById('overlay').classList.remove('active');
    panelHistory = [];
    updateBackButton();
}

// Panel navigation history
let panelHistory = [];

function updateBackButton() {
    const backBtn = document.getElementById('panelBackBtn');
    if (panelHistory.length > 1) {
        backBtn.style.display = 'inline-block';
    } else {
        backBtn.style.display = 'none';
    }
}

function goBackPanel() {
    if (panelHistory.length > 1) {
        panelHistory.pop(); // Remove current
        const prev = panelHistory[panelHistory.length - 1];
        // Re-render without adding to history
        panelHistory.pop();
        if (prev.type === 'owner') {
            showOwnerDetail(prev.id);
        } else if (prev.type === 'tenant') {
            showTenantDetail(prev.id);
        } else if (prev.type === 'property') {
            showPropertyDetail(prev.id);
        }
    }
}

// ========== SALES PREP CALCULATOR ==========
let salesSelectedProp = null;
let selectedServices = [];

function initSalesPrep() {
    // Populate cities for budget matcher
    const cities = [...new Set(allProperties.map(p => p.plaats).filter(Boolean))].sort();
    const budgetCity = document.getElementById('budgetCity');
    cities.forEach(c => {
        const opt = document.createElement('option');
        opt.value = c;
        opt.textContent = c;
        budgetCity.appendChild(opt);
    });

    // Setup searchable dropdown
    const searchInput = document.getElementById('salesPropSearch');
    const dropdown = document.getElementById('salesPropDropdown');

    searchInput.addEventListener('focus', () => {
        renderPropertyDropdown('');
        dropdown.classList.add('open');
    });

    searchInput.addEventListener('input', (e) => {
        renderPropertyDropdown(e.target.value);
        dropdown.classList.add('open');
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
        if (!e.target.closest('#propertySearchSelect')) {
            dropdown.classList.remove('open');
        }
    });

    // Margin target change
    document.getElementById('calcMargeTarget').addEventListener('input', updateSalesCalc);

    // New verhuur input
    document.getElementById('calcNieuweVerhuur').addEventListener('input', updateSalesCalc);

    // Service toggles
    document.querySelectorAll('#serviceToggles .toggle-btn').forEach(btn => {
        btn.addEventListener('click', function () {
            this.classList.toggle('active');
            updateSalesCalc();
        });
    });

    // One-time cost toggles
    document.querySelectorAll('#onetimeToggles .toggle-btn').forEach(btn => {
        btn.addEventListener('click', function () {
            this.classList.toggle('active');
            updateSalesCalc();
        });
    });
}

function renderPropertyDropdown(search) {
    const dropdown = document.getElementById('salesPropDropdown');
    const searchLower = search.toLowerCase();

    const filtered = allProperties.filter(p => {
        if (!search) return true;
        return (p.object_id || '').toLowerCase().includes(searchLower) ||
            (p.adres || '').toLowerCase().includes(searchLower) ||
            (p.plaats || '').toLowerCase().includes(searchLower) ||
            (p.eigenaar_naam || '').toLowerCase().includes(searchLower) ||
            (p.huurder_naam || '').toLowerCase().includes(searchLower);
    }).slice(0, 50); // Limit to 50 results

    dropdown.innerHTML = filtered.map(p => {
        const pppw = p.verhuur_pppw ? `€${p.verhuur_pppw.toFixed(0)}` : '-';
        const isSelected = salesSelectedProp && salesSelectedProp.object_id === p.object_id;
        return `
            <div class="dropdown-item ${isSelected ? 'selected' : ''}" data-id="${p.object_id}">
                <span><strong>${p.object_id}</strong> - ${p.adres}, ${p.plaats || ''}</span>
                <span class="pppw">${pppw}/pppw</span>
            </div>
        `;
    }).join('');

    // Add click handlers
    dropdown.querySelectorAll('.dropdown-item').forEach(item => {
        item.addEventListener('click', () => {
            const id = item.dataset.id;
            salesSelectedProp = allProperties.find(p => p.object_id === id);
            document.getElementById('salesPropSearch').value =
                `${salesSelectedProp.object_id} - ${salesSelectedProp.adres}`;
            dropdown.classList.remove('open');
            updateSalesCalc();
        });
    });
}

function updateSalesCalc() {
    if (!salesSelectedProp) {
        return;
    }

    const p = salesSelectedProp;
    const inhuur = p.inhuur_totaal_excl_btw || 0;
    const verhuurHuidig = p.verhuur_totaal_excl_btw || 0;
    const margeHuidig = p.marge_maand_excl_btw || 0;
    const margeTarget = parseFloat(document.getElementById('calcMargeTarget').value) || 0;
    const capacity = p.capaciteit_personen || 4;
    const weeksPerMonth = SALES_DATA.config?.weken_per_maand || 4.33;
    const gweValue = p.verhuur_voorschot_gwe || p.voorschot_gwe_standaard || 250;

    // Property info with enhanced details
    const inhuurPppw = p.inhuur_pppw ? `€${p.inhuur_pppw.toFixed(2)}/pppw` : '-';
    const verhuurPppw = p.verhuur_pppw ? `€${p.verhuur_pppw.toFixed(2)}/pppw` : '-';
    document.getElementById('salesPropInfo').innerHTML = `
        <div class="detail-grid" style="font-size:0.85rem">
            <div class="detail-item"><span class="label">Type:</span><span class="value">${p.woning_type || '-'}</span></div>
            <div class="detail-item"><span class="label">Capaciteit:</span><span class="value">${capacity} pers</span></div>
            <div class="detail-item"><span class="label">Slaapkamers:</span><span class="value">${p.aantal_slaapkamers || '-'}</span></div>
            <div class="detail-item"><span class="label">Status:</span><span class="value">${p.beschikbaarheid_status || '-'}</span></div>
            <div class="detail-item"><span class="label">Inhuur PPPW:</span><span class="value" style="color:var(--gray)">${inhuurPppw}</span></div>
            <div class="detail-item"><span class="label">Verhuur PPPW:</span><span class="value positive">${verhuurPppw}</span></div>
            <div class="detail-item"><span class="label">GWE/maand:</span><span class="value">€${gweValue}</span></div>
            <div class="detail-item"><span class="label">Beschikbaar:</span><span class="value">${p.verhuur_eind || 'Nu'}</span></div>
        </div>
    `;

    // Calculator
    document.getElementById('calcInhuur').textContent = formatMoney(inhuur);

    // Min verhuur = inhuur / (1 - margin%) for true margin calculation
    const minVerhuur = margeTarget >= 100 ? inhuur * 10 : inhuur / (1 - margeTarget / 100);
    document.getElementById('calcMinVerhuur').textContent = formatMoney(minVerhuur);

    // Calculate PPPW services
    let pppwServicesCost = 0;
    let servicesBreakdown = [];

    document.querySelectorAll('#serviceToggles .toggle-btn.active').forEach(btn => {
        const service = btn.dataset.service;
        if (service === 'gwe') {
            pppwServicesCost += gweValue;
            servicesBreakdown.push({ name: '💡 GWE', cost: gweValue, type: 'fixed' });
        } else if (btn.dataset.pppw) {
            const pppwRate = parseFloat(btn.dataset.pppw) || 0;
            const monthlyCost = pppwRate * capacity * weeksPerMonth;
            pppwServicesCost += monthlyCost;
            servicesBreakdown.push({
                name: btn.textContent.trim(),
                pppw: pppwRate,
                cost: monthlyCost,
                type: 'pppw'
            });
        }
    });

    // Calculate one-time costs
    let onetimeCost = 0;
    document.querySelectorAll('#onetimeToggles .toggle-btn.active').forEach(btn => {
        if (btn.dataset.onetime) {
            onetimeCost += parseFloat(btn.dataset.onetime) || 0;
        }
    });

    // Update services breakdown display
    const breakdownHtml = servicesBreakdown.length > 0
        ? servicesBreakdown.map(s =>
            s.type === 'pppw'
                ? `<div style="display:flex;justify-content:space-between;"><span>${s.name}</span><span>€${s.pppw}/pppw × ${capacity}p × ${weeksPerMonth.toFixed(2)}w = <strong>${formatMoney(s.cost)}</strong></span></div>`
                : `<div style="display:flex;justify-content:space-between;"><span>${s.name}</span><span><strong>${formatMoney(s.cost)}</strong>/maand</span></div>`
        ).join('')
        : '<span style="color:var(--gray);">Geen services geselecteerd</span>';
    document.getElementById('servicesDetails').innerHTML = breakdownHtml;

    // One-time costs display
    document.getElementById('calcOnetime').textContent = formatMoney(onetimeCost);

    // Total monthly = minVerhuur + PPPW services
    const totalMonthly = minVerhuur + pppwServicesCost;
    document.getElementById('calcTotalAdvice').textContent = formatMoney(totalMonthly);

    // PPPW calculations
    const pppwWithServices = totalMonthly / (capacity * weeksPerMonth);
    const pppwBase = minVerhuur / (capacity * weeksPerMonth);
    document.getElementById('calcPppwWithServices').textContent = `€${pppwWithServices.toFixed(2)}`;
    document.getElementById('calcPppwBase').textContent = `€${pppwBase.toFixed(2)}`;

    // Margin bar (visual)
    const marginPct = Math.min(100, Math.max(0, margeTarget));
    document.getElementById('marginFill').style.width = marginPct + '%';

    // ========== SCENARIO COMPARISON ==========
    document.getElementById('calcHuidigeVerhuur').textContent = formatMoney(verhuurHuidig);
    document.getElementById('calcInhuurRef').textContent = formatMoney(inhuur);
    document.getElementById('calcInhuurRef2').textContent = formatMoney(inhuur);
    document.getElementById('calcHuidigeMarge').textContent = formatMoney(margeHuidig);

    // Huidige margin % = marge / verhuur (not inhuur)
    const huidigeMargePct = verhuurHuidig > 0 ? ((margeHuidig / verhuurHuidig) * 100) : 0;
    document.getElementById('calcHuidigeMargePct').textContent = huidigeMargePct.toFixed(1) + '%';
    document.getElementById('calcHuidigeMargePct').className = huidigeMargePct >= 0 ? 'positive' : 'negative';

    // Huidige PPPW
    const huidigePppw = capacity > 0 ? verhuurHuidig / (capacity * weeksPerMonth) : 0;
    document.getElementById('calcHuidigePppw').textContent = `€${huidigePppw.toFixed(2)}`;

    // Nieuwe scenario
    const nieuweVerhuur = parseFloat(document.getElementById('calcNieuweVerhuur').value) || 0;
    const nieuweMarge = nieuweVerhuur - inhuur;
    const nieuweMargePct = nieuweVerhuur > 0 ? ((nieuweMarge / nieuweVerhuur) * 100) : 0;
    const nieuwePppw = capacity > 0 ? nieuweVerhuur / (capacity * weeksPerMonth) : 0;
    const verschil = nieuweMarge - margeHuidig;

    document.getElementById('calcNieuweMarge').textContent = formatMoney(nieuweMarge);
    document.getElementById('calcNieuweMarge').className = nieuweMarge >= 0 ? 'positive' : 'negative';

    document.getElementById('calcNieuweMargePct').textContent = nieuweMargePct.toFixed(1) + '%';
    document.getElementById('calcNieuweMargePct').className = nieuweMargePct >= 0 ? 'positive' : 'negative';

    document.getElementById('calcNieuwePppw').textContent = `€${nieuwePppw.toFixed(2)}`;
    document.getElementById('calcNieuwePppw').className = nieuwePppw >= huidigePppw ? 'positive' : 'negative';

    document.getElementById('calcVerschil').textContent = (verschil >= 0 ? '+' : '') + formatMoney(verschil);
    document.getElementById('calcVerschil').className = 'value ' + (verschil >= 0 ? 'positive' : 'negative');

    document.getElementById('calcVerschilJaar').textContent = (verschil >= 0 ? '+' : '') + formatMoney(verschil * 12);
    document.getElementById('calcVerschilJaar').className = 'value ' + (verschil >= 0 ? 'positive' : 'negative');

    // Quick info with enhanced PPPW
    const inhuurPppwQ = p.inhuur_pppw ? `€${p.inhuur_pppw.toFixed(2)}` : '-';
    const verhuurPppwQ = p.verhuur_pppw ? `€${p.verhuur_pppw.toFixed(2)}` : '-';
    document.getElementById('quickInfo').innerHTML = `
        <div style="font-size:0.85rem">
            <p><strong>👤 Eigenaar:</strong> ${p.eigenaar_naam || 'Onbekend'}</p>
            <p style="color:var(--gray)">${p.eigenaar_telefoon || ''} | ${p.eigenaar_email || ''}</p>
            <hr style="margin:0.5rem 0; border:none; border-top:1px solid #eee">
            <p><strong>👥 Huurder:</strong> ${p.huurder_naam || 'Leeg'}</p>
            <p style="color:var(--gray)">${p.huurder_telefoon || ''} | ${p.huurder_email || ''}</p>
            <hr style="margin:0.5rem 0; border:none; border-top:1px solid #eee">
            <p><strong>💰 PPPW:</strong> <span style="color:var(--gray)">Inhuur ${inhuurPppwQ}</span> → <span style="color:var(--success); font-weight:600">Verhuur ${verhuurPppwQ}</span></p>
            <p><strong>📅 Contract:</strong> ${p.verhuur_start || '-'} → ${p.verhuur_eind || '-'}</p>
        </div>
    `;
}

// ========== CONTRACT OUTPUT ==========
function generateContractOutput() {
    if (!salesSelectedProp) {
        alert('Selecteer eerst een woning');
        return;
    }

    const p = salesSelectedProp;
    const startDate = document.getElementById('contractStartDate').value;
    const duration = parseInt(document.getElementById('contractDuration').value) || 12;
    const totalAdvice = document.getElementById('calcTotalAdvice').textContent;
    const pppwWithServices = document.getElementById('calcPppwWithServices').textContent;
    const pppwBase = document.getElementById('calcPppwBase').textContent;
    const onetimeCost = document.getElementById('calcOnetime').textContent;
    const capacity = p.capaciteit_personen || 4;

    // Get selected services
    const selectedServices = [];
    document.querySelectorAll('#serviceToggles .toggle-btn.active, #onetimeToggles .toggle-btn.active').forEach(btn => {
        selectedServices.push(btn.textContent.trim());
    });

    const output = `
        <h4 style="margin-bottom:0.5rem;">📋 Contract Gegevens</h4>
        <table style="width:100%; border-collapse:collapse;">
            <tr><td style="padding:0.25rem 0; border-bottom:1px solid #eee;"><strong>Object</strong></td><td>${p.object_id} - ${p.adres}</td></tr>
            <tr><td style="padding:0.25rem 0; border-bottom:1px solid #eee;"><strong>Plaats</strong></td><td>${p.plaats || '-'}</td></tr>
            <tr><td style="padding:0.25rem 0; border-bottom:1px solid #eee;"><strong>Capaciteit</strong></td><td>${capacity} personen</td></tr>
            <tr><td style="padding:0.25rem 0; border-bottom:1px solid #eee;"><strong>Startdatum</strong></td><td>${startDate || 'Niet ingevuld'}</td></tr>
            <tr><td style="padding:0.25rem 0; border-bottom:1px solid #eee;"><strong>Looptijd</strong></td><td>${duration} maanden</td></tr>
            <tr><td style="padding:0.25rem 0; border-bottom:1px solid #eee;"><strong>Huur/maand</strong></td><td>${totalAdvice}</td></tr>
            <tr><td style="padding:0.25rem 0; border-bottom:1px solid #eee;"><strong>PPPW (incl. services)</strong></td><td>${pppwWithServices}</td></tr>
            <tr><td style="padding:0.25rem 0; border-bottom:1px solid #eee;"><strong>PPPW (kaal)</strong></td><td>${pppwBase}</td></tr>
            <tr><td style="padding:0.25rem 0; border-bottom:1px solid #eee;"><strong>Eenmalige kosten</strong></td><td>${onetimeCost}</td></tr>
            <tr><td style="padding:0.25rem 0;"><strong>Services</strong></td><td>${selectedServices.join(', ') || 'Geen'}</td></tr>
        </table>
        <button onclick="copyContractData()" style="margin-top:0.75rem; padding:0.5rem 1rem; background:#667eea; color:white; border:none; border-radius:var(--radius); cursor:pointer;">📋 Kopieer naar klembord</button>
    `;

    document.getElementById('contractOutput').innerHTML = output;
    document.getElementById('contractOutput').style.display = 'block';
}

function copyContractData() {
    const p = salesSelectedProp;
    const startDate = document.getElementById('contractStartDate').value;
    const duration = document.getElementById('contractDuration').value;
    const totalAdvice = document.getElementById('calcTotalAdvice').textContent;
    const pppwWithServices = document.getElementById('calcPppwWithServices').textContent;

    const selectedServices = [];
    document.querySelectorAll('#serviceToggles .toggle-btn.active, #onetimeToggles .toggle-btn.active').forEach(btn => {
        selectedServices.push(btn.textContent.trim());
    });

    const text = `CONTRACT GEGEVENS
Object: ${p.object_id} - ${p.adres}, ${p.plaats}
Capaciteit: ${p.capaciteit_personen} personen
Startdatum: ${startDate}
Looptijd: ${duration} maanden
Huur/maand: ${totalAdvice}
PPPW: ${pppwWithServices}
Services: ${selectedServices.join(', ')}`;

    navigator.clipboard.writeText(text).then(() => {
        alert('Contract data gekopieerd naar klembord!');
    });
}

// ========== BUDGET MATCHER WITH DISTANCE ==========

// Dutch city center coordinates (fallback for distance calc)
const CITY_COORDS = {
    'Rotterdam': { lat: 51.9225, lng: 4.4792 },
    'Den Haag': { lat: 52.0705, lng: 4.3007 },
    'Amsterdam': { lat: 52.3676, lng: 4.9041 },
    'Utrecht': { lat: 52.0893, lng: 5.1101 },
    'Leiden': { lat: 52.1601, lng: 4.4970 },
    'Delft': { lat: 52.0116, lng: 4.3571 },
    'Dordrecht': { lat: 51.8133, lng: 4.6901 },
    'Schiedam': { lat: 51.9194, lng: 4.3997 },
    'Vlaardingen': { lat: 51.9117, lng: 4.3419 },
    'Capelle aan den IJssel': { lat: 51.9292, lng: 4.5783 },
    'Spijkenisse': { lat: 51.8450, lng: 4.3292 },
    'Hoogvliet': { lat: 51.8625, lng: 4.3558 },
    'Zoetermeer': { lat: 52.0575, lng: 4.4931 },
    'Alphen aan den Rijn': { lat: 52.1292, lng: 4.6578 },
    'Gouda': { lat: 52.0175, lng: 4.7056 },
    'Hoek van Holland': { lat: 51.9792, lng: 4.1333 },
    'Heerlen': { lat: 50.8833, lng: 5.9833 },
    'Maastricht': { lat: 50.8514, lng: 5.6900 },
    'Eindhoven': { lat: 51.4416, lng: 5.4697 },
    'Tilburg': { lat: 51.5555, lng: 5.0913 },
    'Breda': { lat: 51.5719, lng: 4.7683 },
};

// Haversine formula for distance in km
function haversineDistance(lat1, lon1, lat2, lon2) {
    const R = 6371; // Earth's radius in km
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
        Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
        Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
}

// Geocode postcode using Nominatim (async)
async function geocodePostcode(postcode) {
    const cleanPostcode = postcode.replace(/\s/g, '').toUpperCase();
    const url = `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(cleanPostcode + ', Netherlands')}&format=json&limit=1&countrycodes=nl`;

    try {
        const response = await fetch(url, {
            headers: { 'User-Agent': 'RyanRent-Dashboard/1.0' }
        });
        const data = await response.json();
        if (data && data.length > 0) {
            return { lat: parseFloat(data[0].lat), lng: parseFloat(data[0].lon) };
        }
    } catch (e) {
        console.error('Geocoding failed:', e);
    }
    return null;
}

// Get property coordinates (from city lookup)
function getPropertyCoords(property) {
    // First try city lookup
    if (property.plaats && CITY_COORDS[property.plaats]) {
        return CITY_COORDS[property.plaats];
    }
    // Fallback to Rotterdam center
    return CITY_COORDS['Rotterdam'];
}

async function runBudgetMatcher() {
    const targetPostcode = document.getElementById('targetPostcode').value.trim();
    const maxDistance = parseFloat(document.getElementById('maxDistance').value) || 999;
    const minBudget = parseFloat(document.getElementById('budgetMin').value) || 0;
    const maxBudget = parseFloat(document.getElementById('budgetMax').value) || 999999;
    const minRooms = parseInt(document.getElementById('budgetRooms').value) || 0;
    const cityFilter = document.getElementById('budgetCity').value;
    const availableWithinWeeks = parseInt(document.getElementById('availableWithin').value) || 0;

    const statusDiv = document.getElementById('matcherStatus');
    const resultsDiv = document.getElementById('matcherResults');

    // Geocode target postcode if provided
    let targetCoords = null;
    let filterInfo = [];

    if (cityFilter) {
        filterInfo.push(`🏙️ ${cityFilter}`);
    }

    if (availableWithinWeeks === 0) {
        filterInfo.push('🏠 Nu vrij');
    } else {
        filterInfo.push(`📅 ${availableWithinWeeks}w`);
    }

    if (targetPostcode) {
        statusDiv.textContent = '📍 Locatie opzoeken...';
        targetCoords = await geocodePostcode(targetPostcode);
        if (!targetCoords) {
            statusDiv.textContent = '⚠️ Postcode niet gevonden';
        } else {
            filterInfo.push(`📍 ${maxDistance}km`);
        }
    }

    statusDiv.textContent = filterInfo.length > 0 ? `Filters: ${filterInfo.join(' + ')}` : '';

    // Calculate availability cutoff date
    const today = new Date();
    const cutoffDate = new Date(today);
    cutoffDate.setDate(cutoffDate.getDate() + (availableWithinWeeks * 7));

    // Filter properties
    let matches = allProperties.filter(p => {
        const pppw = p.verhuur_pppw || 0;
        const rooms = p.aantal_slaapkamers || 0;
        const matchCity = !cityFilter || p.plaats === cityFilter;
        const matchRooms = rooms >= minRooms;
        const nearBudget = pppw >= (minBudget * 0.8) && pppw <= (maxBudget * 1.2);

        // Check availability
        let isAvailable = false;
        if (p.beschikbaarheid_status === 'Beschikbaar' || p.beschikbaarheid_status === 'Leegstand') {
            isAvailable = true;
        } else if (p.verhuur_eind && availableWithinWeeks > 0) {
            // Check if contract ends within the timeframe
            const endDate = new Date(p.verhuur_eind);
            isAvailable = endDate <= cutoffDate;
        }

        return matchCity && matchRooms && nearBudget && pppw > 0 && isAvailable;
    });

    // Calculate distances if we have target coordinates
    if (targetCoords) {
        matches = matches.map(p => {
            const propCoords = getPropertyCoords(p);
            const distance = haversineDistance(
                targetCoords.lat, targetCoords.lng,
                propCoords.lat, propCoords.lng
            );
            return { ...p, _distance: distance };
        }).filter(p => p._distance <= maxDistance);

        // Sort by distance first, then by in-budget
        matches.sort((a, b) => {
            const aInBudget = a.verhuur_pppw >= minBudget && a.verhuur_pppw <= maxBudget;
            const bInBudget = b.verhuur_pppw >= minBudget && b.verhuur_pppw <= maxBudget;
            // Prioritize in-budget, then sort by distance
            if (aInBudget !== bInBudget) return bInBudget - aInBudget;
            return a._distance - b._distance;
        });
    } else {
        // No distance: sort by budget fit
        matches.sort((a, b) => {
            const aInBudget = a.verhuur_pppw >= minBudget && a.verhuur_pppw <= maxBudget;
            const bInBudget = b.verhuur_pppw >= minBudget && b.verhuur_pppw <= maxBudget;
            if (aInBudget && !bInBudget) return -1;
            if (!aInBudget && bInBudget) return 1;
            return a.verhuur_pppw - b.verhuur_pppw;
        });
    }

    if (matches.length === 0) {
        resultsDiv.innerHTML = `<p style="color: var(--gray); text-align: center;">Geen woningen gevonden</p>`;
        return;
    }

    resultsDiv.innerHTML = `<p style="margin-bottom:0.5rem; color:var(--gray); font-size:0.8rem;">${matches.length} woningen gevonden</p>` +
        matches.map(p => {
            const pppw = p.verhuur_pppw.toFixed(0);
            const inBudget = p.verhuur_pppw >= minBudget && p.verhuur_pppw <= maxBudget;
            const distanceText = p._distance !== undefined ? `${p._distance.toFixed(1)} km` : '';
            return `
                <div class="matcher-item ${inBudget ? 'in-budget' : ''}" onclick="selectMatcherProperty('${p.object_id}')">
                    <div class="info">
                        <div class="addr">${p.object_id} - ${p.adres}</div>
                        <div class="meta">${p.plaats || ''} ${distanceText ? '| 📍 ' + distanceText : ''} | ${p.aantal_slaapkamers || '?'} slaapk. | ${p.capaciteit_personen || '?'} pers</div>
                    </div>
                    <div class="pppw-badge">€${pppw}</div>
                </div>
            `;
        }).join('');
}

function selectMatcherProperty(objectId) {
    salesSelectedProp = allProperties.find(p => p.object_id === objectId);
    if (salesSelectedProp) {
        document.getElementById('salesPropSearch').value =
            `${salesSelectedProp.object_id} - ${salesSelectedProp.adres}`;
        updateSalesCalc();
        // Scroll to top of sales prep
        document.getElementById('panel-salesprep').scrollTo({ top: 0, behavior: 'smooth' });
    }
}

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', function () {
    setTimeout(initSalesPrep, 100);
});

const API_URL = 'http://localhost:8002/api/drafts';

let allDrafts = [];
let companies = new Set();
let dates = new Set();

const tableBody = document.getElementById('table-body');
const companyFilter = document.getElementById('company-filter');
const dateFilter = document.getElementById('date-filter');
const emptyState = document.getElementById('empty-state');
const refreshBtn = document.getElementById('refresh-btn');
const table = document.getElementById('drafts-table');

async function fetchDrafts() {
    try {
        const response = await fetch(API_URL);
        const json = await response.json();
        if (json.status === 'success') {
            allDrafts = json.data;
            processFilters();
            renderTable();
        } else {
            console.error("Failed to fetch drafts");
        }
    } catch (error) {
        console.error("Error fetching data:", error);
    }
}

function processFilters() {
    companies.clear();
    dates.clear();
    
    allDrafts.forEach(draft => {
        if (draft.parsed_company) companies.add(draft.parsed_company);
        if (draft.parsed_date) dates.add(draft.parsed_date);
    });

    // Populate Company Dropdown
    companyFilter.innerHTML = '<option value="all">All Companies</option>';
    [...companies].sort().forEach(company => {
        const option = document.createElement('option');
        option.value = company;
        option.textContent = company;
        companyFilter.appendChild(option);
    });

    // Populate Date Dropdown
    dateFilter.innerHTML = '<option value="all">All Dates</option>';
    [...dates].sort().forEach(date => {
        const option = document.createElement('option');
        option.value = date;
        // Format date from DDMMYY to a more readable format if needed, for now just use raw
        option.textContent = date;
        dateFilter.appendChild(option);
    });
}

function extractNameFromUrl(url) {
    if (!url) return "Unknown";
    const parts = url.split('/');
    let namePart = parts[parts.length - 1] || parts[parts.length - 2];
    namePart = namePart.split('?')[0]; // remove queries
    namePart = namePart.split('-').slice(0, 2).join(' '); // get first and last name
    return namePart.replace(/\b\w/g, l => l.toUpperCase()) || "Unknown";
}

function formatDate(isoString) {
    if (!isoString) return "N/A";
    const date = new Date(isoString);
    return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

function renderTable() {
    const selectedCompany = companyFilter.value;
    const selectedDate = dateFilter.value;

    const filteredDrafts = allDrafts.filter(draft => {
        const matchCompany = selectedCompany === 'all' || draft.parsed_company === selectedCompany;
        const matchDate = selectedDate === 'all' || draft.parsed_date === selectedDate;
        return matchCompany && matchDate;
    });

    tableBody.innerHTML = '';

    if (filteredDrafts.length === 0) {
        emptyState.classList.remove('hidden');
        table.style.display = 'none';
        return;
    }

    emptyState.classList.add('hidden');
    table.style.display = 'table';

    filteredDrafts.forEach((draft, index) => {
        const tr = document.createElement('tr');
        
        // Name parsing from URL if not provided directly
        const personName = extractNameFromUrl(draft.connection_profile_url);
        
        // Status Badge
        const isConnected = draft.connected;
        const badgeClass = isConnected ? 'badge-connected' : 'badge-pending';
        const badgeText = isConnected ? 'Connected' : 'Pending Request';
        
        // Job Link
        const jobUrl = draft.job_link || "#";

        tr.innerHTML = `
            <td>
                <a href="${draft.connection_profile_url}" target="_blank" class="profile-link">
                    <i class="ph-fill ph-linkedin-logo" style="color: #0a66c2; font-size: 1.2rem;"></i>
                    ${personName}
                </a>
            </td>
            <td><span class="badge ${badgeClass}">${badgeText}</span></td>
            <td>
                <a href="${jobUrl}" target="_blank" class="job-link">
                    <i class="ph ph-link"></i> View Job
                </a>
            </td>
            <td>
                <div class="message-box">${draft.draft_message || "No draft message"}</div>
            </td>
            <td><span class="date-text">${formatDate(draft.date)}</span></td>
            <td>
                <select class="modern-select workflow-select" data-index="${index}">
                    <option value="none">Select Action...</option>
                    <option value="send_email">Send Email</option>
                    <option value="wait_1_day">Wait 1 Day</option>
                    <option value="follow_up">Follow Up</option>
                    <option value="mark_done">Mark as Done</option>
                </select>
            </td>
            <td>
                <button class="btn btn-primary submit-row-btn" data-index="${index}">
                    <i class="ph ph-paper-plane-right"></i> Submit
                </button>
            </td>
        `;
        tableBody.appendChild(tr);
    });

    // Attach Event Listeners to Buttons
    document.querySelectorAll('.submit-row-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const rowIdx = e.currentTarget.getAttribute('data-index');
            const selectEl = document.querySelector(`.workflow-select[data-index="${rowIdx}"]`);
            const action = selectEl.value;
            const draft = filteredDrafts[rowIdx];
            
            if (action === 'none') {
                alert("Please select a workflow action first.");
                return;
            }
            
            // Dummy submit action
            console.log(`Submitting action '${action}' for profile ${draft.connection_profile_url}`);
            
            // UI Feedback
            const originalText = e.currentTarget.innerHTML;
            e.currentTarget.innerHTML = '<i class="ph ph-spinner-gap ph-spin"></i> Sent';
            e.currentTarget.classList.remove('btn-primary');
            e.currentTarget.classList.add('btn-secondary');
            
            setTimeout(() => {
                e.currentTarget.innerHTML = originalText;
                e.currentTarget.classList.add('btn-primary');
                e.currentTarget.classList.remove('btn-secondary');
            }, 2000);
        });
    });
}

// Event Listeners
companyFilter.addEventListener('change', renderTable);
dateFilter.addEventListener('change', renderTable);
refreshBtn.addEventListener('click', () => {
    refreshBtn.innerHTML = '<i class="ph ph-spinner-gap ph-spin"></i> Refreshing';
    fetchDrafts().then(() => {
        refreshBtn.innerHTML = '<i class="ph ph-arrows-clockwise"></i> Refresh';
    });
});

// Init
fetchDrafts();

letdocument.addEventListener('DOMContentLoaded', () => {
    const fetchBtn = document.getElementById('fetchBtn');
    const searchDateInput = document.getElementById('searchDate');
    const tableBody = document.getElementById('tableBody');
    const statusMessage = document.getElementById('statusMessage');
    const statsRow = document.getElementById('statsRow');
    const recordCountSpan = document.getElementById('recordCount');

    // Automatically fill today's date
    const today = new Date();
    const dd = String(today.getDate()).padStart(2, '0');
    const mm = String(today.getMonth() + 1).padStart(2, '0');
    const yy = String(today.getFullYear()).slice(-2);
    searchDateInput.value = `${dd}-${mm}-${yy}`;

    const API_BASE = 'https://email-creator-api.onrender.com';

    fetchBtn.addEventListener('click', async () => {
        const targetDate = searchDateInput.value.trim();
        
        if (!targetDate) {
            showError('Please enter a valid date (DD-MM-YY)');
            return;
        }

        // Reset UI
        hideError();
        statsRow.classList.add('hidden');
        tableBody.innerHTML = `<tr><td colspan="3" style="text-align: center;"><div class="loader" style="display: inline-block; border-top-color: #3b82f6;"></div></td></tr>`;
        
        fetchBtn.classList.add('loading');
        fetchBtn.disabled = true;

        try {
            const response = await fetch(`${API_BASE}/fetch_by_date?date=${encodeURIComponent(targetDate)}`, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json'
                }
            });

            const result = await response.json();

            if (response.ok) {
                const records = result.data || [];
                renderTable(records);
            } else {
                showError(`Error: ${result.detail || result.message || 'Failed to fetch'}`);
                showEmptyState();
            }
        } catch (error) {
            showError(`Network Error: Ensure the Render API is awake and running. (${error.message})`);
            showEmptyState();
        } finally {
            fetchBtn.classList.remove('loading');
            fetchBtn.disabled = false;
        }
    });

    function renderTable(records) {
        tableBody.innerHTML = ''; // Clear previous

        if (records.length === 0) {
            showEmptyState('No applications found for this date.');
            return;
        }

        records.forEach(record => {
            const tr = document.createElement('tr');
            
            // Format email
            const tdEmail = document.createElement('td');
            tdEmail.textContent = record.email || 'N/A';
            tdEmail.style.fontWeight = '500';

            // Format type
            const tdType = document.createElement('td');
            const typeBadge = document.createElement('span');
            typeBadge.textContent = record.type || 'N/A';
            typeBadge.style.background = 'rgba(59, 130, 246, 0.2)';
            typeBadge.style.color = '#60a5fa';
            typeBadge.style.padding = '4px 10px';
            typeBadge.style.borderRadius = '20px';
            typeBadge.style.fontSize = '12px';
            tdType.appendChild(typeBadge);

            // Format date
            const tdDate = document.createElement('td');
            tdDate.textContent = record.date || 'N/A';

            tr.appendChild(tdEmail);
            tr.appendChild(tdType);
            tr.appendChild(tdDate);
            tableBody.appendChild(tr);
        });

        // Show stats
        recordCountSpan.textContent = records.length;
        statsRow.classList.remove('hidden');
    }

    function showEmptyState(msg = 'Enter a date and click fetch to see records.') {
        tableBody.innerHTML = `<tr class="empty-state"><td colspan="3">${msg}</td></tr>`;
        statsRow.classList.add('hidden');
    }

    function showError(message) {
        statusMessage.textContent = message;
        statusMessage.classList.remove('hidden');
    }

    function hideError() {
        statusMessage.classList.add('hidden');
    }
});

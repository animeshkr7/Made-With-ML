const API_BASE_URL = "http://127.0.0.1:8001";

const addForm = document.getElementById('add-form');
const fetchForm = document.getElementById('fetch-form');
const resultsContainer = document.getElementById('resultsContainer');
const resultsTableBody = document.getElementById('resultsTableBody');
const noResultsMsg = document.getElementById('noResultsMsg');
const toast = document.getElementById('toast');

// Utility to show toast messages
function showToast(message, type = 'success') {
    toast.textContent = message;
    toast.className = '';
    toast.classList.add(`toast-${type}`, 'show');
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// Map status to css class
function getStatusClass(status) {
    const s = status.toLowerCase();
    if (s === 'applied') return 'status-applied';
    if (s === 'rejected') return 'status-rejected';
    return 'status-pending';
}

// 1. Add new record
addForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const url = document.getElementById('urlInput').value;
    const date = document.getElementById('dateInput').value;
    const status = document.getElementById('statusInput').value;
    
    const payload = { url, date, status };
    
    try {
        const response = await fetch(`${API_BASE_URL}/store_record`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showToast('Record saved successfully!');
            addForm.reset();
            // Automatically fetch for that date to show the user
            document.getElementById('fetchDateInput').value = date;
            fetchForm.dispatchEvent(new Event('submit'));
        } else {
            showToast(result.detail || 'Error saving record', 'error');
        }
    } catch (err) {
        showToast('Network error connecting to API', 'error');
        console.error(err);
    }
});

// 2. Fetch records
fetchForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const date = document.getElementById('fetchDateInput').value;
    
    try {
        const response = await fetch(`${API_BASE_URL}/fetch_by_date?date=${date}`);
        const result = await response.json();
        
        resultsTableBody.innerHTML = '';
        
        if (response.ok && result.data && result.data.length > 0) {
            resultsContainer.style.display = 'block';
            noResultsMsg.style.display = 'none';
            
            result.data.forEach(item => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${item.id}</td>
                    <td style="max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                        <a href="${item.url}" target="_blank" style="color: var(--primary); text-decoration: none;">${item.url}</a>
                    </td>
                    <td>${item.date}</td>
                    <td><span class="status-badge ${getStatusClass(item.status)}">${item.status}</span></td>
                    <td class="action-btns">
                        <button class="btn-secondary" onclick="updateRecord(${item.id})">Update</button>
                        <button class="btn-danger" onclick="deleteRecord(${item.id}, '${item.date}')">Delete</button>
                    </td>
                `;
                resultsTableBody.appendChild(tr);
            });
        } else {
            resultsContainer.style.display = 'none';
            noResultsMsg.style.display = 'block';
            if (!response.ok) {
                showToast(result.detail || 'Error fetching records', 'error');
            }
        }
    } catch (err) {
        showToast('Network error connecting to API', 'error');
        console.error(err);
    }
});

// 3. Delete record
async function deleteRecord(id, date) {
    if (!confirm(`Are you sure you want to delete record #${id}?`)) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/delete_record/${id}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showToast('Record deleted');
            // Refresh table
            document.getElementById('fetchDateInput').value = date;
            fetchForm.dispatchEvent(new Event('submit'));
        } else {
            const result = await response.json();
            showToast(result.detail || 'Error deleting', 'error');
        }
    } catch (err) {
        showToast('Network error', 'error');
    }
}

// 4. Update record
async function updateRecord(id) {
    const newStatus = prompt("Enter new status (Pending, Applied, Rejected):");
    if (!newStatus) return;
    
    // basic validation
    const validStatuses = ['Pending', 'Applied', 'Rejected'];
    const formattedStatus = newStatus.charAt(0).toUpperCase() + newStatus.slice(1).toLowerCase();
    
    if (!validStatuses.includes(formattedStatus)) {
        showToast('Invalid status entered.', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/update_record/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: formattedStatus })
        });
        
        if (response.ok) {
            showToast('Record updated successfully');
            // Refresh table
            fetchForm.dispatchEvent(new Event('submit'));
        } else {
            const result = await response.json();
            showToast(result.detail || 'Error updating', 'error');
        }
    } catch (err) {
        showToast('Network error', 'error');
    }
}

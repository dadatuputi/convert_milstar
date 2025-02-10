let originalData = null;
let ynabData = null;

// DOM Elements
const dropZone = document.getElementById('dropZone');
const csvInput = document.getElementById('csvInput');
const fileInfo = document.getElementById('fileInfo');
const csvContent = document.getElementById('csvContent');
const downloadBtn = document.getElementById('downloadCsv');

// Event Listeners
dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('dragover');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    handleFile(e.dataTransfer.files[0]);
});

dropZone.addEventListener('click', () => csvInput.click());

csvInput.addEventListener('change', (e) => {
    if (e.target.files.length) {
        handleFile(e.target.files[0]);
    }
});

function handleFile(file) {
    if (!file || !file.name.endsWith('.csv')) {
        alert('Please upload a CSV file');
        return;
    }

    dropZone.classList.add('has-file');
    fileInfo.textContent = `File: ${file.name}`;

    Papa.parse(file, {
        complete: handleParsedData,
        header: true,
        skipEmptyLines: true,
        dynamicTyping: true
    });
}

function handleParsedData(results) {
    originalData = results.data.filter(row => row.Status !== 'CANCELLED');
    
    ynabData = originalData.map(row => ({
        Date: new Date(row['Finished on']).toISOString().split('T')[0],
        Payee: row.Direction === 'OUT' ? row['Target name'] : row['Source name'],
        Memo: row.Reference ? `${row.Reference}; ${row.ID}` : row.ID,
        Amount: row.Direction === 'OUT' ? 
            -Math.abs(row['Target amount (after fees)']) : 
            Math.abs(row['Target amount (after fees)']),
        id: row.ID // Adding ID for tracking edits
    }));

    displayCSV(ynabData);
    downloadBtn.disabled = false;
    downloadBtn.addEventListener('click', downloadCSV, { once: true });
}

function displayCSV(data) {
    if (!data.length) return;

    const headers = ['Date', 'Payee', 'Memo', 'Amount'];
    const html = `
        <table>
            <thead>
                <tr>${headers.map(h => `<th>${h}</th>`).join('')}</tr>
            </thead>
            <tbody>
                ${data.map(row => `
                    <tr data-id="${row.id}">
                        <td>${row.Date}</td>
                        <td contenteditable="true" class="editable payee">${row.Payee}</td>
                        <td contenteditable="true" class="editable memo">${row.Memo}</td>
                        <td>$${row.Amount.toFixed(2)}</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
    
    csvContent.innerHTML = html;

    // Add event listeners for editable cells
    document.querySelectorAll('.editable').forEach(cell => {
        cell.addEventListener('blur', handleEdit);
    });
}

function handleEdit(event) {
    const cell = event.target;
    const row = cell.closest('tr');
    const id = row.dataset.id;
    const field = cell.classList.contains('payee') ? 'Payee' : 'Memo';
    
    // Update the data
    const rowData = ynabData.find(item => item.id === id);
    if (rowData) {
        rowData[field] = cell.textContent;
    }
}

function downloadCSV() {
    // Remove id field before download
    const downloadData = ynabData.map(({ id, ...rest }) => rest);
    const csv = Papa.unparse(downloadData);
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'ynab_import.csv';
    link.click();
}
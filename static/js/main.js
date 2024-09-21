document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('uploadForm');
    const analysisResult = document.getElementById('analysisResult');
    const resultContent = document.getElementById('resultContent');
    const exportBtn = document.getElementById('exportBtn');
    const reportsList = document.getElementById('reportsList');

    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData();
        const fileInput = document.getElementById('pdfFile');
        formData.append('file', fileInput.files[0]);

        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.id) {
                fetchReport(data.id);
            } else {
                alert('Error: ' + data.error);
            }
        })
        .catch(error => console.error('Error:', error));
    });

    function fetchReport(id) {
        fetch(`/report/${id}`)
        .then(response => response.json())
        .then(report => {
            displayReport(report);
            fetchReports();
        })
        .catch(error => console.error('Error:', error));
    }

    function displayReport(report) {
        const content = report.content;
        resultContent.innerHTML = `
            <h3 class="font-bold">${content.report_title}</h3>
            <p><strong>Audit Organization:</strong> ${content.audit_organization}</p>
            <p><strong>Audit Objectives:</strong> ${content.audit_objectives.join(', ')}</p>
            <p><strong>Overall Conclusion:</strong> ${content.overall_conclusion}</p>
            <h4 class="font-semibold mt-4">Key Findings:</h4>
            <ul>${content.key_findings.map(f => `<li>${f}</li>`).join('')}</ul>
            <h4 class="font-semibold mt-4">Recommendations:</h4>
            <ul>${content.recommendations.map(r => `<li>${r}</li>`).join('')}</ul>
            <p><strong>AI-Generated Insight:</strong> ${content.llm_insight}</p>
            <h4 class="font-semibold mt-4">Potential Future Audit Objectives:</h4>
            <ul>${content.potential_audit_objectives.map(o => `<li>${o}</li>`).join('')}</ul>
        `;
        analysisResult.classList.remove('hidden');
        exportBtn.onclick = () => window.location.href = `/export/${report.id}`;
    }

    function fetchReports() {
        fetch('/reports')
        .then(response => response.json())
        .then(reports => {
            reportsList.innerHTML = reports.map(report => `
                <li>
                    <a href="#" class="text-blue-500 hover:underline" onclick="fetchReport(${report.id}); return false;">
                        ${report.file_name} (Version ${report.version})
                    </a>
                </li>
            `).join('');
        })
        .catch(error => console.error('Error:', error));
    }

    fetchReports();
});

function fetchReport(id) {
    fetch(`/report/${id}`)
    .then(response => response.json())
    .then(report => {
        displayReport(report);
    })
    .catch(error => console.error('Error:', error));
}

function displayReport(report) {
    const analysisResult = document.getElementById('analysisResult');
    const resultContent = document.getElementById('resultContent');
    const exportBtn = document.getElementById('exportBtn');
    const content = report.content;
    resultContent.innerHTML = `
        <h3 class="font-bold">${content.report_title}</h3>
        <p><strong>Audit Organization:</strong> ${content.audit_organization}</p>
        <p><strong>Audit Objectives:</strong> ${content.audit_objectives.join(', ')}</p>
        <p><strong>Overall Conclusion:</strong> ${content.overall_conclusion}</p>
        <h4 class="font-semibold mt-4">Key Findings:</h4>
        <ul>${content.key_findings.map(f => `<li>${f}</li>`).join('')}</ul>
        <h4 class="font-semibold mt-4">Recommendations:</h4>
        <ul>${content.recommendations.map(r => `<li>${r}</li>`).join('')}</ul>
        <p><strong>AI-Generated Insight:</strong> ${content.llm_insight}</p>
        <h4 class="font-semibold mt-4">Potential Future Audit Objectives:</h4>
        <ul>${content.potential_audit_objectives.map(o => `<li>${o}</li>`).join('')}</ul>
    `;
    analysisResult.classList.remove('hidden');
    exportBtn.onclick = () => window.location.href = `/export/${report.id}`;
}

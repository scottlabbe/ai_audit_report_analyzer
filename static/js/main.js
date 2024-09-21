document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('uploadForm');
    const analysisResult = document.getElementById('analysisResult');
    const resultContent = document.getElementById('resultContent');
    const exportBtn = document.getElementById('exportBtn');
    const reportsList = document.getElementById('reportsList');

    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        console.log('Form submitted, preparing to show loading indicator');

        const loadingIndicator = document.getElementById('loadingIndicator');
        console.log('Loading indicator element:', loadingIndicator);

        if (loadingIndicator) {
            loadingIndicator.style.display = 'flex';
            console.log('Loading indicator shown');
        } else {
            console.error('Loading indicator element not found');
        }

        const formData = new FormData();
        const fileInput = document.getElementById('pdfFile');
        formData.append('file', fileInput.files[0]);

        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            console.log('Fetch request completed, hiding loading indicator');
            if (loadingIndicator) {
                loadingIndicator.style.display = 'none';
            }

            if (data.id) {
                fetchReport(data.id);
            } else {
                alert('Error: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            console.log('Error occurred, hiding loading indicator');
            if (loadingIndicator) {
                loadingIndicator.style.display = 'none';
            }
            alert('An error occurred during upload and analysis.');
        });
    });

    function fetchReport(id) {
        fetch(`/report/${id}`)
        .then(response => response.json())
        .then(report => {
            if (report.error) {
                throw new Error(report.error);
            }
            displayReport(report);
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error: ' + error.message);
        });
    }

    function displayReport(report) {
        const content = report.content;
        
        if (!content || typeof content !== 'object') {
            resultContent.innerHTML = '<p class="text-red-500">Error: Invalid report data</p>';
            analysisResult.classList.remove('hidden');
            exportBtn.classList.add('hidden');
            return;
        }
        
        resultContent.innerHTML = `
            <h3 class="font-bold">${content.report_title || 'N/A'}</h3>
            <p><strong>Audit Organization:</strong> ${content.audit_organization || 'N/A'}</p>
            <p><strong>Audit Objectives:</strong> ${(content.audit_objectives || []).join(', ') || 'N/A'}</p>
            <p><strong>Overall Conclusion:</strong> ${content.overall_conclusion || 'N/A'}</p>
            <h4 class="font-semibold mt-4">Key Findings:</h4>
            <ul>${(content.key_findings || []).map(f => `<li>${f}</li>`).join('') || '<li>N/A</li>'}</ul>
            <h4 class="font-semibold mt-4">Recommendations:</h4>
            <ul>${(content.recommendations || []).map(r => `<li>${r}</li>`).join('') || '<li>N/A</li>'}</ul>
            <p><strong>AI-Generated Insight:</strong> ${content.llm_insight || 'N/A'}</p>
            <h4 class="font-semibold mt-4">Potential Future Audit Objectives:</h4>
            <ul>${(content.potential_audit_objectives || []).map(o => `<li>${o}</li>`).join('') || '<li>N/A</li>'}</ul>
        `;
        analysisResult.classList.remove('hidden');
        exportBtn.classList.remove('hidden');
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

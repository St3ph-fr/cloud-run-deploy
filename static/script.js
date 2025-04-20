document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('queryForm');
    const queryInput = document.getElementById('queryInput');
    const submitButton = document.getElementById('submitButton');
    const logOutput = document.getElementById('logOutput');
    const resultOutput = document.getElementById('resultOutput');

    form.addEventListener('submit', async (event) => {
        event.preventDefault(); // Prevent default page reload

        const query = queryInput.value.trim();
        if (!query) {
            alert('Please enter a query.');
            return;
        }

        // Disable button and show loading state
        submitButton.disabled = true;
        submitButton.textContent = 'Running...';
        logOutput.innerHTML = '<div class="loading">Processing your request...</div>';
        resultOutput.innerHTML = '<div class="loading">Waiting for final answer...</div>';
        logOutput.scrollTop = logOutput.scrollHeight; // Scroll to bottom

        try {
            const response = await fetch('/run', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query: query }),
            });

            const result = await response.json();

            if (!response.ok) {
                // Handle HTTP errors (e.g., 500 Internal Server Error)
                throw new Error(result.detail || `Server error: ${response.status}`);
            }

            // Update UI with results
            // Assuming the backend sends back { "logs": "...", "final_answer": "..." }
            logOutput.textContent = result.logs || 'No logs were generated.';
            resultOutput.textContent = result.final_answer || 'No final answer was provided.';
             logOutput.scrollTop = logOutput.scrollHeight; // Scroll to bottom


        } catch (error) {
            console.error('Error during fetch:', error);
            logOutput.innerHTML = `<div class="error">An error occurred: ${error.message}</div>`;
            resultOutput.innerHTML = `<div class="error">Failed to get answer.</div>`;
        } finally {
            // Re-enable button
            submitButton.disabled = false;
            submitButton.textContent = 'Run Agent';
        }
    });
});

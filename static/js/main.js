// Initialize Feather icons
document.addEventListener('DOMContentLoaded', () => {
    feather.replace();
});

// Handle job application form submission
function handleApplicationSubmit(event, jobId) {
    event.preventDefault();
    const form = event.target;
    const submitButton = form.querySelector('button[type="submit"]');
    const originalText = submitButton.innerHTML;
    const modal = document.getElementById('applyModal');

    try {
        submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Submitting...';
        submitButton.disabled = true;

        // For now, simulate submission with a success message
        setTimeout(() => {
            alert('Thank you for your application! The company will contact you soon.');
            // Hide modal and reset form
            const modalInstance = bootstrap.Modal.getInstance(modal);
            modalInstance.hide();
            form.reset();
        }, 1000);
    } catch (error) {
        console.error('Error submitting application:', error);
        alert('Error submitting application. Please try again.');
    } finally {
        // Always restore button state
        submitButton.innerHTML = originalText;
        submitButton.disabled = false;
    }
}

// Handle job post submission
function handleJobSubmit(event) {
    event.preventDefault();
    const form = event.target;
    const submitButton = form.querySelector('button[type="submit"]');
    const originalText = submitButton.innerHTML;

    submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Posting...';
    submitButton.disabled = true;

    const formData = {
        title: document.getElementById('title').value,
        company_id: document.getElementById('company').value,
        description: document.getElementById('description').value,
        location: document.getElementById('location').value,
        job_type: document.getElementById('jobType').value,
        salary_range: document.getElementById('salary').value,
        requirements: document.getElementById('requirements').value
    };

    fetch('/post-job', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        alert('Job posted successfully!');
        window.location.href = '/';
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error posting job. Please try again.');
    })
    .finally(() => {
        // Always restore button state
        submitButton.innerHTML = originalText;
        submitButton.disabled = false;
    });
}

// Generic function to handle form submissions
document.addEventListener('DOMContentLoaded', () => {
    // Handle regular form submissions (login, register)
    document.querySelectorAll('form:not(#jobPostForm):not(#applicationForm)').forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitButton = this.querySelector('button[type="submit"]');
            if (submitButton) {
                const originalText = submitButton.innerHTML;
                submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
                submitButton.disabled = true;

                // Set a timeout to restore button state if the form submission takes too long
                setTimeout(() => {
                    submitButton.innerHTML = originalText;
                    submitButton.disabled = false;
                }, 5000); // Reset after 5 seconds if no page transition
            }
        });
    });
});

// Handle job application (old function, kept for backward compatibility if needed)
function applyForJob(jobId) {
    const button = document.querySelector(`button[onclick="applyForJob(${jobId})"]`);
    const originalText = button.innerHTML;

    try {
        button.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Applying...';
        button.disabled = true;

        const confirmApply = confirm('Would you like to apply for this position?');

        if (confirmApply) {
            alert('Thank you for your application! The company will contact you soon.');
        }
    } finally {
        // Always restore button state
        button.innerHTML = originalText;
        button.disabled = false;
    }
}
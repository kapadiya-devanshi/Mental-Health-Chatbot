// Desktop Feedback Display Script
(function() {
  'use strict';

  const feedbackContainer = document.getElementById('desktop-feedback-container');
  const feedbackContent = document.getElementById('feedback-content');
  const closeButton = document.getElementById('close-feedback');

  // Check if feedback container exists
  if (!feedbackContainer || !feedbackContent) {
    return;
  }

  // Load and display feedbacks
  function loadFeedbacks() {
    fetch('/api/feedbacks')
      .then(response => response.json())
      .then(data => {
        if (data && data.length > 0) {
          displayFeedbacks(data);
          feedbackContainer.style.display = 'block';
        } else {
          feedbackContainer.style.display = 'none';
        }
      })
      .catch(error => {
        console.error('Error loading feedbacks:', error);
        feedbackContainer.style.display = 'none';
      });
  }

  // Display feedbacks in the container
  function displayFeedbacks(feedbacks) {
    feedbackContent.innerHTML = '';
    
    feedbacks.slice(0, 5).forEach(feedback => {
      const feedbackCard = document.createElement('div');
      feedbackCard.className = 'mb-3 p-3';
      feedbackCard.style.cssText = 'background-color: var(--card-bg); border: 1px solid var(--border-color); border-radius: 0.5rem;';
      
      const stars = '⭐'.repeat(feedback.rating);
      const date = new Date(feedback.timestamp).toLocaleDateString();
      
      // Escape HTML to prevent XSS
      const safeNotes = feedback.notes ? feedback.notes.replace(/</g, '&lt;').replace(/>/g, '&gt;') : '';
      const safeUsername = feedback.username.replace(/</g, '&lt;').replace(/>/g, '&gt;');
      
      feedbackCard.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.5rem;">
          <div>
            <strong style="color: var(--text-color); font-size: 0.9rem; font-weight: bold;">${safeUsername}</strong>
            <div style="font-size: 1rem; color: #ffc107; margin-top: 0.25rem; line-height: 1.2;">${stars}</div>
          </div>
          <small style="color: #6c757d; font-size: 0.75rem; font-style: normal;">${date}</small>
        </div>
        ${safeNotes ? `<p style="color: var(--text-color); font-size: 0.85rem; margin: 0.5rem 0 0 0; line-height: 1.4; font-style: normal;">${safeNotes}</p>` : ''}
      `;
      
      feedbackContent.appendChild(feedbackCard);
    });
  }

  // Close button handler
  if (closeButton) {
    closeButton.addEventListener('click', function() {
      feedbackContainer.style.display = 'none';
      // Store preference in localStorage
      localStorage.setItem('feedbackDisplayClosed', 'true');
    });
  }

  // Check if user previously closed the feedback display
  const wasClosed = localStorage.getItem('feedbackDisplayClosed');
  if (wasClosed === 'true') {
    // Reset after 24 hours
    const closeTime = localStorage.getItem('feedbackDisplayCloseTime');
    if (closeTime) {
      const now = Date.now();
      const dayInMs = 24 * 60 * 60 * 1000;
      if (now - parseInt(closeTime) > dayInMs) {
        localStorage.removeItem('feedbackDisplayClosed');
        localStorage.removeItem('feedbackDisplayCloseTime');
        loadFeedbacks();
      }
    }
  } else {
    // Load feedbacks on page load
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', loadFeedbacks);
    } else {
      loadFeedbacks();
    }
  }

  // Update close time when closed
  if (closeButton) {
    closeButton.addEventListener('click', function() {
      localStorage.setItem('feedbackDisplayCloseTime', Date.now().toString());
    });
  }

  // Refresh feedbacks every 5 minutes
  setInterval(loadFeedbacks, 5 * 60 * 1000);
})();


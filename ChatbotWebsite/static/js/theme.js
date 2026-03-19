// Theme management script
(function() {
  'use strict';

  // Get theme from localStorage or default to 'light'
  const getTheme = () => {
    return localStorage.getItem('theme') || 'light';
  };

  // Set theme
  const setTheme = (theme) => {
    localStorage.setItem('theme', theme);
    document.documentElement.setAttribute('data-theme', theme);
    updateThemeIcon(theme);
  };

  // Update theme icon
  const updateThemeIcon = (theme) => {
    const themeIcon = document.getElementById('theme-icon');
    if (themeIcon) {
      themeIcon.textContent = theme === 'dark' ? '☀️' : '🌙';
    }
  };

  // Toggle theme
  const toggleTheme = () => {
    const currentTheme = getTheme();
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
  };

  // Initialize theme immediately to prevent flash
  const initTheme = () => {
    const savedTheme = getTheme();
    document.documentElement.setAttribute('data-theme', savedTheme);
    // Update icon after DOM is ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => updateThemeIcon(savedTheme));
    } else {
      updateThemeIcon(savedTheme);
    }
  };

  // Initialize theme immediately
  initTheme();

  // Add click event listener to theme toggle button
  const setupThemeToggle = () => {
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
      themeToggle.addEventListener('click', toggleTheme);
    }
  };

  // Wait for DOM to be ready for button setup
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupThemeToggle);
  } else {
    setupThemeToggle();
  }
})();


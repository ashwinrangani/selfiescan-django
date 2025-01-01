document.addEventListener('DOMContentLoaded', () => {
    const themeToggle = document.getElementById('theme-toggle');
    const htmlElement = document.documentElement;
  
    // SVG Icons
    const lightIcon = themeToggle.querySelector('.block');
    const darkIcon = themeToggle.querySelector('.hidden');
  
    const currentTheme = localStorage.getItem('theme') || 'gourmet';
  
    // Apply the saved theme on page load
    htmlElement.setAttribute('data-theme', currentTheme);
    toggleIcons(currentTheme);
  
    // Toggle the theme on button click
    themeToggle.addEventListener('click', () => {
      const isDark = htmlElement.getAttribute('data-theme') === 'dark';
      const newTheme = isDark ? 'gourmet' : 'dark';
  
      htmlElement.setAttribute('data-theme', newTheme);
      localStorage.setItem('theme', newTheme);
      toggleIcons(newTheme);
    });
  
    function toggleIcons(theme) {
      if (theme === 'dark') {
        lightIcon.classList.add('hidden');
        darkIcon.classList.remove('hidden');
      } else {
        lightIcon.classList.remove('hidden');
        darkIcon.classList.add('hidden');
      }
    }
  });
  
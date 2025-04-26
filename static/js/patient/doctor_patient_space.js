document.addEventListener('DOMContentLoaded', function() {
    // Toggle sidebar
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('main-content');

    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('sidebar-collapsed');
            mainContent.classList.toggle('main-content-expanded');
        });
    }

    // Mobile menu toggle
    const mobileMenuToggle = document.getElementById('mobile-menu-toggle');

    if (mobileMenuToggle) {
        mobileMenuToggle.addEventListener('click', function() {
            sidebar.classList.toggle('sidebar-open');
        });
    }

    // Countdown timer for upcoming appointments
    const countdownElements = document.querySelectorAll('.appointment-countdown');

    if (countdownElements.length > 0) {
        // Update countdown every second
        setInterval(updateCountdowns, 1000);

        // Initial update
        updateCountdowns();
    }

    function updateCountdowns() {
        countdownElements.forEach(element => {
            const appointmentTime = new Date(element.getAttribute('data-time')).getTime();
            const now = new Date().getTime();
            const timeLeft = appointmentTime - now;

            if (timeLeft > 0) {
                // Calculate days, hours, minutes, seconds
                const days = Math.floor(timeLeft / (1000 * 60 * 60 * 24));
                const hours = Math.floor((timeLeft % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                const minutes = Math.floor((timeLeft % (1000 * 60 * 60)) / (1000 * 60));
                const seconds = Math.floor((timeLeft % (1000 * 60)) / 1000);

                // Display countdown
                if (days > 0) {
                    element.textContent = `${days}j ${hours}h ${minutes}m ${seconds}s`;
                } else if (hours > 0) {
                    element.textContent = `${hours}h ${minutes}m ${seconds}s`;
                } else {
                    element.textContent = `${minutes}m ${seconds}s`;
                }

                // Change color when less than 1 hour
                if (timeLeft < 1000 * 60 * 60) {
                    element.style.color = '#e74c3c';
                }
            } else {
                element.textContent = 'Maintenant !';
                element.style.color = '#2ecc71';

                // Enable join button
                const joinButton = element.closest('.appointment-card').querySelector('.join-consultation-btn');
                if (joinButton) {
                    joinButton.classList.remove('disabled');

                    // Add click event listener if not already added
                    if (!joinButton.hasAttribute('data-event-added')) {
                        joinButton.setAttribute('data-event-added', 'true');

                        joinButton.addEventListener('click', function(e) {
                            e.preventDefault();

                            // Get the video room URL
                            const videoRoomUrl = this.getAttribute('href');

                            // Open the video room in a new tab
                            window.open(videoRoomUrl, '_blank');
                        });
                    }
                }
            }
        });
    }
});

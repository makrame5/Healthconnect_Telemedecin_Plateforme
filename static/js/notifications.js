/**
 * Notifications - Scripts
 */

// Initialiser Socket.IO
let socket;

document.addEventListener('DOMContentLoaded', function() {
    // Initialiser Socket.IO
    initializeSocketIO();
    
    // Configurer les notifications
    setupNotifications();
    
    // Charger les notifications existantes
    loadNotifications();
});

/**
 * Initialise la connexion Socket.IO
 */
function initializeSocketIO() {
    // Connexion au serveur Socket.IO
    socket = io();
    
    // Événement de connexion
    socket.on('connect', function() {
        console.log('Connecté au serveur Socket.IO');
    });
    
    // Événement de déconnexion
    socket.on('disconnect', function() {
        console.log('Déconnecté du serveur Socket.IO');
    });
    
    // Événement de nouvelle notification
    socket.on('new_notification', function(notification) {
        console.log('Nouvelle notification reçue:', notification);
        addNotification(notification);
        updateNotificationBadge();
        
        // Afficher une notification système si le navigateur le supporte
        showBrowserNotification(notification);
    });
    
    // Événement de mise à jour de notification
    socket.on('notification_updated', function(data) {
        console.log('Notification mise à jour:', data);
        updateNotificationStatus(data.id, data.is_read);
        updateNotificationBadge();
    });
}

/**
 * Configure les notifications
 */
function setupNotifications() {
    const notificationToggle = document.getElementById('notification-toggle');
    const notificationDropdown = document.getElementById('notification-dropdown');
    
    if (!notificationToggle || !notificationDropdown) return;
    
    notificationToggle.addEventListener('click', function(event) {
        event.stopPropagation();
        
        // Fermer le menu profil s'il est ouvert
        const profileDropdown = document.getElementById('profile-dropdown');
        const profileToggle = document.getElementById('profile-toggle');
        
        if (profileDropdown && profileDropdown.classList.contains('show')) {
            profileDropdown.classList.remove('show');
            profileToggle.classList.remove('active');
        }
        
        // Toggle du dropdown notifications
        notificationDropdown.classList.toggle('show');
        
        // Marquer les notifications comme lues lorsqu'on ouvre le dropdown
        if (notificationDropdown.classList.contains('show')) {
            const unreadNotifications = document.querySelectorAll('.notification-item.notification-unread');
            unreadNotifications.forEach(notification => {
                const notificationId = notification.getAttribute('data-notification-id');
                markNotificationAsRead(notificationId);
            });
        }
    });
    
    // Empêcher la fermeture quand on clique dans le dropdown
    notificationDropdown.addEventListener('click', function(event) {
        event.stopPropagation();
    });
    
    // Fermer le dropdown quand on clique ailleurs
    document.addEventListener('click', function() {
        if (notificationDropdown.classList.contains('show')) {
            notificationDropdown.classList.remove('show');
        }
    });
    
    // Marquer toutes les notifications comme lues
    const markAllAsRead = document.querySelector('.notification-actions');
    if (markAllAsRead) {
        markAllAsRead.addEventListener('click', function() {
            const unreadNotifications = document.querySelectorAll('.notification-item.notification-unread');
            unreadNotifications.forEach(notification => {
                const notificationId = notification.getAttribute('data-notification-id');
                markNotificationAsRead(notificationId);
            });
            
            // Mettre à jour le badge
            updateNotificationBadge();
        });
    }
}

/**
 * Charge les notifications existantes depuis le serveur
 */
function loadNotifications() {
    fetch('/api/notifications')
        .then(response => response.json())
        .then(data => {
            // Vider le conteneur de notifications
            const notificationContainer = document.querySelector('.notification-list');
            if (notificationContainer) {
                notificationContainer.innerHTML = '';
                
                // Ajouter chaque notification
                data.notifications.forEach(notification => {
                    addNotification(notification);
                });
                
                // Mettre à jour le badge
                updateNotificationBadge();
            }
        })
        .catch(error => console.error('Erreur lors du chargement des notifications:', error));
}

/**
 * Ajoute une notification à l'interface
 * @param {Object} notification - Objet notification
 */
function addNotification(notification) {
    const notificationList = document.querySelector('.notification-list');
    if (!notificationList) return;
    
    // Créer l'élément de notification
    const notificationItem = document.createElement('div');
    notificationItem.className = `notification-item ${notification.is_read ? '' : 'notification-unread'}`;
    notificationItem.setAttribute('data-notification-id', notification.id);
    
    // Déterminer l'icône en fonction du type de notification
    let iconClass = 'fas fa-bell';
    if (notification.type === 'appointment') {
        iconClass = 'fas fa-calendar-check';
    } else if (notification.type === 'appointment_accepted') {
        iconClass = 'fas fa-check-circle';
    } else if (notification.type === 'appointment_rejected') {
        iconClass = 'fas fa-times-circle';
    } else if (notification.type === 'message') {
        iconClass = 'fas fa-envelope';
    }
    
    // Créer le contenu HTML
    notificationItem.innerHTML = `
        <div class="notification-icon">
            <i class="${iconClass}"></i>
        </div>
        <div class="notification-content">
            <div class="notification-text">${notification.content}</div>
            <div class="notification-time">${formatNotificationTime(notification.created_at)}</div>
        </div>
    `;
    
    // Ajouter un gestionnaire d'événements pour marquer comme lu au clic
    notificationItem.addEventListener('click', function() {
        if (!notification.is_read) {
            markNotificationAsRead(notification.id);
        }
        
        // Si la notification est liée à un rendez-vous, rediriger vers la page du rendez-vous
        if (notification.type === 'appointment' && notification.related_id) {
            window.location.href = `/doctor/appointment/${notification.related_id}`;
        }
    });
    
    // Ajouter au début de la liste
    notificationList.insertBefore(notificationItem, notificationList.firstChild);
    
    // Mettre à jour le badge
    updateNotificationBadge();
}

/**
 * Marque une notification comme lue
 * @param {number} notificationId - ID de la notification
 */
function markNotificationAsRead(notificationId) {
    // Mettre à jour l'interface
    const notificationItem = document.querySelector(`.notification-item[data-notification-id="${notificationId}"]`);
    if (notificationItem) {
        notificationItem.classList.remove('notification-unread');
    }
    
    // Envoyer au serveur via Socket.IO
    if (socket && socket.connected) {
        socket.emit('read_notification', { notification_id: notificationId });
    } else {
        // Fallback si Socket.IO n'est pas disponible
        fetch(`/api/notifications/${notificationId}/read`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            console.log('Notification marquée comme lue:', data);
            updateNotificationBadge();
        })
        .catch(error => console.error('Erreur lors du marquage de la notification:', error));
    }
}

/**
 * Met à jour le statut d'une notification
 * @param {number} notificationId - ID de la notification
 * @param {boolean} isRead - Statut de lecture
 */
function updateNotificationStatus(notificationId, isRead) {
    const notificationItem = document.querySelector(`.notification-item[data-notification-id="${notificationId}"]`);
    if (notificationItem) {
        if (isRead) {
            notificationItem.classList.remove('notification-unread');
        } else {
            notificationItem.classList.add('notification-unread');
        }
    }
}

/**
 * Met à jour le badge de notification
 */
function updateNotificationBadge() {
    const badge = document.querySelector('.notification-badge');
    if (!badge) return;
    
    const unreadCount = document.querySelectorAll('.notification-item.notification-unread').length;
    badge.textContent = unreadCount;
    
    // Masquer le badge s'il n'y a pas de notifications non lues
    if (unreadCount === 0) {
        badge.style.display = 'none';
    } else {
        badge.style.display = 'flex';
    }
}

/**
 * Formate le temps de la notification
 * @param {string} dateTimeStr - Date et heure au format ISO
 * @returns {string} - Texte formaté (ex: "Il y a 5 minutes")
 */
function formatNotificationTime(dateTimeStr) {
    const now = new Date();
    const notificationTime = new Date(dateTimeStr);
    const diffMs = now - notificationTime;
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHour = Math.floor(diffMin / 60);
    const diffDay = Math.floor(diffHour / 24);
    
    if (diffSec < 60) {
        return "À l'instant";
    } else if (diffMin < 60) {
        return `Il y a ${diffMin} minute${diffMin > 1 ? 's' : ''}`;
    } else if (diffHour < 24) {
        return `Il y a ${diffHour} heure${diffHour > 1 ? 's' : ''}`;
    } else if (diffDay < 7) {
        return `Il y a ${diffDay} jour${diffDay > 1 ? 's' : ''}`;
    } else {
        return notificationTime.toLocaleDateString();
    }
}

/**
 * Affiche une notification du navigateur
 * @param {Object} notification - Objet notification
 */
function showBrowserNotification(notification) {
    // Vérifier si les notifications sont supportées
    if (!("Notification" in window)) {
        console.log("Ce navigateur ne supporte pas les notifications desktop");
        return;
    }
    
    // Vérifier si l'autorisation a déjà été accordée
    if (Notification.permission === "granted") {
        // Créer et afficher la notification
        createBrowserNotification(notification);
    }
    // Sinon, demander la permission
    else if (Notification.permission !== "denied") {
        Notification.requestPermission().then(function (permission) {
            // Si l'utilisateur accepte, créer la notification
            if (permission === "granted") {
                createBrowserNotification(notification);
            }
        });
    }
}

/**
 * Crée et affiche une notification du navigateur
 * @param {Object} notification - Objet notification
 */
function createBrowserNotification(notification) {
    const notif = new Notification(notification.title, {
        body: notification.content,
        icon: '/static/images/logo.png'
    });
    
    // Rediriger vers la page appropriée au clic sur la notification
    notif.onclick = function() {
        window.focus();
        if (notification.type === 'appointment' && notification.related_id) {
            window.location.href = `/doctor/appointment/${notification.related_id}`;
        } else {
            // Ouvrir le dropdown des notifications
            const notificationToggle = document.getElementById('notification-toggle');
            if (notificationToggle) {
                notificationToggle.click();
            }
        }
    };
}

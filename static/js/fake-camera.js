/**
 * Utilitaire pour créer une caméra virtuelle pour les tests
 * Cela permet de tester la fonctionnalité d'appel vidéo sans avoir besoin de deux caméras physiques
 */

// Fonction pour créer un flux vidéo simulé
async function createFakeVideoStream() {
    // Créer un canvas qui servira de source vidéo
    const canvas = document.createElement('canvas');
    canvas.width = 640;
    canvas.height = 480;
    
    // Obtenir le contexte 2D pour dessiner
    const ctx = canvas.getContext('2d');
    
    // Fonction pour dessiner sur le canvas
    function drawToCanvas() {
        // Remplir le fond
        ctx.fillStyle = '#f0f0f0';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        // Dessiner un cercle qui se déplace pour montrer que la vidéo est active
        const time = Date.now() / 1000;
        const x = canvas.width / 2 + Math.cos(time) * 100;
        const y = canvas.height / 2 + Math.sin(time) * 100;
        
        ctx.beginPath();
        ctx.arc(x, y, 20, 0, 2 * Math.PI);
        ctx.fillStyle = '#4285F4';
        ctx.fill();
        
        // Ajouter du texte
        ctx.font = '20px Arial';
        ctx.fillStyle = '#333';
        ctx.textAlign = 'center';
        ctx.fillText('Caméra virtuelle', canvas.width / 2, 40);
        
        // Ajouter l'heure actuelle
        const now = new Date();
        ctx.fillText(now.toLocaleTimeString(), canvas.width / 2, canvas.height - 40);
        
        // Ajouter le rôle de l'utilisateur
        const userRole = document.body.getAttribute('data-user-role') || 'inconnu';
        ctx.fillText(`Rôle: ${userRole}`, canvas.width / 2, canvas.height - 80);
        
        // Continuer à dessiner
        requestAnimationFrame(drawToCanvas);
    }
    
    // Commencer à dessiner
    drawToCanvas();
    
    // Obtenir le flux vidéo à partir du canvas
    const stream = canvas.captureStream(30); // 30 FPS
    
    // Ajouter une piste audio simulée si nécessaire
    try {
        // Essayer d'obtenir uniquement l'audio réel
        const audioStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
        audioStream.getAudioTracks().forEach(track => {
            stream.addTrack(track);
        });
    } catch (e) {
        console.warn('Impossible d\'obtenir l\'audio réel, création d\'une piste audio silencieuse');
        // Créer un contexte audio
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const dst = oscillator.connect(audioContext.createMediaStreamDestination());
        oscillator.start();
        
        // Ajouter la piste audio au flux
        const audioTrack = dst.stream.getAudioTracks()[0];
        stream.addTrack(audioTrack);
    }
    
    return stream;
}

// Fonction pour remplacer getUserMedia
function patchGetUserMedia() {
    // Sauvegarder la fonction originale
    const originalGetUserMedia = navigator.mediaDevices.getUserMedia;
    
    // Remplacer par notre version
    navigator.mediaDevices.getUserMedia = async function(constraints) {
        // Si l'utilisateur a activé la caméra virtuelle
        if (window.useFakeCamera) {
            console.log('Utilisation de la caméra virtuelle');
            
            // Si la contrainte vidéo est demandée, utiliser notre flux simulé
            if (constraints.video) {
                try {
                    return await createFakeVideoStream();
                } catch (e) {
                    console.error('Erreur lors de la création du flux vidéo simulé:', e);
                    // En cas d'erreur, essayer la méthode originale
                    return await originalGetUserMedia.call(this, constraints);
                }
            }
        }
        
        // Sinon, utiliser la méthode originale
        return await originalGetUserMedia.call(this, constraints);
    };
}

// Fonction pour activer/désactiver la caméra virtuelle
function toggleFakeCamera() {
    window.useFakeCamera = !window.useFakeCamera;
    
    // Mettre à jour l'état du bouton
    const button = document.getElementById('toggle-fake-camera');
    if (button) {
        button.classList.toggle('active', window.useFakeCamera);
        button.innerHTML = window.useFakeCamera ? 
            '<i class="fas fa-video-slash"></i> Désactiver caméra virtuelle' : 
            '<i class="fas fa-video"></i> Activer caméra virtuelle';
    }
    
    // Sauvegarder la préférence
    localStorage.setItem('useFakeCamera', window.useFakeCamera ? 'true' : 'false');
    
    return window.useFakeCamera;
}

// Ajouter un bouton pour activer/désactiver la caméra virtuelle
function addFakeCameraToggle() {
    // Créer le bouton
    const button = document.createElement('button');
    button.id = 'toggle-fake-camera';
    button.className = 'fake-camera-toggle';
    button.innerHTML = '<i class="fas fa-video"></i> Activer caméra virtuelle';
    
    // Ajouter le style
    const style = document.createElement('style');
    style.textContent = `
        .fake-camera-toggle {
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 9999;
            background-color: #4285F4;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 10px 15px;
            font-size: 14px;
            cursor: pointer;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            transition: all 0.3s ease;
        }
        
        .fake-camera-toggle:hover {
            background-color: #3367D6;
        }
        
        .fake-camera-toggle.active {
            background-color: #EA4335;
        }
        
        .fake-camera-toggle.active:hover {
            background-color: #C62828;
        }
        
        .fake-camera-toggle i {
            margin-right: 5px;
        }
    `;
    
    // Ajouter le bouton et le style au document
    document.head.appendChild(style);
    document.body.appendChild(button);
    
    // Ajouter l'événement de clic
    button.addEventListener('click', toggleFakeCamera);
    
    // Restaurer la préférence
    window.useFakeCamera = localStorage.getItem('useFakeCamera') === 'true';
    if (window.useFakeCamera) {
        button.classList.add('active');
        button.innerHTML = '<i class="fas fa-video-slash"></i> Désactiver caméra virtuelle';
    }
}

// Initialiser quand le document est chargé
document.addEventListener('DOMContentLoaded', function() {
    // Patcher getUserMedia
    patchGetUserMedia();
    
    // Ajouter le bouton de toggle
    addFakeCameraToggle();
    
    console.log('Utilitaire de caméra virtuelle initialisé');
});

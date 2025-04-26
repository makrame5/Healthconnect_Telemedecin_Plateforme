/**
 * Utilitaire de débogage pour WebRTC
 * Ce script ajoute des fonctionnalités de débogage pour WebRTC
 */

// Fonction pour afficher les statistiques WebRTC
function showWebRTCStats(peerConnection) {
    if (!peerConnection) {
        console.error('Aucune connexion WebRTC disponible');
        return;
    }

    // Créer ou récupérer le conteneur de statistiques
    let statsContainer = document.getElementById('webrtc-stats-container');
    if (!statsContainer) {
        statsContainer = document.createElement('div');
        statsContainer.id = 'webrtc-stats-container';
        statsContainer.className = 'webrtc-stats-container';
        document.body.appendChild(statsContainer);

        // Ajouter le style
        const style = document.createElement('style');
        style.textContent = `
            .webrtc-stats-container {
                position: fixed;
                bottom: 20px;
                right: 20px;
                width: 300px;
                max-height: 400px;
                overflow-y: auto;
                background-color: rgba(0, 0, 0, 0.8);
                color: #fff;
                border-radius: 8px;
                padding: 15px;
                font-family: monospace;
                font-size: 12px;
                z-index: 9999;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            }
            
            .webrtc-stats-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 10px;
                padding-bottom: 5px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.2);
            }
            
            .webrtc-stats-title {
                font-weight: bold;
                font-size: 14px;
            }
            
            .webrtc-stats-close {
                background: none;
                border: none;
                color: #fff;
                cursor: pointer;
                font-size: 16px;
            }
            
            .webrtc-stats-section {
                margin-bottom: 10px;
            }
            
            .webrtc-stats-section-title {
                font-weight: bold;
                margin-bottom: 5px;
                color: #4285F4;
            }
            
            .webrtc-stats-item {
                margin-bottom: 3px;
                display: flex;
            }
            
            .webrtc-stats-label {
                flex: 1;
                color: #aaa;
            }
            
            .webrtc-stats-value {
                flex: 1;
                text-align: right;
            }
            
            .webrtc-stats-good {
                color: #0f0;
            }
            
            .webrtc-stats-warning {
                color: #ff0;
            }
            
            .webrtc-stats-error {
                color: #f00;
            }
            
            .webrtc-stats-toggle {
                position: fixed;
                bottom: 20px;
                right: 20px;
                background-color: #4285F4;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 12px;
                cursor: pointer;
                z-index: 9998;
                box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            }
            
            .webrtc-stats-toggle.active {
                background-color: #EA4335;
            }
        `;
        document.head.appendChild(style);

        // Créer l'en-tête
        const header = document.createElement('div');
        header.className = 'webrtc-stats-header';
        
        const title = document.createElement('div');
        title.className = 'webrtc-stats-title';
        title.textContent = 'Statistiques WebRTC';
        
        const closeButton = document.createElement('button');
        closeButton.className = 'webrtc-stats-close';
        closeButton.innerHTML = '&times;';
        closeButton.addEventListener('click', () => {
            statsContainer.style.display = 'none';
            toggleButton.style.display = 'block';
        });
        
        header.appendChild(title);
        header.appendChild(closeButton);
        statsContainer.appendChild(header);

        // Créer le contenu
        const content = document.createElement('div');
        content.className = 'webrtc-stats-content';
        statsContainer.appendChild(content);

        // Créer le bouton de toggle
        const toggleButton = document.createElement('button');
        toggleButton.className = 'webrtc-stats-toggle';
        toggleButton.textContent = 'Afficher les stats WebRTC';
        toggleButton.style.display = 'none';
        toggleButton.addEventListener('click', () => {
            statsContainer.style.display = 'block';
            toggleButton.style.display = 'none';
        });
        document.body.appendChild(toggleButton);
    }

    // Récupérer le contenu
    const content = statsContainer.querySelector('.webrtc-stats-content');

    // Fonction pour mettre à jour les statistiques
    async function updateStats() {
        if (!peerConnection) return;
        
        try {
            const stats = await peerConnection.getStats();
            content.innerHTML = ''; // Effacer le contenu précédent
            
            // Informations de connexion
            const connectionSection = document.createElement('div');
            connectionSection.className = 'webrtc-stats-section';
            
            const connectionTitle = document.createElement('div');
            connectionTitle.className = 'webrtc-stats-section-title';
            connectionTitle.textContent = 'État de la connexion';
            connectionSection.appendChild(connectionTitle);
            
            // État de la connexion
            addStatItem(connectionSection, 'État de signalisation', peerConnection.signalingState);
            addStatItem(connectionSection, 'État de connexion', peerConnection.connectionState);
            addStatItem(connectionSection, 'État de connexion ICE', peerConnection.iceConnectionState);
            addStatItem(connectionSection, 'État de rassemblement ICE', peerConnection.iceGatheringState);
            
            content.appendChild(connectionSection);
            
            // Statistiques des candidats ICE
            let iceCandidates = {
                local: { host: 0, srflx: 0, relay: 0, total: 0 },
                remote: { host: 0, srflx: 0, relay: 0, total: 0 }
            };
            
            // Statistiques audio/vidéo
            let audioStats = { send: null, recv: null };
            let videoStats = { send: null, recv: null };
            
            // Parcourir toutes les statistiques
            stats.forEach(stat => {
                // Candidats ICE
                if (stat.type === 'local-candidate' || stat.type === 'remote-candidate') {
                    const type = stat.type === 'local-candidate' ? 'local' : 'remote';
                    iceCandidates[type].total++;
                    
                    if (stat.candidateType === 'host') iceCandidates[type].host++;
                    else if (stat.candidateType === 'srflx') iceCandidates[type].srflx++;
                    else if (stat.candidateType === 'relay') iceCandidates[type].relay++;
                }
                
                // Statistiques audio
                if (stat.type === 'inbound-rtp' && stat.kind === 'audio') {
                    audioStats.recv = stat;
                } else if (stat.type === 'outbound-rtp' && stat.kind === 'audio') {
                    audioStats.send = stat;
                }
                
                // Statistiques vidéo
                if (stat.type === 'inbound-rtp' && stat.kind === 'video') {
                    videoStats.recv = stat;
                } else if (stat.type === 'outbound-rtp' && stat.kind === 'video') {
                    videoStats.send = stat;
                }
            });
            
            // Afficher les statistiques des candidats ICE
            const iceSection = document.createElement('div');
            iceSection.className = 'webrtc-stats-section';
            
            const iceTitle = document.createElement('div');
            iceTitle.className = 'webrtc-stats-section-title';
            iceTitle.textContent = 'Candidats ICE';
            iceSection.appendChild(iceTitle);
            
            addStatItem(iceSection, 'Locaux (total)', iceCandidates.local.total);
            addStatItem(iceSection, '- host', iceCandidates.local.host);
            addStatItem(iceSection, '- srflx', iceCandidates.local.srflx);
            addStatItem(iceSection, '- relay', iceCandidates.local.relay);
            
            addStatItem(iceSection, 'Distants (total)', iceCandidates.remote.total);
            addStatItem(iceSection, '- host', iceCandidates.remote.host);
            addStatItem(iceSection, '- srflx', iceCandidates.remote.srflx);
            addStatItem(iceSection, '- relay', iceCandidates.remote.relay);
            
            content.appendChild(iceSection);
            
            // Afficher les statistiques audio
            if (audioStats.send || audioStats.recv) {
                const audioSection = document.createElement('div');
                audioSection.className = 'webrtc-stats-section';
                
                const audioTitle = document.createElement('div');
                audioTitle.className = 'webrtc-stats-section-title';
                audioTitle.textContent = 'Audio';
                audioSection.appendChild(audioTitle);
                
                if (audioStats.send) {
                    addStatItem(audioSection, 'Paquets envoyés', audioStats.send.packetsSent);
                    addStatItem(audioSection, 'Octets envoyés', formatBytes(audioStats.send.bytesSent));
                }
                
                if (audioStats.recv) {
                    addStatItem(audioSection, 'Paquets reçus', audioStats.recv.packetsReceived);
                    addStatItem(audioSection, 'Paquets perdus', audioStats.recv.packetsLost);
                    addStatItem(audioSection, 'Octets reçus', formatBytes(audioStats.recv.bytesReceived));
                    
                    // Calculer le taux de perte de paquets
                    if (audioStats.recv.packetsReceived > 0) {
                        const lossRate = (audioStats.recv.packetsLost / (audioStats.recv.packetsReceived + audioStats.recv.packetsLost)) * 100;
                        const lossRateFormatted = lossRate.toFixed(2) + '%';
                        
                        let className = 'webrtc-stats-good';
                        if (lossRate > 5) className = 'webrtc-stats-warning';
                        if (lossRate > 10) className = 'webrtc-stats-error';
                        
                        addStatItem(audioSection, 'Taux de perte', lossRateFormatted, className);
                    }
                }
                
                content.appendChild(audioSection);
            }
            
            // Afficher les statistiques vidéo
            if (videoStats.send || videoStats.recv) {
                const videoSection = document.createElement('div');
                videoSection.className = 'webrtc-stats-section';
                
                const videoTitle = document.createElement('div');
                videoTitle.className = 'webrtc-stats-section-title';
                videoTitle.textContent = 'Vidéo';
                videoSection.appendChild(videoTitle);
                
                if (videoStats.send) {
                    addStatItem(videoSection, 'Paquets envoyés', videoStats.send.packetsSent);
                    addStatItem(videoSection, 'Octets envoyés', formatBytes(videoStats.send.bytesSent));
                    if (videoStats.send.frameWidth && videoStats.send.frameHeight) {
                        addStatItem(videoSection, 'Résolution envoyée', `${videoStats.send.frameWidth}x${videoStats.send.frameHeight}`);
                    }
                    if (videoStats.send.framesPerSecond) {
                        addStatItem(videoSection, 'FPS envoyé', videoStats.send.framesPerSecond.toFixed(1));
                    }
                }
                
                if (videoStats.recv) {
                    addStatItem(videoSection, 'Paquets reçus', videoStats.recv.packetsReceived);
                    addStatItem(videoSection, 'Paquets perdus', videoStats.recv.packetsLost);
                    addStatItem(videoSection, 'Octets reçus', formatBytes(videoStats.recv.bytesReceived));
                    
                    if (videoStats.recv.frameWidth && videoStats.recv.frameHeight) {
                        addStatItem(videoSection, 'Résolution reçue', `${videoStats.recv.frameWidth}x${videoStats.recv.frameHeight}`);
                    }
                    if (videoStats.recv.framesPerSecond) {
                        addStatItem(videoSection, 'FPS reçu', videoStats.recv.framesPerSecond.toFixed(1));
                    }
                    
                    // Calculer le taux de perte de paquets
                    if (videoStats.recv.packetsReceived > 0) {
                        const lossRate = (videoStats.recv.packetsLost / (videoStats.recv.packetsReceived + videoStats.recv.packetsLost)) * 100;
                        const lossRateFormatted = lossRate.toFixed(2) + '%';
                        
                        let className = 'webrtc-stats-good';
                        if (lossRate > 5) className = 'webrtc-stats-warning';
                        if (lossRate > 10) className = 'webrtc-stats-error';
                        
                        addStatItem(videoSection, 'Taux de perte', lossRateFormatted, className);
                    }
                }
                
                content.appendChild(videoSection);
            }
            
        } catch (error) {
            console.error('Erreur lors de la récupération des statistiques WebRTC:', error);
            content.innerHTML = `<div class="webrtc-stats-error">Erreur: ${error.message}</div>`;
        }
    }
    
    // Fonction pour ajouter un élément de statistique
    function addStatItem(container, label, value, valueClass = '') {
        const item = document.createElement('div');
        item.className = 'webrtc-stats-item';
        
        const labelElement = document.createElement('div');
        labelElement.className = 'webrtc-stats-label';
        labelElement.textContent = label;
        
        const valueElement = document.createElement('div');
        valueElement.className = `webrtc-stats-value ${valueClass}`;
        valueElement.textContent = value;
        
        item.appendChild(labelElement);
        item.appendChild(valueElement);
        container.appendChild(item);
    }
    
    // Fonction pour formater les octets
    function formatBytes(bytes, decimals = 2) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    }
    
    // Mettre à jour les statistiques toutes les secondes
    const statsInterval = setInterval(updateStats, 1000);
    
    // Nettoyer l'intervalle lorsque la page est fermée
    window.addEventListener('beforeunload', () => {
        clearInterval(statsInterval);
    });
    
    // Mettre à jour les statistiques immédiatement
    updateStats();
}

// Fonction pour patcher la création de RTCPeerConnection
function patchRTCPeerConnection() {
    // Sauvegarder le constructeur original
    const originalRTCPeerConnection = window.RTCPeerConnection;
    
    // Remplacer par notre version
    window.RTCPeerConnection = function(...args) {
        console.log('Création d\'une nouvelle RTCPeerConnection avec les arguments:', args);
        
        // Créer une nouvelle connexion avec le constructeur original
        const pc = new originalRTCPeerConnection(...args);
        
        // Ajouter des écouteurs d'événements pour le débogage
        pc.addEventListener('icecandidate', event => {
            if (event.candidate) {
                console.log('Nouveau candidat ICE local:', event.candidate.candidate);
                console.log('Type de candidat:', event.candidate.type);
                console.log('Protocol:', event.candidate.protocol);
            } else {
                console.log('Fin de la génération des candidats ICE locaux');
            }
        });
        
        pc.addEventListener('icecandidateerror', event => {
            console.error('Erreur de candidat ICE:', event);
        });
        
        pc.addEventListener('iceconnectionstatechange', () => {
            console.log('État de connexion ICE changé:', pc.iceConnectionState);
            
            if (pc.iceConnectionState === 'failed') {
                console.error('La connexion ICE a échoué');
            } else if (pc.iceConnectionState === 'disconnected') {
                console.warn('La connexion ICE est déconnectée');
            } else if (pc.iceConnectionState === 'connected') {
                console.log('La connexion ICE est établie');
            }
        });
        
        pc.addEventListener('connectionstatechange', () => {
            console.log('État de connexion changé:', pc.connectionState);
            
            if (pc.connectionState === 'failed') {
                console.error('La connexion a échoué');
            } else if (pc.connectionState === 'disconnected') {
                console.warn('La connexion est déconnectée');
            } else if (pc.connectionState === 'connected') {
                console.log('La connexion est établie');
            }
        });
        
        pc.addEventListener('signalingstatechange', () => {
            console.log('État de signalisation changé:', pc.signalingState);
        });
        
        pc.addEventListener('negotiationneeded', () => {
            console.log('Négociation nécessaire');
        });
        
        // Patcher les méthodes
        const originalSetLocalDescription = pc.setLocalDescription;
        pc.setLocalDescription = async function(...args) {
            console.log('setLocalDescription appelé avec:', args[0]);
            return originalSetLocalDescription.apply(this, args);
        };
        
        const originalSetRemoteDescription = pc.setRemoteDescription;
        pc.setRemoteDescription = async function(...args) {
            console.log('setRemoteDescription appelé avec:', args[0]);
            return originalSetRemoteDescription.apply(this, args);
        };
        
        const originalAddIceCandidate = pc.addIceCandidate;
        pc.addIceCandidate = async function(...args) {
            console.log('addIceCandidate appelé avec:', args[0]);
            return originalAddIceCandidate.apply(this, args);
        };
        
        const originalCreateOffer = pc.createOffer;
        pc.createOffer = async function(...args) {
            console.log('createOffer appelé');
            return originalCreateOffer.apply(this, args);
        };
        
        const originalCreateAnswer = pc.createAnswer;
        pc.createAnswer = async function(...args) {
            console.log('createAnswer appelé');
            return originalCreateAnswer.apply(this, args);
        };
        
        // Ajouter un bouton pour afficher les statistiques
        setTimeout(() => {
            showWebRTCStats(pc);
        }, 1000);
        
        return pc;
    };
}

// Initialiser le débogage WebRTC
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initialisation du débogage WebRTC...');
    patchRTCPeerConnection();
});

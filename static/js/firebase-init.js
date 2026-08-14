/**
 * AquaGuru Firebase & Firestore Client Initialization
 * Project: aquaguru-f35c0
 */

(function() {
    'use strict';

    // Firebase Configuration for AquaGuru
    const firebaseConfig = {
        apiKey: "AIzaSyBQsl2HCcf_RLEFkyooSQCKZvdjgzC5XWs",
        authDomain: "aquaguru-f35c0.firebaseapp.com",
        projectId: "aquaguru-f35c0",
        storageBucket: "aquaguru-f35c0.firebasestorage.app",
        messagingSenderId: "632009597255",
        appId: "1:632009597255:web:a9a708852a4c5817772c62",
        measurementId: "G-FBVB1F0CJ9"
    };

    let firebaseApp = null;
    let firestoreDb = null;
    let analyticsInstance = null;

    try {
        if (typeof firebase !== 'undefined') {
            if (!firebase.apps.length) {
                firebaseApp = firebase.initializeApp(firebaseConfig);
            } else {
                firebaseApp = firebase.app();
            }

            // Initialize Firestore
            if (typeof firebase.firestore === 'function') {
                firestoreDb = firebase.firestore();
                console.log('[FIREBASE] Cloud Firestore connected successfully for project:', firebaseConfig.projectId);
            }

            // Initialize Analytics
            if (typeof firebase.analytics === 'function') {
                analyticsInstance = firebase.analytics();
            }
        } else {
            console.warn('[FIREBASE] Firebase SDK script not loaded yet.');
        }
    } catch (err) {
        console.error('[FIREBASE INIT ERROR]', err);
    }

    // Expose global AquaGuru Firebase helper
    window.AquaGuruFirebase = {
        config: firebaseConfig,
        app: firebaseApp,
        db: firestoreDb,
        analytics: analyticsInstance,
        
        // Helper to listen to a collection in real-time
        listenCollection: function(collectionName, callback) {
            if (!firestoreDb) {
                console.warn('[FIREBASE] Firestore not available for real-time listener:', collectionName);
                return null;
            }
            return firestoreDb.collection(collectionName).onSnapshot(snapshot => {
                const docs = [];
                snapshot.forEach(doc => docs.push({ id: doc.id, ...doc.data() }));
                if (typeof callback === 'function') {
                    callback(docs);
                }
            }, error => {
                console.error(`[FIREBASE] Error listening to ${collectionName}:`, error);
            });
        },
        
        // Helper to save a document
        saveDoc: function(collectionName, docId, data) {
            if (!firestoreDb) return Promise.reject('Firestore not initialized');
            if (docId) {
                return firestoreDb.collection(collectionName).doc(String(docId)).set(data, { merge: true });
            } else {
                return firestoreDb.collection(collectionName).add(data);
            }
        },

        // Helper to trigger backend full sync
        syncAllToFirestore: function() {
            return fetch('/api/firebase/sync', { method: 'POST' })
                .then(r => r.json())
                .then(data => {
                    console.log('[FIREBASE SYNC COMPLETE]', data);
                    return data;
                });
        }
    };
})();

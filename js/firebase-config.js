/* Firebase configuration — PLACEHOLDERS
 *
 * STAP 1 — TODO voor de gebruiker:
 *   1. Ga naar https://console.firebase.google.com
 *   2. Maak een nieuw project aan (bv. "open-vertaling")
 *   3. Voeg een Web-app toe (</> icoon)  → kopieer de config
 *   4. Plak de waarden hieronder
 *   5. Activeer in de Firebase-console:
 *        - Authentication  →  Sign-in method  →  Google  (Enable)
 *        - Firestore Database  →  Start in production mode (eu-west)
 *        - Voeg jouw lokale dev-domein (localhost) toe in
 *          Authentication → Settings → Authorized domains
 *
 * STAP 2 — Firestore-rules (kopieer in console → Rules):
 *   rules_version = '2';
 *   service cloud.firestore {
 *     match /databases/{database}/documents {
 *       match /users/{uid}/{doc=**} {
 *         allow read, write: if request.auth != null && request.auth.uid == uid;
 *       }
 *       match /feedback/{id} {
 *         allow create: if request.auth != null;
 *         allow read, update, delete: if false; // alleen via admin/console
 *       }
 *     }
 *   }
 *
 * Zolang `apiKey` op "YOUR_API_KEY" staat blijft de app werken in
 * "anonymous local mode": login-knop is verborgen en highlights worden
 * uitsluitend in localStorage opgeslagen.
 */

window.firebaseConfig = {
    apiKey: "AIzaSyCiZhSCcksr4QVBJ_iXgLavzYDfHzLd2Ls",
    authDomain: "open-vertaling.firebaseapp.com",
    projectId: "open-vertaling",
    storageBucket: "open-vertaling.firebasestorage.app",
    messagingSenderId: "516870721479",
    appId: "1:516870721479:web:946b7cc057478b06e193e2",
    measurementId: "G-K1RNRTMFM3"
};

window.firebaseEnabled = !window.firebaseConfig.apiKey.startsWith('YOUR_');

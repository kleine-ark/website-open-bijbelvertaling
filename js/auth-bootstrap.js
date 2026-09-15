/* Eén geordende login-opstart per document, vóór DOMContentLoaded. */
import './firebase-config.js';
import './auth.js';
import './collaboration.js';

window.Collaboration.init();
window.Auth.init();

// URL base da API do backend. Usa o mesmo host que serviu a pagina
// (window.location.hostname) em vez de "localhost" fixo, para que o
// frontend funcione tanto na maquina local quanto acessado por outro
// dispositivo na rede (ex: notebook acessando o IP do Raspberry Pi).
export const API_BASE_URL = `http://${window.location.hostname}:8000`;

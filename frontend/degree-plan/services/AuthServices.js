import {baseUrl} from './HttpServices';

const API_DOMAIN = baseUrl;

export async function apiCheckAuth() {
    const res = await fetch(`${baseUrl}/accounts/me/`);
    if (res.status < 300 && res.status >= 200) {
      return true;
    } else {
      return false;
    }
  }

export function redirectForAuth() {
    window.location.href = `${baseUrl}/accounts/login/?next=${window.location.pathname}`;
  }
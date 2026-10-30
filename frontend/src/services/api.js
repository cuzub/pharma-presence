import axios from 'axios'

const lireCookie = (nom) => {
  const morceau = document.cookie.split('; ').find((c) => c.startsWith(`${nom}=`))
  return morceau ? decodeURIComponent(morceau.slice(nom.length + 1)) : null
}

const api = axios.create({
  baseURL: '/api',
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' }
})

// Le jeton de session est dans un cookie httpOnly ; seul le jeton CSRF (non sensible seul) est lu ici.
api.interceptors.request.use((config) => {
  const methode = (config.method || 'get').toLowerCase()
  if (!['get', 'head', 'options'].includes(methode)) {
    const csrf = lireCookie('csrf_access_token')
    if (csrf) config.headers['X-CSRF-TOKEN'] = csrf
  }
  return config
})

const gestionnaires = { nonAuthentifie: null, changementMdpRequis: null }

export const surErreurSession = ({ nonAuthentifie, changementMdpRequis }) => {
  gestionnaires.nonAuthentifie = nonAuthentifie
  gestionnaires.changementMdpRequis = changementMdpRequis
}

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status
    const code = error.response?.data?.code
    const url = error.config?.url || ''
    if (status === 401 && !url.startsWith('/auth/login') && !url.startsWith('/auth/me')) {
      gestionnaires.nonAuthentifie?.()
    } else if (status === 403 && code === 'changement_mdp_requis') {
      gestionnaires.changementMdpRequis?.()
    }
    return Promise.reject(error)
  }
)

export const messageErreur = async (error, defaut = 'Une erreur est survenue') => {
  const data = error?.response?.data
  if (data instanceof Blob) {
    try {
      return JSON.parse(await data.text()).message || defaut
    } catch {
      return defaut
    }
  }
  if (data?.message) return data.message
  if (!error?.response) return 'Serveur injoignable, vérifiez votre connexion'
  return defaut
}

export const telecharger = async (url, nomFichier) => {
  const response = await api.get(url, { responseType: 'blob' })
  const lien = document.createElement('a')
  lien.href = URL.createObjectURL(response.data)
  lien.download = nomFichier
  document.body.appendChild(lien)
  lien.click()
  lien.remove()
  URL.revokeObjectURL(lien.href)
}

export default api

// Mot de passe provisoire lisible (sans caractères ambigus) à transmettre à un employé.
const ALPHABET = 'abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789'

export const genererMotDePasse = (longueur = 14) => {
  const valeurs = new Uint32Array(longueur)
  crypto.getRandomValues(valeurs)
  return Array.from(valeurs, (v) => ALPHABET[v % ALPHABET.length]).join('')
}

export const LONGUEUR_MIN_MDP = 12

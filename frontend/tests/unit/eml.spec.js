import { describe, expect, it } from 'vitest'
import { construireEml, encoderBase64 } from '../../src/utils/eml'

const decoderBase64 = (base64) => Uint8Array.from(atob(base64), (c) => c.charCodeAt(0))

describe('construireEml', () => {
  const pieceJointe = new Uint8Array([0, 1, 2, 250, 251, 252, 253, 254, 255])

  it('produit un brouillon avec destinataire, sujet UTF-8 et pièce jointe', () => {
    const eml = construireEml({
      destinataire: 'comptable@example.fr',
      sujet: 'Export octobre 2026 — récap',
      texte: 'Bonjour,\nCi-joint l’état préparatoire.',
      nomPieceJointe: 'etat-preparatoire-2026-10.xlsx',
      typePieceJointe: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      pieceJointe,
    })

    expect(eml).toContain('To: comptable@example.fr\r\n')
    expect(eml).toContain('X-Unsent: 1\r\n')
    const sujet = eml.match(/^Subject: =\?UTF-8\?B\?(.+)\?=$/m)[1]
    expect(new TextDecoder().decode(decoderBase64(sujet))).toBe('Export octobre 2026 — récap')

    const frontiere = eml.match(/boundary="([^"]+)"/)[1]
    const parties = eml.split(`--${frontiere}`)
    const corps = parties[1].split('\r\n\r\n')[1].replace(/\r\n/g, '')
    expect(new TextDecoder().decode(decoderBase64(corps))).toBe('Bonjour,\nCi-joint l’état préparatoire.')

    const fichier = parties[2].split('\r\n\r\n')[1].replace(/\r\n/g, '')
    expect(Array.from(decoderBase64(fichier))).toEqual(Array.from(pieceJointe))
    expect(eml).toContain('Content-Disposition: attachment; filename="etat-preparatoire-2026-10.xlsx"')
    expect(eml.endsWith(`--${frontiere}--\r\n`)).toBe(true)
  })

  it('supprime les retours à la ligne dans les en-têtes', () => {
    const eml = construireEml({
      destinataire: 'a@b.fr\r\nBcc: espion@x.fr',
      sujet: 'Titre\r\nBcc: espion@x.fr',
      texte: '',
      nomPieceJointe: 'f.xlsx',
      typePieceJointe: 'application/octet-stream',
      pieceJointe,
    })
    expect(eml).not.toMatch(/^Bcc:/m)
  })

  it('encode les longs contenus sur des lignes de 76 caractères au plus', () => {
    const grand = new Uint8Array(5000).map((_, i) => i % 256)
    const eml = construireEml({
      destinataire: 'a@b.fr', sujet: 's', texte: 't', nomPieceJointe: 'f.xlsx', typePieceJointe: 'application/octet-stream', pieceJointe: grand,
    })
    expect(eml.split('\r\n').every((ligne) => ligne.length <= 76)).toBe(true)
    expect(encoderBase64(new Uint8Array([104, 105]))).toBe('aGk=')
  })
})

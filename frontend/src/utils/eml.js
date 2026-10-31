const encodeur = new TextEncoder()

export const encoderBase64 = (octets) => {
  let binaire = ''
  for (let i = 0; i < octets.length; i += 0x8000) {
    binaire += String.fromCharCode(...octets.subarray(i, i + 0x8000))
  }
  return btoa(binaire)
}

const sur76 = (base64) => (base64.match(/.{1,76}/g) || []).join('\r\n')

const entete = (valeur) => valeur.replace(/[\r\n]+/g, ' ').trim()

/**
 * Brouillon de mail au format .eml (RFC 5322 / MIME) avec une pièce jointe.
 * Ouvert par l'appli mail, il apparaît comme message non envoyé, prêt à relire et envoyer.
 */
export const construireEml = ({ destinataire, sujet, texte, nomPieceJointe, typePieceJointe, pieceJointe }) => {
  const frontiere = `frontiere-${Date.now().toString(36)}`
  const sujetEncode = `=?UTF-8?B?${encoderBase64(encodeur.encode(entete(sujet)))}?=`
  return [
    `To: ${entete(destinataire)}`,
    `Subject: ${sujetEncode}`,
    'MIME-Version: 1.0',
    'X-Unsent: 1',
    `Content-Type: multipart/mixed; boundary="${frontiere}"`,
    '',
    `--${frontiere}`,
    'Content-Type: text/plain; charset=UTF-8',
    'Content-Transfer-Encoding: base64',
    '',
    sur76(encoderBase64(encodeur.encode(texte))),
    `--${frontiere}`,
    `Content-Type: ${typePieceJointe}; name="${nomPieceJointe}"`,
    `Content-Disposition: attachment; filename="${nomPieceJointe}"`,
    'Content-Transfer-Encoding: base64',
    '',
    sur76(encoderBase64(pieceJointe)),
    `--${frontiere}--`,
    '',
  ].join('\r\n')
}

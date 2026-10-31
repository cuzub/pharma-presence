import { ref, watch } from 'vue'

const CLE_STOCKAGE = 'barre-laterale-reduite'

const reduite = ref(localStorage.getItem(CLE_STOCKAGE) === '1')

watch(reduite, (valeur) => localStorage.setItem(CLE_STOCKAGE, valeur ? '1' : '0'))

export function useBarreLaterale() {
  const basculer = () => {
    reduite.value = !reduite.value
  }
  return { reduite, basculer }
}
